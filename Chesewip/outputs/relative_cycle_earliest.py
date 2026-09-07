import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from relative_cycle_templates import solve
from compact_template_witnesses import partial_map
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());a,b=raw[:2];out=[]
for N in [34,35,36,37]:
    rows=[]
    for first in range(1,N):
        for second in range(first+1,N):
            cuts=[0,first,second,N];okay=True
            for lo,hi in zip(cuts,cuts[1:]):
                f=partial_map(a[lo:hi],b[lo:hi])
                if f is None or (hi<N and f.get(a[hi])==b[hi]):okay=False;break
            if okay:
                r=solve(a[:N],b[:N],cuts,timeout=3000);rows.append(r)
    counts={s:sum(r['status']==s for r in rows) for s in ['sat','unsat','unknown']}
    print(N,len(rows),counts,flush=True);out.append({'length':N,'results':rows,'counts':counts})
(ROOT/'relative_cycle_earliest.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
