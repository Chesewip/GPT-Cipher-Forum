"""Output agreement without hidden-state agreement in a simple deck cipher.

For uniform choice among all n-1 non-top source positions and relative deck
support r, P(L further matching outputs | current outputs differ) equals
((n-r)/(n-1))*((n-1-r)/(n-1))**(L-1). Shared permutations preserve r.
"""
from pathlib import Path
from collections import Counter
import random,json,math,time
ROOT=Path(__file__).resolve().parent

def step(deck,p,b):
    n=len(deck);r=1+p%(n-1);a,c,e=deck[0],deck[p],deck[r]
    deck[0]=c;deck[p]=e;deck[r]=a
    if b:deck=[deck[0]]+deck[-b:]+deck[1:-b]
    return deck,c

def probability(n,r,length):return (n-r)/(n-1)*((n-1-r)/(n-1))**(length-1)

if __name__=='__main__':
    start=time.time();rng=random.Random(20261023);results=[]
    for A in [82,27]:
        count=10000;by_support=Counter();success=Counter();example=None;support_checks=0
        for trial in range(count):
            key=list(range(83));rng.shuffle(key);deck=key.copy();prefix=[];prefixct=[]
            for _ in range(24):
                p=rng.randrange(1,A+1);prefix.append(p);deck,c=step(deck,p,9);prefixct.append(c)
            p,q=rng.sample(range(1,A+1),2);da,ca=step(deck.copy(),p,9);db,cb=step(deck.copy(),q,9)
            assert ca!=cb
            r=sum(x!=y for x,y in zip(da,db));assert 0<r<=5;by_support[r]+=1
            suffix=[];oa=[];ob=[]
            for _ in range(13):
                v=rng.randrange(1,A+1);suffix.append(v);da,x=step(da,v,9);db,y=step(db,v,9)
                oa.append(x);ob.append(y)
                assert sum(x!=y for x,y in zip(da,db))==r;support_checks+=1
            if oa==ob:
                success[r]+=1
                if example is None:
                    example={'initial_deck':key,'plaintext_positions':[prefix+[p]+suffix,prefix+[q]+suffix],
                             'ciphertext':[prefixct+[ca]+oa,prefixct+[cb]+ob],
                             'relative_support':r,'different_plaintext_position':24,'identical_output_positions':[25,37],
                             'final_decks':[da,db]}
        groups=[]
        for r,nr in sorted(by_support.items()):
            row={'support':r,'trials':nr,'thirteen_output_agreements':success[r]}
            if A==82:
                pr=probability(83,r,13);z=(success[r]-nr*pr)/math.sqrt(nr*pr*(1-pr));assert abs(z)<6
                row.update(exact_probability=pr,expected_successes=nr*pr,descriptive_standardized_difference=z)
            groups.append(row)
        results.append({'plaintext_alphabet_size':A,'trials':count,'successes':sum(success.values()),
                        'fraction':sum(success.values())/count,'groups':groups,'support_invariance_checks':support_checks,
                        'generated_example':example})
        print(A,'success fraction',results[-1]['fraction'],'groups',groups,flush=True)
    support_pairs=Counter()
    for p in range(1,83):
        for q in range(1,83):
            if p==q:continue
            da,_=step(list(range(83)),p,9);db,_=step(list(range(83)),q,9)
            support_pairs[sum(x!=y for x,y in zip(da,db))]+=1
    assert support_pairs=={4:164,5:6478}
    exact_mixture=sum(count*probability(83,r,13) for r,count in support_pairs.items())/sum(support_pairs.values())
    out={'model':'Top/selected/next-ring-card three-cycle followed by bottom rotation 9; identical starting deck; one changed plaintext character; 13 shared subsequent characters.',
         'exhaustive_distinct_input_pair_support_counts':dict(support_pairs),
         'exact_uniform_82_thirteen_match_probability':exact_mixture,
         'results':results,'seconds':time.time()-start,
         'caveat':'Generated counterexamples and a uniform-input formula, not a probability model for the real Noita plaintext.'}
    (ROOT/'reconvergence_controls.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
