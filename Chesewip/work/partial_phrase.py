from pathlib import Path
import sys,json,itertools
sys.path.insert(0,str(Path('outputs').resolve()))
from progressive_reduction import deswap
msgs=list(json.load(open('outputs/ciphertext.json')).values());first={m[0] for m in msgs}
results=[]
for top in range(83):
    if top in first:continue
    b=[deswap(m,top,83) for m in msgs]
    table=list(zip(b[6][52:63],b[7][54:65],b[8][53:64]))
    best=[]
    for size in range(11,-1,-1):
        for subset in itertools.combinations(range(11),size):
            f={top:top};inv={top:top};valid=True
            for k in subset:
                e,w,z=table[k]
                for x,y in [(w,z),(z,e)]:
                    if (x in f and f[x]!=y) or (y in inv and inv[y]!=x):valid=False;break
                    f[x]=y;inv[y]=x
                if not valid:break
            if valid:best.append(list(subset))
        if best:break
    results.append(dict(top=top,maximum_common_positions=size,examples=best[:3]))
Path('outputs/partial_phrase_results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Maximum shared positions across all possible top labels:',max(r['maximum_common_positions'] for r in results),'of 11')
print(results[:2])
