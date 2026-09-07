"""Exact crib-to-initial-key constraints and a held-out recovery benchmark."""
from pathlib import Path
import json,argparse
import numpy as np
from clocked_three_cycle_scan import encrypt_physical
from english_clocked_search import make_control,model,attack
ROOT=Path(__file__).resolve().parent

def crib_constraints(ct,pt,b):
    fixed={};used={}
    for ciphertext,plaintext in zip(ct,pt):
        slots=encrypt_physical(plaintext,range(83),1,b)
        for t,(slot,label) in enumerate(zip(slots,ciphertext)):
            if slot in fixed and fixed[slot]!=label:return None
            if label in used and used[label]!=slot:return None
            fixed[slot]=label;used[label]=slot
    return fixed

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--messages',type=int,default=3)
    ap.add_argument('--length',type=int,default=20);ap.add_argument('--steps',type=int,default=60)
    args=ap.parse_args();ct,pt,key,_=make_control(9)
    fixed=crib_constraints(ct[:args.messages],[m[:args.length] for m in pt[:args.messages]],9)
    assert fixed is not None and all(key[p]==c for p,c in fixed.items())
    # Exhaustive permutations on small decks independently verify the crib bijection criterion.
    import itertools
    checks=0
    for n in [4,5]:
        rng=np.random.default_rng(n)
        for _ in range(20):
            p=rng.integers(0,n,size=8).tolist();k=rng.permutation(n);c=encrypt_physical(p,k,1,1)
            if rng.random()<0.5:c[int(rng.integers(len(c)))]=int(rng.integers(n))
            slots=encrypt_physical(p,range(n),1,1);pairs=list(zip(slots,c))
            consistent=all((a==x)==(b==y) for a,b in pairs for x,y in pairs)
            brute=any(encrypt_physical(p,q,1,1)==c for q in itertools.permutations(range(n)))
            assert consistent==brute;checks+=1
    result=attack(ct,9,model(),steps=args.steps,restarts=1,staged=False,fixed=fixed)
    result.update(known_prefix_messages=args.messages,known_prefix_length=args.length,
                  fixed_key_positions=len(fixed),exhaustive_crib_controls=checks,
                  planted_exact_plaintext_recovered=result['plaintext_positions']==pt,
                  matching_plaintext_positions=sum(a==b for m,v in zip(pt,result['plaintext_positions']) for a,b in zip(m,v)),
                  control_positions=sum(map(len,pt)),
                  warning='Known-plaintext control only. The Noita plaintext and these crib assumptions are unknown.')
    name=f'crib_control_{args.messages}_{args.length}.json'
    (ROOT/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in result.items() if k not in ['initial_deck','plaintext_positions','candidate_text']})
