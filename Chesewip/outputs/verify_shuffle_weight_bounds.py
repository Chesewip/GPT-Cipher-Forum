"""Controls for the partial-permutation weight and plaintext-change bounds."""
from pathlib import Path
import random,json,itertools
from shuffle_weight_bounds import partial_weight,bound,segment_table
from plaintext_change_bounds import encrypt
ROOT=Path(__file__).resolve().parent

def weight(p):
    seen=set();out=0
    for x in range(len(p)):
        if x in seen:continue
        v=x;size=0
        while v not in seen:seen.add(v);size+=1;v=p[v]
        out+=size//2
    return out

rng=random.Random(20261024);partial_checks=0;metric_checks=0;brute_checks=0;generated=[]
for n in range(3,7):
    permutations=list(itertools.permutations(range(n)));weights=[weight(p) for p in permutations]
    for trial in range(30):
        true=rng.choice(permutations);observed=rng.sample(range(n),rng.randrange(n+1));f={x:true[x] for x in observed}
        minimum=min(w for p,w in zip(permutations,weights) if all(p[x]==y for x,y in f.items()))
        assert minimum==partial_weight(f);partial_checks+=1
    for _ in range(200):
        p,q=rng.choices(permutations,k=2);composed=[p[q[x]] for x in range(n)]
        assert weight(composed)<=weight(p)+weight(q);metric_checks+=1
for _ in range(100):
    a=[rng.randrange(4) for _ in range(8)];b=[rng.randrange(4) for _ in range(8)]
    if a[0]==b[0]:b[0]=(a[0]+1)%4
    segments=segment_table(a,b)
    for budget in [1,2]:
        best=8
        for mask in range(1<<7):
            cuts=[0]+[t for t in range(1,8) if mask>>(t-1)&1]+[8]
            if all((l,r) in segments and segments[l,r]<=budget*k for k,(l,r) in enumerate(zip(cuts,cuts[1:]),1)):
                best=min(best,len(cuts)-1)
        assert bound(a,b,budget)['minimum_plaintext_differences']==best;brute_checks+=1
for budget in [1,2]:
    for n in [7,19,83]:
        for trial in range(30):
            q=list(range(n));rng.shuffle(q);anchor=q.index(0);sources=list(range(1,n));perms=[]
            for p in sources:
                move=list(range(n))
                if p!=anchor:
                    if budget==1:move[anchor],move[p]=p,anchor
                    else:
                        r=rng.choice([x for x in range(n) if x not in [anchor,p]])
                        move[p]=anchor;move[r]=p;move[anchor]=r
                perms.append([q[move[x]] for x in range(n)])
            key=list(range(n));rng.shuffle(key);pa=[rng.randrange(n-1) for _ in range(50)];pb=pa.copy()
            for t in {0}|set(rng.sample(range(1,50),rng.randrange(1,12))):
                pb[t]=rng.choice([p for p in range(n-1) if p!=pa[t]])
            ca=encrypt(pa,key,perms);cb=encrypt(pb,key,perms);actual=sum(x!=y for x,y in zip(pa,pb))
            result=bound(ca,cb,budget)['minimum_plaintext_differences'];assert result<=actual
            generated.append({'n':n,'budget':budget,'actual_differences':actual,'lower_bound':result})
report=json.loads((ROOT/'shuffle_weight_bounds.json').read_text());assert report['east1_west1'][-1]['bounds'][0]['minimum_plaintext_differences']==11
out={'exhaustive_partial_completion_checks':partial_checks,'metric_checks':metric_checks,
     'exhaustive_partition_checks':brute_checks,'generated_cipher_controls':generated,
     'generated_controls_count':len(generated),'all_passed':True}
(ROOT/'checked_shuffle_weight_bounds.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print({k:v for k,v in out.items() if k!='generated_cipher_controls'})
