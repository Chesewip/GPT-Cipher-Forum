"""Independent exhaustive and physical checks of inverse position encoding."""
from pathlib import Path
import json,itertools
import numpy as np
from inverse_position_solver import solve
from shared_plaintext_search import decode_physical
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent
rng=np.random.default_rng(20261112);checks=[]
for n in [4,5]:
    for trial in range(12):
        b=int(rng.integers(n-1));key=rng.permutation(n).tolist();pt=[rng.integers(1,n,6).tolist() for _ in range(2)];pt[1][2:5]=pt[0][1:4]
        ct=[encrypt_physical(row,key,1,b) for row in pt];cl=[[(i,t) for t in range(6)] for i in range(2)];cl[1][2:5]=cl[0][1:4]
        if trial%2:ct[0][int(rng.integers(6))]=int(rng.integers(n))
        fixed={key[0]:0,key[2]:2} if trial%3==0 else None
        possible=False
        for k in itertools.permutations(range(n)):
            if fixed and any(k[p]!=c for c,p in fixed.items()):continue
            decoded=decode_physical(ct,k,b)
            if all(p>0 for row in decoded for p in row) and decoded[1][2:5]==decoded[0][1:4]:possible=True;break
        r=solve(ct,cl,b,n,5000,fixed)
        assert r['status']!='unknown';assert (r['status']=='sat')==possible,(n,trial,possible,r)
        checks.append(dict(n=n,trial=trial,independent_exhaustive_has_key=possible,status=r['status']))
for n in [7,19,83]:
    b=3%(n-1);key=rng.permutation(n).tolist();pt=[rng.integers(1,n,10).tolist() for _ in range(3)];pt[1][3:7]=pt[0][2:6];pt[2][2:6]=pt[0][2:6]
    ct=[encrypt_physical(row,key,1,b) for row in pt];cl=[[(i,t) for t in range(10)] for i in range(3)];cl[1][3:7]=cl[0][2:6];cl[2][2:6]=cl[0][2:6]
    # The actual key is in each six-free-slot neighborhood.
    free=set(rng.choice(n,min(6,n),replace=False).tolist());fixed={c:p for p,c in enumerate(key) if p not in free}
    r=solve(ct,cl,b,n,10000,fixed);assert r['status']=='sat'
    checks.append(dict(n=n,fixture='known solution in restricted neighborhood',status=r['status'],seconds=r['seconds']))
    bad=[row.copy() for row in ct];bad[0][1]=bad[0][0]
    r=solve(bad,cl,b,n,10000,{c:p for p,c in enumerate(key)});assert r['status']=='unsat'
    checks.append(dict(n=n,fixture='adjacent repeat impossible with non-top selectors',status=r['status']))
(ROOT/'checked_inverse_positions.json').write_text(json.dumps(dict(checks=checks,total=len(checks)),indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Passed',len(checks),'independent checks.',flush=True)
