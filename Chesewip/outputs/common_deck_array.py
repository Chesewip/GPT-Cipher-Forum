"""Exact common-initial-deck prefix solver for the rotating 3-card model.

The deck is an SMT array, updated in a rotating coordinate frame. Every SAT
result is replayed with ordinary physical deck updates on all messages.
"""
from pathlib import Path
import sys,json,time,argparse
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_three_cycle_scan import encrypt_physical

def solve(ct,classes,b,n=83,timeout=10000,pinned=None,fixed_key=None):
    start=time.time();M=n-1;width=(2*n).bit_length();bv=lambda x:z3.BitVecVal(int(x),width)
    sort=z3.BitVecSort(width);key=z3.Array('initial',sort,sort);values=[z3.Select(key,bv(i)) for i in range(n)]
    unique=list(dict.fromkeys(x for cl in classes for x in cl));p={x:z3.BitVec('p_'+str(i),width) for i,x in enumerate(unique)}
    solver=z3.Solver();solver.set(timeout=timeout)
    solver.add(z3.Distinct(*values),*(z3.ULT(x,bv(n)) for x in values),*(z3.ULT(x,bv(M)) for x in p.values()))
    if pinned is None and fixed_key is None:solver.add(next(iter(p.values()))==bv(0))
    if pinned is not None:
        for pt,cl in zip(pinned,classes):
            for v,x in zip(pt,cl):solver.add(p[x]==bv(v-1))
    if fixed_key is not None:solver.add(*(x==bv(v) for x,v in zip(values,fixed_key)))
    for mi,(message,cl) in enumerate(zip(ct,classes)):
        deck=key
        for t,c in enumerate(message):
            physical=p[cl[t]];offset=t*b%M;rotated=z3.If(z3.ULT(physical,bv(offset)),physical+bv(M-offset),physical-bv(offset));slot=rotated+bv(1)
            neighbor=z3.If(slot==bv(M),bv(1),slot+bv(1));old=z3.Select(deck,bv(0));tail=z3.Select(deck,neighbor)
            solver.add(z3.Select(deck,slot)==bv(c))
            deck=z3.Store(z3.Store(z3.Store(deck,slot,tail),neighbor,old),bv(0),bv(c))
    status=str(solver.check());out={'status':status,'rotation':b,'positions':sum(map(len,ct)),'lengths':list(map(len,ct)),
          'plaintext_classes':len(p),'seconds':time.time()-start,'common_initial_deck':True,'initial_key_pinned':fixed_key is not None,'selectors_pinned':pinned is not None}
    if status=='unknown':out['reason']=solver.reason_unknown()
    if status=='sat':
        model=solver.model();deck=[model.eval(v).as_long() for v in values];assignment={x:model.eval(v).as_long()+1 for x,v in p.items()};pt=[[assignment[x] for x in cl] for cl in classes]
        assert sorted(deck)==list(range(n))
        assert all(encrypt_physical(m,deck,1,b)==c for m,c in zip(pt,ct))
        out.update(initial_deck=deck,plaintext_positions=pt,exact_common_key_replay=True)
    out['warning']='A prefix fit with artificial selection positions is not meaningful plaintext or a recovered historical key.'
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--length',type=int,default=6);ap.add_argument('--timeout',type=int,default=10000);ap.add_argument('--rotation',type=int,default=9);args=ap.parse_args()
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());fullclasses=make_plaintexts(raw,assumptions(raw));ct=[m[:args.length] for m in raw];cl=[p[:args.length] for p in fullclasses]
    r=solve(ct,cl,args.rotation,timeout=args.timeout);r['assumed_equalities']=assumptions(raw)
    (ROOT/f'common_array_prefix_{args.length}_{args.rotation}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions','assumed_equalities']},flush=True)
