"""Verify every recorded affine exclusion using only integer row combinations.
This verifier does not perform elimination and does not import its discovery code.
"""
from pathlib import Path
import json,random,itertools,collections,time
ROOT=Path(__file__).resolve().parent
start=time.time();data=json.loads((ROOT/'affine_strong_linear_trim3.json').read_text());maps=[dict(p) for p in data['observed_maps']]
# Re-extract the strong contexts from the corpus, without importing the scanner.
ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());contexts=data['contexts'];extracted=[]
for i,s,j,t,n in contexts:extracted.append(dict(zip(ct[i][s+2:s+n],ct[j][t+2:t+n])))
assert maps==[extracted[i] for i in data['map_order']]
def check(case,selected):
    parameters=case['multipliers'];n=83+len(selected);sums=[0]*(n+1);weights=iter(case['weights'])
    for g,(mapping,a) in enumerate(zip(selected,parameters)):
        for x,y in mapping.items():
            w=next(weights);sums[y]+=w;sums[x]-=a*w;sums[83+g]-=w
    for label,value in zip(data['anchors'],[0,1]):w=next(weights);sums[label]+=w;sums[-1]+=w*value
    assert next(weights,None) is None;sums=[v%83 for v in sums]
    if case['status']=='inconsistent':assert sums[:-1]==[0]*n and sums[-1]!=0
    else:
        a,b=case['collision'];assert 0<=a<83 and 0<=b<83 and a!=b;target=[0]*(n+1);target[a]=1;target[b]=82;assert sums==target
pairs=[tuple(r['multipliers']) for r in data['stage1']];assert len(pairs)==6724 and set(pairs)==set(itertools.product(range(1,83),repeat=2));open_pairs=[];verified=0
for r in data['stage1']:
    if r['status']=='linear_test_open':open_pairs.append(tuple(r['multipliers']))
    else:check(r,maps[:2]);verified+=1
assert set(open_pairs)==set(map(tuple,data['stage1_open_pairs']))
triples=[tuple(r['multipliers']) for r in data['stage2']];assert len(triples)==len(open_pairs)*82 and set(triples)=={p+(a,) for p in open_pairs for a in range(1,83)}
for r in data['stage2']:assert r['status'] in ['inconsistent','forced_collision'];check(r,maps);verified+=1
# Known conjugate-affine fixtures cannot be ruled out by the discovery analyzer.
from affine_linear_certificate import analyze
rng=random.Random(20261116);controls=0
for trial in range(150):
    labels=list(range(83));rng.shuffle(labels);trial_maps=[];slopes=[]
    for j in range(2+trial%2):
        a=rng.randrange(1,83);b=rng.randrange(83);domain=rng.sample(range(83),rng.randrange(8,32));slopes.append(a);trial_maps.append({labels[x]:labels[(a*x+b)%83] for x in domain})
    r=analyze(trial_maps,slopes,[labels[0],labels[1]]);assert r['status']=='linear_test_open';controls+=1
out=dict(status='all_recorded_exclusions_verified',certificates_checked=verified,multiplier_triples_covered=82**3,stage1_pairs=len(pairs),stage1_open_pairs=open_pairs,stage2_triples=len(triples),generated_affine_controls=controls,independent_corpus_context_extraction=True,seconds=time.time()-start,scope='Exclusion conditional on the three strong passage-context assumptions. The verifier uses direct modular row sums, not a solver verdict.')
(ROOT/'checked_affine_strong_linear.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n');print(out,flush=True)
