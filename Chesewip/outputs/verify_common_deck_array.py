from pathlib import Path
import json,random
from common_deck_array import solve
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent
rng=random.Random(20261104);results=[]
for n in [7,19,83]:
    key=rng.sample(list(range(n)),n);rotation=rng.randrange(n-1)
    shared=[rng.randrange(1,n) for _ in range(5)]
    pts=[[rng.randrange(1,n)]+shared+[rng.randrange(1,n) for _ in range(2)] for j in range(3)]
    cl=[[(99,t) if 1<=t<6 else (j,t) for t in range(len(pt))] for j,pt in enumerate(pts)]
    ct=[encrypt_physical(pt,key,1,rotation) for pt in pts]
    r=solve(ct,cl,rotation,n,10000);assert r['status']=='sat',r
    results.append({'n':n,'mode':'unknown_key_and_selectors','seconds':r['seconds'],'exact_replay':r['exact_common_key_replay']})
    r=solve(ct,cl,rotation,n,10000,pinned=pts);assert r['status']=='sat',r
    results.append({'n':n,'mode':'known_selectors_unknown_key','seconds':r['seconds'],'exact_replay':r['exact_common_key_replay']})
    damaged=[x.copy() for x in ct];damaged[0][4]=(damaged[0][4]+1)%n
    r=solve(damaged,cl,rotation,n,10000,pinned=pts,fixed_key=key);assert r['status']=='unsat',r
    results.append({'n':n,'mode':'damaged_output_pinned_key_and_selectors','status':r['status']})
(ROOT/'checked_common_deck_array.json').write_text(json.dumps({'controls':results},indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(results)
