"""Independent bit-set DP verifier for the real-data shuffle-weight bounds."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent

def completion_weight(f,n):
    f=f.copy()
    for x in list(f):
        if x in f.values():continue
        end=x
        while end in f:end=f[end]
        f[end]=x
    for x in range(n):f.setdefault(x,x)
    seen=set();odd=0
    for x in range(n):
        if x in seen:continue
        size=0;v=x
        while v not in seen:seen.add(v);size+=1;v=f[v]
        odd+=size%2
    return (n-odd)//2

def check(a,b,budget):
    n=min(len(a),len(b));reach=[1]+[0]*n;mask=(1<<(n+1))-1
    for end in range(1,n+1):
        for start in range(end):
            pairs=list(zip(a[start:end],b[start:end]));f=dict(pairs)
            if any(f[x]!=y for x,y in pairs) or len(set(f.values()))!=len(f):continue
            w=completion_weight(f,83);minimum=(w+budget-1)//budget
            eligible=(reach[start]<<1)&mask&~((1<<minimum)-1)
            reach[end]|=eligible
    smallest=(reach[-1]&-reach[-1]).bit_length()-1
    return smallest,reach

ms=list(json.loads((ROOT/'ciphertext.json').read_text()).values());report=json.loads((ROOT/'shuffle_weight_bounds.json').read_text());verified=[]
for case in report['east1_west1']:
    length=case['prefix_length']
    for result in case['bounds']:
        budget=result['relative_shuffle_weight_budget'];actual,reach=check(ms[0][:length],ms[1][:length],budget)
        assert actual==result['minimum_plaintext_differences']
        verified.append({'length':length,'budget':budget,'bound':actual,'reachable_count_bitsets':reach})
(ROOT/'checked_weight_dp.json').write_text(json.dumps({'independent_cases':verified,'all_passed':True},indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Independently verified',len(verified),'real-data bounds')
