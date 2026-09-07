from pathlib import Path
import sys,json,random
from entry_change_timing import intervals,solve
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent
rng=random.Random(20261031);checks=0
for common in [False,True]:
    for _ in range(60):
        n=4;N=7;a=[rng.randrange(n) for t in range(N)];b=[rng.randrange(n) for t in range(N)]
        for row in range(n):
            ivs=intervals(a,b,n,row,common)
            for mask in range(1<<N):
                cuts={t for t in range(N) if mask>>t&1};possible={row} if common else set(range(n));okay=True
                for t,(ca,cb) in enumerate(zip(a,b)):
                    if t in cuts:possible=set(range(n))
                    allowed={cb} if ca==row else set(range(n))-{cb};possible&=allowed
                    if not possible:okay=False;break
                covered=all(any(lo<=t<=hi for t in cuts) for lo,hi in ivs)
                assert okay==covered;checks+=1
plants=[]
for n in [11,83]:
    for _ in range(6):
        key=rng.sample(list(range(n)),n);a=[rng.randrange(1,n) for t in range(35)];b=a.copy()
        for t in rng.sample(range(35),7):b[t]=rng.randrange(1,n)
        ca=encrypt_physical(a,key,1,3);cb=encrypt_physical(b,key,1,3);k=sum(x!=y for x,y in zip(a,b))
        r=solve(ca,cb,5,k,n,timeout=10000);assert r['status']=='sat';plants.append({'n':n,'true_differences':k,'status':r['status']})
real=json.loads((ROOT/'entry_change_timing_99_18.json').read_text());raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());ys=set(real['possible_change_positions'])
assert len(ys)<=18
for row in range(83):
    cuts=set(real['row_changes'][str(row)]);assert cuts<=ys;possible={row}
    for t,(ca,cb) in enumerate(zip(raw[0],raw[1])):
        if t in cuts:possible=set(range(83))
        possible&=({cb} if ca==row else set(range(83))-{cb})
        assert possible
for t in range(99):assert sum(t in r for r in real['row_changes'].values())<=5
out={'exhaustive_row_cutset_checks':checks,'generated_cipher_plants':plants,'real_18_change_timing_witness_verified':True,'warning':'Only independent mapping rows are modeled; bijectivity and a common cipher rule are not established.'}
(ROOT/'checked_entry_change_timing.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(out)
