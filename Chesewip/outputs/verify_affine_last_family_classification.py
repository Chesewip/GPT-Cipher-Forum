"""Direct verification of the complete three-pair last-family classification."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
linear=json.loads((ROOT/'affine_strong_linear_trim3.json').read_text());packing=json.loads((ROOT/'affine_last_family_packing.json').read_text());cert=json.loads((ROOT/'affine_pair_52_32_collision_certificate.json').read_text());maps=[dict(m) for m in linear['observed_maps'][:2]];rows=[]
for g,(mapping,a) in enumerate(zip(maps,[52,32])):
 for x,y in mapping.items():
  row=[0]*86;row[y]+=1;row[x]-=a;row[83+g]-=1;rows.append(row)
for c,value in zip(linear['anchors'],[0,1]):row=[0]*86;row[c]=1;row[-1]=value;rows.append(row)
expressions={}
for equation in cert['coordinate_equations']:
 assert len(equation['weights'])==len(rows)
 c=equation['label'];e=equation['expression'];sums=[sum(w*row[k] for w,row in zip(equation['weights'],rows))%83 for k in range(86)];target=[0]*86;target[c]=1
 for v,coeff in e['coefficients'].items():target[int(v)]-=coeff
 target[-1]=e['constant'];assert sums==[v%83 for v in target];expressions[c]=e
assert {r['parameter'] for r in cert['collision_cover']}==set(range(83)) and len(cert['collision_cover'])==83
for r in cert['collision_cover']:
 q=r['parameter'];a,b=r['collision_labels'];assert a!=b
 def coordinate(c):
  e=expressions[c];assert set(e['coefficients'])<={'57'};return (e['constant']+e['coefficients'].get('57',0)*q)%83
 assert coordinate(a)==coordinate(b)==r['shared_coordinate']
valid=[]
for r in packing['results']:
 if r['status']!='affine_context_embedding':continue
 coordinates=r['coordinates'];assert sorted(coordinates)==list(range(83))
 for mapping,a,b in zip(maps,r['multipliers'],r['offsets']):assert all(coordinates[y]==(a*coordinates[x]+b)%83 for x,y in mapping.items())
 valid.append(r['multipliers'])
assert sorted(valid)==[[4,24],[42,30],[45,7]]
out=dict(status='three_exact_multiplier_pairs',valid_multiplier_pairs=valid,excluded_linear_survivor=[52,32],coordinate_equations_verified=len(expressions),parameter_values_exhausted=83,complete_bijective_embeddings_verified=3,scope='Combine with checked_affine_strong_linear.json stage-one coverage. Classification concerns the two last-family partial context maps only, under the recorded affine-coordinate normalization.')
(ROOT/'checked_affine_last_family_classification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n');print(out,flush=True)
