import json,sys
from pathlib import Path
sys.path.insert(0,'outputs')
from compact_template_witnesses import partial_map
raw=list(json.loads(Path('outputs/ciphertext.json').read_text()).values());a,b=[x[:50] for x in raw[:2]]
for c1 in [23,24,25]:
    for c2 in [28,29,30,31,32,33]:
        cuts=[0,c1,c2,50];maps=[dict(zip(a[l:r],b[l:r])) for l,r in zip(cuts,cuts[1:])];prev={i:i for i in range(83)};counts=[]
        for f in maps:
            forced={x for x in f.keys()&prev.keys() if f[x]!=prev[x]};ip={v:k for k,v in prev.items()};ic={v:k for k,v in f.items()}
            for v in ip.keys()&ic.keys():
                if ip[v]!=ic[v]:forced.update([ip[v],ic[v]])
            counts.append((len(forced),sorted(forced)));prev=f
        print(cuts,counts)
