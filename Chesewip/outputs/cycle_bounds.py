"""Exact alphabet lower bound for an unknown single-cycle bottom shuffle."""
from pathlib import Path
import json
from progressive_reduction import deswap
ROOT=Path(__file__).resolve().parent

def lower_bound(messages,n,top):
    L=n-1;mask=(1<<L)-1;times={i:0 for i in range(n) if i!=top}
    for m in messages:
        for t,b in enumerate(deswap(m,top,n)):
            if b==top:return dict(top=top,invalid_top=True)
            times[b] |= 1<<(t%L)
    labels=list(times);sizes={b:times[b].bit_count() for b in labels}
    rotations={b:[((times[b]<<s)|(times[b]>>(L-s)))&mask for s in range(1,L)] for b in labels}
    bound=max(sizes.values());witness=None
    for k,a in enumerate(labels):
        for b in labels[k+1:]:
            if sizes[a]+sizes[b]<=bound:continue
            overlap=max((times[a]&r).bit_count() for r in rotations[b])
            value=sizes[a]+sizes[b]-overlap
            if value>bound:
                bound=value;witness=dict(labels=[a,b],time_support_sizes=[sizes[a],sizes[b]],maximum_overlap=overlap)
    return dict(top=top,alphabet_lower_bound=bound,witness=witness)

if __name__=='__main__':
    msgs=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    results=[lower_bound(msgs,83,t) for t in range(83)]
    (ROOT/'cycle_alphabet_bounds.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    good=[r for r in results if not r.get('invalid_top')]
    print('Lower bounds range:',min(r['alphabet_lower_bound'] for r in good),max(r['alphabet_lower_bound'] for r in good))
    print('Lowest:',sorted(good,key=lambda r:r['alphabet_lower_bound'])[:3])
