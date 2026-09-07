from pathlib import Path
import json,sys,numpy as np
sys.path.insert(0,'outputs')
from affine_linear_certificate import matrix
D=json.load(open('outputs/affine_strong_linear_trim3.json'));maps=[dict(m) for m in D['observed_maps'][:2]];a=matrix(maps,D['stage1_open_pairs'][0],D['anchors']);r=0;piv=[]
for c in range(a.shape[1]-1):
 nz=np.flatnonzero(a[r:,c])
 if not len(nz):continue
 p=r+int(nz[0]);a[[r,p]]=a[[p,r]];a[r]=a[r]*pow(int(a[r,c]),-1,83)%83;v=a[:,c].copy();v[r]=0;a=(a-v[:,None]*a[r])%83;piv.append(c);r+=1
 if r==len(a):break
free=[x for x in range(a.shape[1]-1) if x not in piv];pr={c:i for i,c in enumerate(piv)};obs=sorted({x for m in maps for p in m.items() for x in p});expr={c:({k:int(-a[pr[c],k]%83) for k in free if a[pr[c],k]} if c in pr else {c:1}) for c in obs};print({v:[c for c,ex in expr.items() if v in ex] for v in free if any(v in ex for ex in expr.values())})
