from pathlib import Path
import random,json,itertools,time
from cycle_subset_bound import feasible,bound_for
from reduced_smt import encrypt
ROOT=Path(__file__).resolve().parent
rng=random.Random(20260911)
checks=0
for trial in range(100):
    L=7;mask=(1<<L)-1;patterns=[rng.randrange(1<<L) for _ in range(4)]
    brute=8
    for shifts in itertools.permutations(range(1,L),3):
        union=patterns[0]
        for p,s in zip(patterns[1:],shifts):union|=((p<<s)|(p>>(L-s)))&mask
        brute=min(brute,union.bit_count())
    for bound in range(8):
        assert (feasible(patterns,L,bound)['status']=='sat')==(brute<=bound)
        checks+=1
controls=[]
for trial in range(10):
    n=83;top=rng.randrange(n);cycle=[i for i in range(n) if i!=top];rng.shuffle(cycle)
    q=list(range(n))
    for i,c in enumerate(cycle):q[c]=cycle[(i+1)%82]
    letters=rng.sample(cycle,27)
    pts=[[rng.choice(letters) for _ in range(120)] for _ in range(9)]
    ct=[encrypt(pt,q,top) for pt in pts]
    result=bound_for(ct,83,top,8,27)
    assert result['status']=='sat',result
    controls.append(result)
out=dict(small_exhaustive_comparisons_passed=checks,planted_83_card_controls_passed=len(controls),controls=controls)
(ROOT/'cycle_bound_controls.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Passed',checks,'exhaustive small comparisons and',len(controls),'83-card hidden-cycle controls.')
