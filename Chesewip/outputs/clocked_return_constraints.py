"""Key-independent necessary constraints for clocked three-cycle ciphers.

Track each emitted card only until its next occurrence. Initial deck and
first occurrences are deliberately unconstrained. UNSAT can exclude the
model under stated plaintext equalities; SAT is only a relaxation.
"""
from pathlib import Path
import sys,json,time,argparse
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from progressive_reduction import RUNS
from clocked_three_cycle_scan import encrypt_physical

def build(messages,n,equalities=(),max_gap=10000,fixed=None,pinned=None,timeout=45000,unit_only=False):
    M=n-1;solver=z3.Solver();solver.set(timeout=timeout)
    d=z3.Int('neighbor_offset');b=z3.Int('shuffle_offset')
    solver.add(d>=1,d<M,b>=0,b<M)
    if fixed is not None:solver.add(d==fixed[0],b==fixed[1])
    elif n==83:
        # Multiplication of all ring coordinates by a unit gives equivalent
        # d,b with a different arbitrary initial key: 82+82+4 representatives.
        solver.add(z3.Or(d==1,d==2,z3.And(d==41,z3.Or(b==0,b==1,b==2,b==41))))
    if unit_only:solver.add(d==1,b!=0)
    pt=[[z3.Int('p_'+str(mi)+'_'+str(t)) for t in range(len(m))] for mi,m in enumerate(messages)]
    for pp in pt:
        for p in pp:solver.add(p>=0,p<M)
    for i,s,j,t,length in equalities:
        for k in range(length):solver.add(pt[i][s+k]==pt[j][t+k])
    if pinned is not None:
        for pp,values in zip(pt,pinned):
            for p,v in zip(pp,values):solver.add(p==v-1)
    else:solver.add(pt[0][1]==0)  # Global ring rotation is a gauge symmetry.
    intervals=0;steps=0
    for mi,(m,pp) in enumerate(zip(messages,pt)):
        last={}
        for t,c in enumerate(m):
            if c in last:
                r=last[c]
                if t-r==1:raise ValueError('Adjacent repeats require a separate identity-selection case')
                if t-r<=max_gap:
                    intervals+=1;u=(pp[r+1]+d+b)%M
                    for s in range(r+2,t):
                        solver.add(pp[s]!=u)
                        v=z3.Int('card_'+str(mi)+'_'+str(r)+'_'+str(s))
                        solver.add(v==(z3.If((pp[s]+d)%M==u,pp[s],u)+b)%M)
                        u=v;steps+=1
                    solver.add(pp[t]==u)
            last[c]=t
    return solver,pt,d,b,{'return_intervals':intervals,'intermediate_card_steps':steps}

def solve(messages,n,eq,max_gap,fixed=None,pinned=None,timeout=45000,unit_only=False):
    start=time.time();solver,pt,d,b,counts=build(messages,n,eq,max_gap,fixed,pinned,timeout,unit_only)
    built=time.time()-start;answer=solver.check()
    out={'status':str(answer),'build_seconds':built,'seconds':time.time()-start,'max_gap':max_gap,**counts}
    if answer==z3.sat:
        model=solver.model();out['neighbor_offset']=model.eval(d).as_long();out['shuffle_offset']=model.eval(b).as_long()
        out['relaxed_plaintext']=[[model.eval(p).as_long()+1 for p in pp] for pp in pt]
    elif answer==z3.unknown:out['reason']=solver.reason_unknown()
    return out

def verify():
    rng=np.random.default_rng(20260930);results=[]
    for n in [11,83]:
        for trial in range(5):
            key=rng.permutation(n);d=int(rng.integers(1,n-1));b=int(rng.integers(0,n-1))
            pt=[rng.integers(1,n,size=70).tolist() for _ in range(3)]
            ct=[encrypt_physical(p,key,d,b) for p in pt]
            out=solve(ct,n,[],10000,(d,b),pt,10000)
            assert out['status']=='sat',(n,trial,out)
            results.append({'n':n,'trial':trial,'return_intervals':out['return_intervals'],'intermediate_card_steps':out['intermediate_card_steps']})
    return results

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true')
    ap.add_argument('--gap',type=int,default=8);ap.add_argument('--long-only',action='store_true')
    ap.add_argument('--unit-only',action='store_true')
    ap.add_argument('--seconds',type=int,default=45);args=ap.parse_args()
    if args.verify:
        results=verify();out={'passed':True,'controls':results};name='clocked_return_controls.json'
    else:
        messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
        runs=[r for r in RUNS if not args.long_only or r[-1]>=14]
        eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in runs]
        out=solve(messages,83,eq,args.gap,timeout=args.seconds*1000,unit_only=args.unit_only)
        out['assumed_plaintext_equalities']=eq;out['initial_key_constraints_included']=False
        out['unit_neighbor_nonzero_shuffle_only']=args.unit_only
        name='clocked_return_'+('long' if args.long_only else 'all')+'_'+str(args.gap)+('_unit' if args.unit_only else '')+'.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in out.items() if k not in ['relaxed_plaintext','assumed_plaintext_equalities']})
