"""Independent slow partition-refinement check for action folding."""
from pathlib import Path
import json,random
from permutation_action_fold import solve
ROOT=Path(__file__).resolve().parent

def independent(pts,cts):
    edges=[];observations=[];count=1
    # No prefix sharing; each observation has its own complete reversed path.
    for pt,ct in zip(pts,cts):
        for t,c in enumerate(ct):
            node=0
            for token in reversed(pt[:t+1]):
                new=count;count+=1;edges.append((node,token,new));node=new
            observations.append((node,c))
    partition=list(range(count))
    def merge(a,b):
        ca,cb=partition[a],partition[b]
        if ca==cb:return False
        partition[:]=[ca if x==cb else x for x in partition]
        return True
    by_card={}
    for node,c in observations:
        if c in by_card:merge(node,by_card[c])
        else:by_card[c]=node
    changed=True
    while changed:
        changed=False
        for reverse in [False,True]:
            groups={}
            for a,token,b in edges:
                if reverse:a,b=b,a
                key=(partition[a],token)
                if key in groups:
                    if merge(b,groups[key]):changed=True;break
                else:groups[key]=b
            if changed:break
    by_node={}
    for node,c in observations:
        p=partition[node]
        if p in by_node and by_node[p]!=c:return 'contradiction'
        by_node[p]=c
    return 'relaxation_survives'

rng=random.Random(20261028);counts={}
for _ in range(300):
    pts=[[rng.randrange(4) for _ in range(rng.randrange(2,9))] for j in range(2)]
    cts=[[rng.randrange(5) for x in pt] for pt in pts]
    a=independent(pts,cts);b=solve(pts,cts)['status'];assert a==b,(pts,cts,a,b)
    counts[a]=counts.get(a,0)+1
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());c=raw[2][37:]
# Only extract three short word spans; no reproduction of the full source text.
quote='SUBLIME THAT WHICH IS THE LOWEST, AND MAKE THAT WHICH IS THE HIGHEST, THE LOWEST.'
assert quote[21:26]==quote[69:74]
assert c[20]==c[25] and c[64]==c[73] and c[64]!=c[68]
out={'independent_partition_refinement_cases':300,'outcomes':counts,
     'published_waite_certificate_independently_checked':True,
     'waite_observation_offsets_zero_based':[20,25,64,68,73],
     'waite_observation_cards':[c[t] for t in [20,25,64,68,73]],
     'source':'https://github.com/mvelzel/eye-vibe/blob/main/docs/waite-sparse-gak-results-2026-07-27.md'}
(ROOT/'checked_action_fold.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(out)
