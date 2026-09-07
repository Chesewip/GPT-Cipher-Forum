"""Initial-key-independent return-gap bounds for common Q plus one swap."""
from pathlib import Path
import numpy as np
import json,collections,random
from key_swap_attack import encrypt,trace
ROOT=Path(__file__).resolve().parent

def verify():
    rng=np.random.default_rng(20260915);checks=0
    for L in range(1,84):
        rest=rng.permutation(np.arange(1,83)).tolist()
        cycle=[0]+rest[:L-1];outside=rest[L-1:]
        q=np.arange(83,dtype=np.int32)
        for i,c in enumerate(cycle):q[c]=cycle[(i+1)%L]
        shuffled=outside[:];random.Random(L).shuffle(shuffled)
        for i,j in zip(outside,shuffled):q[i]=j
        initial=rng.permutation(83)
        pts=[rng.integers(1,83,size=200).tolist() for _ in range(3)]
        ct=[encrypt(pt,q,initial) for pt in pts]
        powers=[0]
        for _ in range(L-1):powers.append(int(q[powers[-1]]))
        for m,pt in zip(ct,pts):
            last={}
            for t,c in enumerate(m):
                if c in last:
                    d=t-last[c]
                    if d<=L:
                        assert pt[t]==powers[d-1],(L,t,d,pt[t],powers[d-1])
                        checks+=1
                last[c]=t
    return checks

if __name__=='__main__':
    checked=verify()
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    distances=[];freq=collections.Counter()
    for m in messages:
        last={};row=[]
        for t,c in enumerate(m):
            d=t-last[c] if c in last else None;row.append(d)
            if d is not None:freq[d]+=1
            last[c]=t
        distances.append(row)
    out=dict(generated_return_gap_checks_passed=checked,
             lower_bounds=[dict(top_cycle_length=L,minimum_selection_alphabet=sum(d<=L for d in freq)) for L in range(1,84)],
             conditional_witness=dict(message='West 1',positions_zero_based=[38,68],
                                      observed_return_distances=[distances[1][38],distances[1][68]],
                                      assumption='These corresponding internal positions in the published repeated passage represent the same plaintext selection.',
                                      conclusion='The cycle of Q containing the top position has length at most 8.'),
             full_83_cycle_minimum_alphabet=sum(d<=83 for d in freq))
    (ROOT/'top_orbit_bounds.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Passed generated checks:',checked,'Full 83-cycle minimum alphabet:',out['full_83_cycle_minimum_alphabet'])
