import sys,json,itertools,numpy as np
sys.path.insert(0,'outputs')
from progressive_reduction import RUNS
ct=list(json.load(open('outputs/ciphertext.json')).values())
def rref(a):
 a=np.array(a,dtype=np.int64)%83;r=0;pivots=[]
 for c in range(a.shape[1]):
  nz=np.flatnonzero(a[r:,c])
  if not len(nz):continue
  p=r+int(nz[0]);a[[r,p]]=a[[p,r]];a[r]=a[r]*pow(int(a[r,c]),-1,83)%83;v=a[:,c].copy();v[r]=0;a=(a-v[:,None]*a[r])%83;pivots.append(c);r+=1
  if r==len(a):break
 return a[:r],pivots
def collision(rows):
 a,pivots=rref(rows);free=[c for c in range(83) if c not in pivots];null=np.zeros((83,len(free)),dtype=np.int64)
 for i,c in enumerate(free):null[c,i]=1
 for r,c in enumerate(pivots):null[c]=-a[r,free]%83
 seen={}
 for c,row in enumerate(null):
  sig=tuple(row)
  if sig in seen:return seen[sig],c,len(pivots)
  seen[sig]=c
blocks=[]
for i,s,j,t,n in RUNS:
 rows=[];u0,v0=ct[i][s],ct[j][t]
 for k in range(1,n):
  row=np.zeros(83,dtype=np.int64);row[ct[i][s+k]]+=1;row[ct[j][t+k]]-=1;row[u0]-=1;row[v0]+=1;rows.append(row)
 blocks.append(rows)
for size in [1,2,3,4]:
 found=[]
 for subset in itertools.combinations(range(10),size):
  rows=[r for i in subset for r in blocks[i]];c=collision(rows)
  if c:found.append((subset,c))
 print('size',size,'excluded',len(found),'examples',found[:12],flush=True)
 if found:break
