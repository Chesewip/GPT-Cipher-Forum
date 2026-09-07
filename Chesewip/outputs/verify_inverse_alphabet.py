"""Exhaustive checks for the optional fixed contiguous selection alphabet."""
from pathlib import Path
import itertools,json
import numpy as np
from inverse_position_solver import solve
from shared_plaintext_search import decode_physical
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent
rng=np.random.default_rng(20261118);checks=[]
for trial in range(24):
 n=4+trial%2;M=n-1;A=1+trial%(M-1);headers=bool(trial%3);b=int(rng.integers(M));key=rng.permutation(n).tolist();pt=[rng.integers(1,A+1,6).tolist() for _ in range(2)];pt[1][2:5]=pt[0][1:4]
 if headers:
  for row in pt:row[0]=int(rng.integers(1,n))
 ct=[encrypt_physical(row,key,1,b) for row in pt];cl=[[(i,t) for t in range(6)] for i in range(2)];cl[1][2:5]=cl[0][1:4]
 if trial%4==0:ct[0][-1]=ct[0][-2]
 fixed={key[0]:0} if trial%5==0 else None;rotation=None if trial%2 else b;possible=False
 for k in itertools.permutations(range(n)):
  if fixed and any(k[p]!=c for c,p in fixed.items()):continue
  for rot in range(M) if rotation is None else [rotation]:
   decoded=decode_physical(ct,k,rot)
   if all(p>0 for row in decoded for p in row) and all(p<=A for row in decoded for p in row[int(headers):]) and decoded[1][2:5]==decoded[0][1:4]:possible=True;break
  if possible:break
 results=[]
 for reduced in [False,True]:
  r=solve(ct,cl,rotation,n,5000,fixed,reduce_observations=reduced,alphabet_bound=A,unrestricted_first=headers);assert r['status']!='unknown';assert (r['status']=='sat')==possible,(trial,r,possible);results.append(r['status']);assert r['bottom_rotation_gauge'] is False;assert r['encoded_lengths']==[6,6]
 checks.append(dict(trial=trial,n=n,alphabet_bound=A,unrestricted_first=headers,rotation=rotation,exhaustive_has_key=possible,results=results))
(ROOT/'checked_inverse_alphabet.json').write_text(json.dumps(dict(fixtures=len(checks),formulation_checks=2*len(checks),checks=checks),indent=2)+'\n',encoding='utf-8',newline='\r\n');print('Passed',len(checks),'exhaustive alphabet fixtures and',2*len(checks),'formulation checks.',flush=True)
