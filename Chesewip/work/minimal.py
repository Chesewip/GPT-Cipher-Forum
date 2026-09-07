from pathlib import Path
import sys,json,itertools
sys.path.insert(0,str(Path('outputs').resolve()))
from progressive_reduction import graph_certificate,RUNS
msgs=list(json.load(open('outputs/ciphertext.json')).values())
eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in RUNS]
validtops=[t for t in range(83) if t not in [m[0] for m in msgs]]
def survivors(indices):
    return [top for top in validtops if not graph_certificate(msgs,83,top,[eq[i] for i in indices])['contradiction']]
for i in range(len(eq)):
    ss=survivors([i]);print(i,len(ss),ss[:10])
for k in (2,3):
    found=[]
    for ids in itertools.combinations(range(len(eq)),k):
        if not survivors(ids):found.append(ids)
    print('minimal group size',k,found,flush=True)
    if found:break
