"""Time-aware relaxation: at most s relative mapping entries change per input difference."""
from pathlib import Path
import sys,json,time,argparse
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3

def intervals(a,b,n,row,common=True):
    full=(1<<n)-1;domains=[((1<<cb) if ca==row else full^(1<<cb)) for ca,cb in zip(a,b)]
    if common:domains=[1<<row]+domains
    offset=-1 if common else 0;found=[]
    for start in range(len(domains)):
        possible=full
        for end in range(start,len(domains)):
            possible&=domains[end]
            if not possible:
                found.append((start+offset+1,end+offset));break
    # A clause for a contained interval implies its containing intervals.
    return sorted(set(iv for iv in found if not any(j!=iv and iv[0]<=j[0] and j[1]<=iv[1] for j in found)))

def solve(a,b,s,limit,n=83,timeout=10000,common=True):
    start=time.time();solver=z3.Solver();solver.set(timeout=timeout);N=len(a)
    y=[z3.Bool(f'y_{t}') for t in range(N)];by_time=[[] for t in range(N)];num_intervals=0
    for row in range(n):
        ivs=intervals(a,b,n,row,common)
        if not ivs:continue
        active=sorted({t for lo,hi in ivs for t in range(lo,hi+1)})
        x={t:z3.Bool(f'x_{row}_{t}') for t in active}
        for lo,hi in ivs:solver.add(z3.Or(*[x[t] for t in range(lo,hi+1)]));num_intervals+=1
        for t,v in x.items():by_time[t].append(v);solver.add(z3.Implies(v,y[t]))
    for xs in by_time:
        if xs:solver.add(z3.PbLe([(v,1) for v in xs],s))
    solver.add(z3.PbLe([(v,1) for v in y],limit))
    result=str(solver.check());out={'status':result,'maximum_differences':limit,'support_per_difference':s,'seconds':time.time()-start,'intervals':num_intervals}
    if result=='unknown':out['reason']=solver.reason_unknown()
    if result=='sat':
        m=solver.model();out['possible_change_positions']=[t for t,v in enumerate(y) if z3.is_true(m.eval(v))]
        out['row_changes']={str(row):[t for t in range(N) if z3.is_true(m.eval(z3.Bool(f'x_{row}_{t}')))] for row in range(n)}
        for row in range(n):
            chosen=out['row_changes'][str(row)]
            assert all(any(lo<=t<=hi for t in chosen) for lo,hi in intervals(a,b,n,row,common))
        assert all(sum(t in xs for xs in out['row_changes'].values())<=s for t in range(N))
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--length',type=int,default=99);ap.add_argument('--budget',type=int,default=18);ap.add_argument('--timeout',type=int,default=10000);args=ap.parse_args()
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());r=solve(raw[0][:args.length],raw[1][:args.length],5,args.budget,timeout=args.timeout)
    (ROOT/f'entry_change_timing_{args.length}_{args.budget}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in r.items() if k!='row_changes'},flush=True)
