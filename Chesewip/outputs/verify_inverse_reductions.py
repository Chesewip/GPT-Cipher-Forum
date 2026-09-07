"""Exhaustive validation of reductions, symbolic rotation, and error budgets."""
from pathlib import Path
import json,itertools
import numpy as np
from inverse_position_solver import solve
from inverse_position_integer import solve as integer_solve
from shared_plaintext_search import decode_physical
ROOT=Path(__file__).resolve().parent
rng=np.random.default_rng(20261114);checks=[]
for trial in range(36):
    n=3+trial%3;M=n-1;key=rng.permutation(n).tolist();length=4+trial%3
    ct=[rng.integers(0,n,length).tolist() for _ in range(2)]
    if trial%3:
        for row in ct:
            for t in range(1,len(row)):
                if row[t]==row[t-1]:row[t]=(row[t]+1)%n
    cl=[[(i,t) for t in range(length)] for i in range(2)]
    for t in range(1,length):
        if rng.random()<0.8:cl[1][t]=cl[0][t-1]
    b=None if trial%2 else int(rng.integers(M));bound=trial%3;fixed={key[0]:0} if trial%4==0 else None;possible=False
    for k in itertools.permutations(range(n)):
        if fixed and any(k[p]!=c for c,p in fixed.items()):continue
        for rotation in range(M) if b is None else [b]:
            pts=decode_physical(ct,k,rotation);seen={};errors=0
            for row,classes in zip(pts,cl):
                for p,x in zip(row,classes):
                    if x in seen:errors+=p!=seen[x]
                    else:seen[x]=p
            if all(p>0 for row in pts for p in row) and errors<=bound:possible=True;break
        if possible:break
    statuses=[]
    for reduced,materialized in [(False,False),(True,False),(True,True)]:
        r=solve(ct,cl,b,n,5000,fixed,max_errors=bound,reduce_observations=reduced,materialize=materialized)
        assert r['status']!='unknown';assert (r['status']=='sat')==possible,(trial,r,possible);statuses.append(r['status'])
    if bound==0:
        r=integer_solve(ct,cl,b,n,5000,fixed);assert r['status']!='unknown';assert (r['status']=='sat')==possible;statuses.append(r['status'])
    checks.append(dict(trial=trial,n=n,rotation=b,error_bound=bound,independent_exhaustive_has_key=possible,statuses=statuses))
(ROOT/'checked_inverse_reductions.json').write_text(json.dumps(dict(exhaustive_fixtures=len(checks),formulation_comparisons=sum(len(c['statuses']) for c in checks),checks=checks),indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Passed',len(checks),'exhaustive fixtures;',sum(len(c['statuses']) for c in checks),'formulation checks.',flush=True)
