import sys,json,numpy as np
sys.path.insert(0,'outputs')
from progressive_reduction import RUNS
from permutation_action_fold import make_plaintexts
ct=list(json.load(open('outputs/ciphertext.json')).values());eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in RUNS];cl=make_plaintexts(ct,eq);seen={};relations=[]
for i,row in enumerate(cl):
 for t,x in enumerate(row):
  if x in seen:j,u=seen[x];relations.append((j,u,i,t))
  else:seen[x]=(i,t)
def rank(mat):
 mat=np.array(mat,dtype=np.int64)%83;r=0
 for c in range(mat.shape[1]):
  piv=np.flatnonzero(mat[r:,c])
  if not len(piv):continue
  p=r+int(piv[0]);mat[[r,p]]=mat[[p,r]];mat[r]=mat[r]*pow(int(mat[r,c]),-1,83)%83;v=mat[:,c].copy();v[r]=0;mat=(mat-v[:,None]*mat[r])%83;r+=1
  if r==len(mat):break
 return r
ranks=[]
for a in range(1,83):
 rows=[]
 for i,s,j,t in relations:
  row=np.zeros(83,dtype=np.int64);row[ct[i][s]]+=1;row[ct[j][t]]-=1;row[ct[i][s-1]]-=a;row[ct[j][t-1]]+=a;rows.append(row)
 ranks.append(rank(rows))
print('relations',len(relations),'ranks',dict((r,ranks.count(r)) for r in set(ranks)));print([(a+1,r) for a,r in enumerate(ranks) if r<82])
