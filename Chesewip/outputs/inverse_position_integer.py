"""Integer counterpart to inverse-position circuit, with sparse restrictions."""
from pathlib import Path
import sys,json,time,argparse
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from clocked_key_attack import decode
from clocked_three_cycle_scan import encrypt_physical

def solve(ct,cl,b,n=83,timeout=20000,fixed=None,preferred=None):
    started=time.time();M=n-1;s=z3.Solver();s.set(timeout=timeout);fixed=fixed or {};gauge=not fixed
    if gauge:fixed={ct[0][0]:1}
    free=[];available=[p for p in range(n) if p not in fixed.values()];initial=[]
    for c in range(n):
        if c in fixed:v=z3.IntVal(fixed[c])
        else:
            v=z3.Int('initial_position_'+str(c));free.append(v)
            if gauge:s.add(v>=0,v<n,v!=1)
            else:s.add(z3.Or(*[v==p for p in available]))
            if preferred is not None:s.set_initial_value(v,z3.IntVal(preferred.index(c)))
        initial.append(v)
    s.add(z3.Distinct(*free));rotation=z3.Int('rotation') if b is None else b
    if b is None:s.add(rotation>=0,rotation<M)
    seen={};count=0
    for mi,(message,classes) in enumerate(zip(ct,cl)):
        pos=initial.copy()
        for t,(c,x) in enumerate(zip(message,classes)):
            p=pos[c];s.add(p!=0)
            if x in seen:
                q,u=seen[x];dt=(t-u)%M;count+=1
                if dt==0:s.add(p==q)
                elif b is not None:
                    offset=dt*b%M;s.add(z3.Or(p-q==-offset,p-q==M-offset))
                else:s.add((p-q+dt*rotation)%M==0)
            else:seen[x]=(p,t)
            r=z3.simplify(z3.If(p==M,1,p+1));pos=[z3.IntVal(0) if card==c else z3.simplify(z3.If(q==0,r,z3.If(q==r,p,q))) for card,q in enumerate(pos)]
    encoded=time.time();status=str(s.check());out=dict(status=status,rotation=b,lengths=list(map(len,ct)),comparisons=count,free_key_entries=len(free),bottom_rotation_gauge=gauge,encoding_seconds=encoded-started,solve_seconds=time.time()-encoded,seconds=time.time()-started)
    if status=='unknown':out['reason']=s.reason_unknown()
    if status=='sat':
        model=s.model();key=[-1]*n
        if b is None:b=model.eval(rotation).as_long();out['rotation']=b
        for c,v in enumerate(initial):key[model.eval(v).as_long()]=c
        assert sorted(key)==list(range(n));pt=decode(ct,key,b);values={}
        for row,classes in zip(pt,cl):
            for p,x in zip(row,classes):
                assert p!=0
                if x in values:assert p==values[x]
                else:values[x]=p
        assert all(encrypt_physical(row,key,1,b)==message for row,message in zip(pt,ct))
        out.update(initial_deck=key,plaintext_positions=pt,exact_common_key_replay=True)
    out['scope']='All conclusions conditional on model and equality assumptions. Restricted UNSAT excludes only the supplied fixed key neighborhood.'
    return out

if __name__=='__main__':
    from shared_update_support import assumptions
    from permutation_action_fold import make_plaintexts
    ap=argparse.ArgumentParser();ap.add_argument('--length',type=int,default=32);ap.add_argument('--rotation',type=int,default=9);ap.add_argument('--all-rotations',action='store_true');ap.add_argument('--timeout',type=int,default=20000);ap.add_argument('--output',required=True);a=ap.parse_args()
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cl=make_plaintexts(raw,assumptions(raw));ct=[m[:a.length] for m in raw];cl=[m[:a.length] for m in cl]
    r=solve(ct,cl,None if a.all_rotations else a.rotation,timeout=a.timeout)
    (ROOT/a.output).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions']},flush=True)
