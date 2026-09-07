"""Exact inverse-position circuit for known ciphertext and common reset key.
Unlike the forward-array encoding, each observed card directly indexes its
position expression. Unknown neighbor identity is handled by conditional moves.
"""
from pathlib import Path
import sys,json,time,argparse,collections
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_three_cycle_scan import encrypt_physical
from clocked_key_attack import decode

def solve(ct,cl,b,n=83,timeout=10000,fixed=None,preferred=None,symmetry_break=True,max_errors=0,reduce_observations=True,materialize=True,alphabet_bound=None,unrestricted_first=True):
    started=time.time();original_ct=ct;original_cl=cl;M=n-1;
    if reduce_observations and alphabet_bound is None:
        counts=collections.Counter(x for row in cl for x in row)
        lengths=[max([t+1 for t,x in enumerate(row) if counts[x]>1]+[1]) for row in cl]
        ct=[row[:length] for row,length in zip(ct,lengths)];cl=[row[:length] for row,length in zip(cl,lengths)]
    observed=set(c for row in ct for c in row)
    width=(2*n).bit_length();bv=lambda x:z3.BitVecVal(int(x),width)
    solver=z3.Solver();solver.set(timeout=timeout);initial={};free=[];fixed=fixed or {}
    gauge=bool(symmetry_break and not fixed and alphabet_bound is None)
    if gauge:fixed={ct[0][0]:1}
    available=[p for p in range(n) if p not in fixed.values()]
    rotation=z3.BitVec('rotation',width) if b is None else None
    if b is None:solver.add(z3.ULT(rotation,bv(M)))
    for c in range(n):
        if reduce_observations and c not in observed and c not in fixed:continue
        if c in fixed:v=bv(fixed[c])
        else:
            v=z3.BitVec('initial_position_'+str(c),width);free.append(v)
            solver.add(z3.Or(*[v==bv(p) for p in available]))
            if preferred is not None:solver.set_initial_value(v,bv(preferred.index(c)))
        initial[c]=v
    if free:solver.add(z3.Distinct(*free))
    seen={};count=0;equalities=[];intermediate=0
    for mi,(message,classes) in enumerate(zip(ct,cl)):
        pos={c:initial[c] for c in set(message)} if reduce_observations else initial.copy()
        for t,(c,x) in enumerate(zip(message,classes)):
            p=pos[c];solver.add(p!=bv(0))
            if alphabet_bound is not None and (t>0 or not unrestricted_first):
                if b is not None:
                    offset=t*b%M;physical=z3.If(z3.ULE(p,bv(M-offset)),p+bv(offset),p-bv(M-offset));solver.add(z3.ULE(physical,bv(alphabet_bound)))
                else:
                    wide=max(width,(2*n*(1+max(map(len,ct)))).bit_length());extend=lambda v:z3.ZeroExt(wide-width,v)
                    physical=z3.URem(extend(p)-1+t*extend(rotation),M)+1;solver.add(z3.ULE(physical,alphabet_bound))
            if x in seen:
                q,u=seen[x];dt=(t-u)%M;count+=1
                if dt==0:equalities.append(p==q)
                elif b is not None:
                    offset=dt*b%M
                    moved=z3.If(z3.ULE(p,bv(M-offset)),p+bv(offset),p-bv(M-offset))
                    equalities.append(moved==q)
                else:
                    wide=(2*n*n).bit_length();extend=lambda v:z3.ZeroExt(wide-width,v)
                    equalities.append(z3.URem(extend(p)+M-extend(q)+dt*extend(rotation),M)==0)
            else:seen[x]=(p,t)
            neighbor=z3.simplify(z3.If(p==bv(M),bv(1),p+bv(1)))
            future=set(message[t+1:]) if reduce_observations else set(pos)
            nxt={}
            for card,q in pos.items():
                if card not in future:continue
                expr=bv(0) if card==c else z3.simplify(z3.If(q==bv(0),neighbor,z3.If(q==neighbor,p,q)))
                if materialize and expr.num_args()>0:
                    v=z3.BitVec('position_%d_%d_%d'%(mi,t,card),width);solver.add(v==expr);nxt[card]=v;intermediate+=1
                else:nxt[card]=expr
            pos=nxt
    # Omitted suffixes cannot introduce top selections unless adjacent cards repeat.
    if any(a==b for row in original_ct for a,b in zip(row,row[1:])):solver.add(z3.BoolVal(False))
    if max_errors==0:solver.add(*equalities)
    elif equalities:solver.add(z3.PbLe([(z3.Not(eq),1) for eq in equalities],max_errors))
    encoded=time.time();status=str(solver.check());out=dict(status=status,rotation=b,lengths=list(map(len,original_ct)),encoded_lengths=list(map(len,ct)),observation_reduction=reduce_observations,observed_labels=len(observed),comparisons=count,alphabet_bound=alphabet_bound,unrestricted_first=unrestricted_first,maximum_equality_errors=max_errors,materialized_positions=intermediate,free_key_entries=len(free),bottom_rotation_gauge=gauge,encoding_seconds=encoded-started,solve_seconds=time.time()-encoded,seconds=time.time()-started)
    if status=='unknown':out['reason']=solver.reason_unknown()
    if status=='sat':
        model=solver.model();key=[-1]*n
        if b is None:b=model.eval(rotation).as_long();out['rotation']=b
        for c,v in initial.items():key[model.eval(v).as_long()]=c
        missing=iter(c for c in range(n) if c not in key)
        key=[next(missing) if c<0 else c for c in key]
        assert sorted(key)==list(range(n));pt=decode(original_ct,key,b);values={};errors=0
        for row,classes in zip(pt,original_cl):
            for p,x in zip(row,classes):
                assert p!=0
                if x in values:errors+=p!=values[x]
                else:values[x]=p
        assert all(encrypt_physical(row,key,1,b)==message for row,message in zip(pt,original_ct))
        if alphabet_bound is not None:assert all(1<=p<=alphabet_bound for row in pt for p in row[int(unrestricted_first):])
        assert errors<=max_errors
        out.update(initial_deck=key,plaintext_positions=pt,shared_selection_disagreements=errors,exact_common_key_replay=True)
    out['scope']='UNSAT with fixed entries excludes only that restricted key neighborhood. Free-key results remain conditional on the specified update, rotation, and plaintext equalities.'
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--length',type=int,default=12);ap.add_argument('--rotation',type=int,default=9);ap.add_argument('--timeout',type=int,default=15000);ap.add_argument('--no-reduction',action='store_true');ap.add_argument('--all-rotations',action='store_true');ap.add_argument('--source');ap.add_argument('--free',type=int,default=14);ap.add_argument('--output',required=True);a=ap.parse_args()
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cl=make_plaintexts(raw,assumptions(raw));ct=[m[:a.length] for m in raw];cl=[m[:a.length] for m in cl];fixed=None;key=None;slots=None
    if a.source:
        import numpy as np
        from two_swap_prefix_repair import profiles
        key=json.loads((ROOT/a.source).read_text())['initial_deck'];aa,bb=np.triu_indices(83,1);ids=np.arange(len(aa));keys=np.tile(key,(len(aa),1));keys[ids,aa]=np.array(key)[bb];keys[ids,bb]=np.array(key)[aa]
        baseline,_=profiles(ct,np.array([key]),cl,a.rotation);matched,invalid=profiles(ct,keys,cl,a.rotation);errors=(~matched).sum(axis=1)+invalid*10000;fixed_count=matched[:,~baseline[0]].sum(axis=1);candidates=sorted(np.flatnonzero(fixed_count>0),key=lambda i:errors[i]);slots=set()
        for i in candidates:
            slots.update([int(aa[i]),int(bb[i])])
            if len(slots)>=a.free:break
        if len(slots)<a.free:slots.update([p for p in range(83) if p not in slots][:a.free-len(slots)])
        fixed={c:p for p,c in enumerate(key) if p not in slots}
    r=solve(ct,cl,None if a.all_rotations else a.rotation,timeout=a.timeout,fixed=fixed,preferred=key,reduce_observations=not a.no_reduction);r.update(source=a.source,free_slots=sorted(slots) if slots is not None else None)
    (ROOT/a.output).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions']},flush=True)
