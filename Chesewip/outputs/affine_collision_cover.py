"""Export row certificates and an 83-case collision cover for slope pair (52,32)."""
from pathlib import Path
import json
import numpy as np
from affine_linear_certificate import matrix
ROOT=Path(__file__).resolve().parent
linear=json.loads((ROOT/'affine_strong_linear_trim3.json').read_text());packing=json.loads((ROOT/'affine_last_family_packing.json').read_text());case=next(r for r in packing['results'] if r['multipliers']==[52,32]);maps=[dict(m) for m in linear['observed_maps'][:2]];original=matrix(maps,[52,32],linear['anchors']);a=original.copy();T=np.eye(len(a),dtype=np.int64);r=0;piv=[]
for c in range(a.shape[1]-1):
 nz=np.flatnonzero(a[r:,c])
 if not len(nz):continue
 p=r+int(nz[0]);a[[r,p]]=a[[p,r]];T[[r,p]]=T[[p,r]];scale=pow(int(a[r,c]),-1,83);a[r]=a[r]*scale%83;T[r]=T[r]*scale%83;v=a[:,c].copy();v[r]=0;a=(a-v[:,None]*a[r])%83;T=(T-v[:,None]*T[r])%83;piv.append(c);r+=1
 if r==len(a):break
pr={c:i for i,c in enumerate(piv)};fixed={int(c):v for c,v in case['fixed_coordinates'].items()};moving={int(c):e for c,e in case['expressions'].items() if '57' in e['coefficients']};proofs=[]
for c in sorted(set(fixed)|set(moving)):
 e=case['expressions'][str(c)];target=np.zeros(a.shape[1],dtype=np.int64);target[c]=1
 for v,coeff in e['coefficients'].items():target[int(v)]-=coeff
 target[-1]=e['constant'];w=T[pr[c]] if c in pr else np.zeros(len(a),dtype=np.int64);assert np.array_equal(w@original%83,target%83);proofs.append(dict(label=c,expression=e,weights=w.tolist()))
cover=[]
for q in range(83):
 values={**fixed,**{c:(e['constant']+e['coefficients']['57']*q)%83 for c,e in moving.items()}};seen={};collision=None
 for c,value in values.items():
  if value in seen:collision=[seen[value],c,value];break
  seen[value]=c
 assert collision is not None;cover.append(dict(parameter=q,collision_labels=collision[:2],shared_coordinate=collision[2]))
out=dict(status='no_injective_embedding',multipliers=[52,32],anchors=linear['anchors'],parameter_label=57,coordinate_equations=proofs,collision_cover=cover,scope='Excludes the fourth linear survivor for the two last-family maps. Every possible F83 value of coordinate 57 forces two distinct ciphertext labels to collide.')
(ROOT/'affine_pair_52_32_collision_certificate.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n');print('Certified',len(proofs),'coordinate equations and',len(cover),'exhaustive parameter collisions.',flush=True)
