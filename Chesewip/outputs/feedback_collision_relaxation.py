"""Preserve the weaker pairwise relaxation tried before exact set unions."""
from pathlib import Path
import json
import numpy as np
ROOT=Path(__file__).resolve().parent
messages=list(json.loads((ROOT/'ciphertext.json').read_text(encoding='utf-8')).values())
cases=[]
for modulus in [83,125,128]:
    counts=np.zeros((83,modulus),dtype=np.int64)
    for row in messages:
        for x,y in zip(row[1:-1],row[2:]):counts[x,y]+=1
    same=sum(int(v@(v-1)//2) for v in counts)
    upper=same
    shift_indices=(np.arange(modulus)[None,:]-np.arange(modulus)[:,None])%modulus
    for i in range(83):
        for j in range(i):upper+=int((counts[j][shift_indices]@counts[i]).max())
    n=int(counts.sum())
    def minimum_pairs(k):
        q,r=divmod(n,k);return r*q*(q+1)//2+(k-r)*q*(q-1)//2
    bound=next(k for k in range(1,modulus+1) if minimum_pairs(k)<=upper)
    cases.append(dict(modulus=modulus,observations=n,collision_upper_bound=upper,support_lower_bound=bound))
assert [c['collision_upper_bound'] for c in cases]==[26703,25203,25108]
assert [c['support_lower_bound'] for c in cases]==[20,21,21]
out=dict(status='Weak relaxation; superseded by exact five-context union bounds.',cases=cases,
         explanation='Each pair of predecessor groups chooses its own best relative shift. These shifts need not be globally consistent. Modulus 128 here is cyclic addition, not XOR.')
(ROOT/'feedback_collision_relaxation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(json.dumps(out,indent=2))
