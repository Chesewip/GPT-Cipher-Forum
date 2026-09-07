"""Independent integer/array encoding of relative cycle templates.

Optionally admits three-cycles as well, covering relative operations of any
two anchored three-cycles, not just the unit-neighbor construction.
"""
from pathlib import Path
import json,sys,time,argparse,random
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3

def solve(a,b,cuts,n=83,allow_three=False,timeout=10000):
    solver=z3.Solver();solver.set(timeout=timeout);r=[z3.IntVal(x) for x in range(n)];start=time.time();steps=[]
    for j,(lo,hi) in enumerate(zip(cuts,cuts[1:])):
        x=[z3.Int(f'p_{j}_{k}') for k in range(5)];kind=z3.Int(f'kind_{j}')
        solver.add(kind>=0,kind<=(2 if allow_three else 1)) # 0 two swaps, 1 five-cycle, 2 three-cycle
        solver.add(*(z3.And(v>=0,v<n) for v in x))
        solver.add(z3.Distinct(*x[:3]),z3.Implies(kind!=2,z3.Distinct(*x[:4])),z3.Implies(kind==1,z3.Distinct(*x)))
        solver.add(x[0]<x[1],x[0]<x[2],z3.Implies(kind==0,x[2]<x[3]),
                   z3.Implies(kind==1,z3.And(x[0]<x[3],x[0]<x[4])),
                   z3.Implies(kind!=1,x[4]==0),z3.Implies(kind==2,x[3]==0))
        array=z3.Array(f'r_{j}',z3.IntSort(),z3.IntSort())
        solver.add(*(z3.Select(array,i)==v for i,v in enumerate(r)))
        solver.add(r[a[lo]]!=b[lo])
        # Compose on the right: replace images at selected domain positions.
        new=[]
        for i in range(n):
            dest=z3.If(i==x[0],x[1],z3.If(i==x[1],z3.If(kind==0,x[0],x[2]),
                 z3.If(i==x[2],z3.If(kind==2,x[0],x[3]),
                 z3.If(z3.And(kind!=2,i==x[3]),z3.If(kind==0,x[2],x[4]),
                 z3.If(z3.And(kind==1,i==x[4]),x[0],i)))))
            new.append(z3.Select(array,dest))
        r=new
        for ca,cb in set(zip(a[lo:hi],b[lo:hi])):solver.add(r[ca]==cb)
        steps.append((x,kind))
    status=str(solver.check());out={'status':status,'seconds':time.time()-start,'cuts':cuts,'allow_three_cycle':allow_three}
    if status=='unknown':out['reason']=solver.reason_unknown()
    if status=='sat':
        m=solver.model();rel=list(range(n));witness=[]
        for (lo,hi),(x,kind) in zip(zip(cuts,cuts[1:]),steps):
            points=[m.eval(v).as_long() for v in x];k=m.eval(kind).as_long();delta=list(range(n))
            cycles=[points[:2],points[2:4]] if k==0 else [points[:5] if k==1 else points[:3]]
            for cycle in cycles:
                for u,v in zip(cycle,cycle[1:]+cycle[:1]):delta[u]=v
            assert rel[a[lo]]!=b[lo];rel=[rel[delta[i]] for i in range(n)]
            assert all(rel[ca]==cb for ca,cb in zip(a[lo:hi],b[lo:hi]))
            witness.append({'cycles':cycles,'relative_permutation':rel.copy()})
        out['witness']=witness
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--allow-three',action='store_true');ap.add_argument('--timeout',type=int,default=5000);args=ap.parse_args()
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());a,b=[x[:36] for x in raw[:2]]
    templates=json.loads((ROOT/'checked_compact_templates.json').read_text())['possible_difference_positions_zero_based'];out=[]
    for template in templates:
        r=solve(a,b,template+[36],allow_three=args.allow_three,timeout=args.timeout);out.append(r);print({k:v for k,v in r.items() if k!='witness'},flush=True)
    name='relative_cycle_integer'+('_with_three' if args.allow_three else '')+'.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
