"""Bit-vector return-path constraints for the unit-neighbor rotating three-cycle.

No initial-key or alphabet-size constraints. SAT is only a relaxation.
Plaintext equality assumptions are explicit and may be omitted.
"""
from pathlib import Path
import sys,json,time,argparse
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from progressive_reduction import RUNS
from clocked_three_cycle_scan import encrypt_physical

def build(messages,n,eq=(),gap=10000,pinned=None):
    M=n-1;width=M.bit_length()+1;bv=lambda x:z3.BitVecVal(int(x),width)
    parent={(i,t):(i,t) for i,m in enumerate(messages) for t in range(len(m))}
    def root(x):
        if parent[x]!=x:parent[x]=root(parent[x])
        return parent[x]
    for i,s,j,t,length in eq:
        for k in range(length):parent[root((i,s+k))]=root((j,t+k))
    variables={root(x):z3.BitVec('p_'+str(root(x)[0])+'_'+str(root(x)[1]),width) for x in parent}
    pp=[[variables[root((i,t))] for t in range(len(m))] for i,m in enumerate(messages)]
    b=z3.BitVec('rotation',width);solver=z3.SolverFor('QF_BV')
    solver.add(z3.ULT(b,bv(M)))
    for p in variables.values():solver.add(z3.ULT(p,bv(M)))
    if pinned is None:solver.add(pp[0][1]==bv(0))
    else:
        for m,pt in zip(pp,pinned):
            for p,v in zip(m,pt):solver.add(p==bv(v-1))
    def add(x,y):
        total=x+y
        return z3.If(z3.UGE(total,bv(M)),total-bv(M),total)
    def prev(x):return z3.If(x==bv(0),bv(M-1),x-bv(1))
    intervals=0;steps=0
    for i,(m,pt) in enumerate(zip(messages,pp)):
        last={}
        for t,c in enumerate(m):
            if c in last and t-last[c]<=gap:
                r=last[c]
                assert t-r>=2
                u=add(add(pt[r+1],bv(1)),b);intervals+=1
                for s in range(r+2,t):
                    solver.add(pt[s]!=u)
                    v=z3.BitVec('v_'+str(i)+'_'+str(r)+'_'+str(s),width)
                    rotated=add(u,b)
                    solver.add(v==z3.If(pt[s]==prev(u),prev(rotated),rotated))
                    u=v;steps+=1
                solver.add(pt[t]==u)
            last[c]=t
    return solver,b,pp,{'return_intervals':intervals,'intermediate_steps':steps,'plaintext_variables':len(variables)}

def verify():
    rng=np.random.default_rng(20261015);results=[]
    for n in [7,11,83]:
        for trial in range(5):
            b=int(rng.integers(n-1));key=rng.permutation(n);shared=rng.integers(1,n,size=30).tolist()
            pt=[rng.integers(1,n,size=12).tolist()+shared+rng.integers(1,n,size=10).tolist() for _ in range(3)]
            ct=[encrypt_physical(m,key,1,b) for m in pt];eq=[(0,12,1,12,30),(0,12,2,12,30)]
            solver,var,_,counts=build(ct,n,eq,pinned=pt);solver.add(var==b);solver.set(timeout=10000)
            status=solver.check();assert status==z3.sat,(n,b,status)
            results.append({'n':n,'rotation':b,'status':str(status),**counts})
    return results

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--gap',type=int,default=10000)
    ap.add_argument('--seconds',type=int,default=4);ap.add_argument('--rotations',type=int,nargs='*')
    ap.add_argument('--equalities',choices=['none','all','long'],default='all');args=ap.parse_args()
    start=time.time();controls=verify();messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    runs=[] if args.equalities=='none' else [r for r in RUNS if args.equalities=='all' or r[-1]>=14]
    eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in runs]
    solver,b,pt,counts=build(messages,83,eq,args.gap);solver.set(timeout=args.seconds*1000)
    results=[]
    for offset in args.rotations if args.rotations is not None else range(82):
        now=time.time();solver.push();solver.add(b==offset);status=solver.check()
        result={'rotation':offset,'status':str(status),'seconds':time.time()-now}
        if status==z3.unknown:result['reason']=solver.reason_unknown()
        # A satisfying assignment deliberately is not represented as plaintext.
        solver.pop();results.append(result);print(result,flush=True)
    out={'generated_controls':controls,'results':results,'assumed_equalities':eq,
         'initial_key_constraints':False,'alphabet_bound':None,'gap':args.gap,**counts,
         'scope':'Unit-neighbor rotating three-cycle; arbitrary selections; shared plaintext only as explicitly listed. SAT is a relaxation.',
         'seconds':time.time()-start}
    name=f'return_bv_{args.equalities}_{args.gap}.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('total seconds',out['seconds'])
