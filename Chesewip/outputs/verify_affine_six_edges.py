"""Independent six-edge certificate and finite affine/labeling controls."""
from pathlib import Path
import json,csv,random,collections,sys
from affine_fixed_point_scan import scan,observed_maps
ROOT=Path(__file__).resolve().parent
raw=json.loads((ROOT/'ciphertext.json').read_text());edges=[
 ('A','West 2',21,'West 3',26,47,18),
 ('A','West 2',26,'West 3',31,54,42),
 ('A','West 2',23,'West 3',28,21,43),
 ('B','East 4',75,'West 4',78,18,47),
 ('B','East 4',82,'West 4',85,42,54),
 ('B','East 4',77,'West 4',80,43,34)]
for name,source,s,target,t,x,y in edges:assert raw[source][s-1]==x and raw[target][t-1]==y
maps={name:{x:y for g,_,_,_,_,x,y in edges if g==name} for name in ['A','B']}
chains=[[x,maps['A'][x],maps['B'][maps['A'][x]]] for x in [47,54,21]]
assert chains==[[47,18,47],[54,42,54],[21,43,34]]
# Direct arithmetic over every invertible affine map, without a solver.
hist=collections.Counter()
for a in range(1,83):
 for b in range(83):
  perm=[(a*x+b)%83 for x in range(83)];fixed=sum(x==y for x,y in enumerate(perm));hist[fixed]+=1
  if fixed>=2:assert perm==list(range(83))
assert dict(hist)=={83:1,0:82,1:6723}
rng=random.Random(20261115);controls=0
for trial in range(100):
 labels=list(range(83));rng.shuffle(labels);partial=[]
 for k in range(3):
  a=rng.randrange(1,83);b=rng.randrange(83);domain=rng.sample(range(83),rng.randrange(14,31));partial.append({labels[x]:labels[(a*x+b)%83] for x in domain})
 r=scan(partial,6,verbose=False);assert r['status']!='affine_obstruction';controls+=1
# Renaming all ciphertext symbols must preserve the certificate.
for trial in range(100):
 labels=list(range(83));rng.shuffle(labels);a={labels[x]:labels[y] for x,y in maps['A'].items()};b={labels[x]:labels[y] for x,y in maps['B'].items()}
 assert b[a[labels[47]]]==labels[47] and b[a[labels[54]]]==labels[54] and b[a[labels[21]]]==labels[34]!=labels[21]
# The same six edges survive dropping the first two ciphertext positions of each run.
ct=list(raw.values())
for trim in [1,2,3]:
 full=observed_maps(ct,trim)
 assert all(full[6][x]==y for x,y in maps['A'].items()) and all(full[9][x]==y for x,y in maps['B'].items())
# Recheck against the separately stored published CSV if available.
reference=ROOT.parent/'work/reference/eye/reference/noita_eye_data_trigrams.csv';crosscheck=False
if reference.exists():
 rows=list(csv.reader(reference.open(newline='')));published={row[1]:[int(v) for v in row[2:] if v] for row in rows[1:]};assert published==raw;crosscheck=True
out=dict(status='conditional_affine_exclusion_verified',chains=chains,edges=[dict(context=g,source_message=s,source_position=i,target_message=t,target_position=j,source_label=x,target_label=y) for g,s,i,t,j,x,y in edges],affine_maps_enumerated=6806,fixed_point_histogram=dict(hist),random_relabelled_affine_controls=controls,random_certificate_relabelings=100,trims_verified=[1,2,3],published_csv_crosscheck=crosscheck,
 assumption='The two aligned passage pairs induce single context permutations in one common conjugate of AGL(1,83). This follows for affine GAK if the selected passages share plaintext. No plaintext equality is authenticated by this certificate.',
 conclusion='B composed with A has two distinct fixed symbols and moves a third, impossible for a nonidentity affine map. This also excludes the order-3403 affine subgroup under the same assumptions.',
 novelty='An independently derived compact certificate. Existing public work already reports affine exclusions; no first-discovery claim.')
(ROOT/'checked_affine_six_edge_certificate.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in out.items() if k!='edges'},flush=True)
