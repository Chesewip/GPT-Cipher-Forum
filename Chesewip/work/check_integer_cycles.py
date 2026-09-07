from pathlib import Path
import sys,json,random
sys.path.insert(0,'outputs')
from relative_cycle_integer import solve
rng=random.Random(20261101);results=[]
for n in [7,83]:
    for kind in [3,5]:
        a=[];b=[];r=list(range(n));cuts=[0,4,8,12]
        for lo,hi in zip(cuts,cuts[1:]):
            previous=r;pts=rng.sample(range(n),kind);d=list(range(n))
            for x,y in zip(pts,pts[1:]+pts[:1]):d[x]=y
            r=[r[d[x]] for x in range(n)]
            for t in range(lo,hi):
                x=rng.choice([v for v in range(n) if t!=lo or previous[v]!=r[v]])
                a.append(x);b.append(r[x])
        result=solve(a,b,cuts,n,True,10000);assert result['status']=='sat',result
        results.append({'n':n,'planted_cycle_length':kind,'seconds':result['seconds']})
raw=list(json.loads(Path('outputs/ciphertext.json').read_text()).values())
retry=solve(raw[0][:36],raw[1][:36],[0,25,28,36],allow_three=True,timeout=20000)
Path('outputs/checked_relative_cycle_integer.json').write_text(json.dumps({'planted_controls':results,'previously_timed_out_case':retry},indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(results);print(retry)
