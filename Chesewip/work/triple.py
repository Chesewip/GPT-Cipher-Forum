from pathlib import Path
import sys,json,itertools
sys.path.insert(0,str(Path('outputs').resolve()))
from progressive_reduction import deswap
m=list(json.load(open('outputs/ciphertext.json')).values());L=82;mask=(1<<L)-1
res=[]
for top in range(83):
    if top in [x[0] for x in m]:continue
    rows={b:0 for b in range(83) if b!=top}
    for msg in m:
        for t,b in enumerate(deswap(msg,top,83)):rows[b]|=1<<(t%L)
    choices=sorted(rows,key=lambda b:rows[b].bit_count(),reverse=True)[:6]
    best=0;witness=None
    for aa,bb,cc in itertools.combinations(choices,3):
        a,b,c=rows[aa],rows[bb],rows[cc]
        rb=[((b<<d)|(b>>(L-d)))&mask for d in range(1,L)]
        rc=[((c<<d)|(c>>(L-d)))&mask for d in range(1,L)]
        value=min((a|v|w).bit_count() for j,v in enumerate(rb) for k,w in enumerate(rc) if j!=k)
        if value>best:best=value;witness=[aa,bb,cc]
    res.append(dict(top=top,lower_bound=best,three_labels=witness))
Path('outputs/cycle_triple_bounds.json').write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Triple bound range:',min(r['lower_bound'] for r in res),max(r['lower_bound'] for r in res))
print(sorted(res,key=lambda r:r['lower_bound'])[:4])
