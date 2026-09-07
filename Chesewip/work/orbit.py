import json,collections
m=list(json.load(open('outputs/ciphertext.json')).values());gaps=[];dists=[]
for row in m:
    prev={};ds=[]
    for t,c in enumerate(row):
        d=t-prev[c] if c in prev else None;ds.append(d)
        if d is not None:gaps.append(d)
        prev[c]=t
    dists.append(ds)
freq=collections.Counter(gaps)
print('Distinct return gaps <=83:',len([d for d in freq if d<=83]))
print('Bound by top cycle length:',[(L,len([d for d in freq if d<=L])) for L in [2,3,4,5,10,20,27,30,32,40,41,52,60,70,82,83]])
runs=[(1,34,1,64,26),(2,39,2,74,24),(0,40,0,68,10),(1,40,2,45,11),(1,40,2,80,11),(3,18,4,24,14),(3,18,5,23,14),(6,51,7,53,12),(6,51,8,52,12),(6,68,7,71,33)]
conflicts=[]
for ri,(mi,s,mj,t,n) in enumerate(runs):
    for k in range(1,n):
        a=dists[mi][s+k];b=dists[mj][t+k]
        if a is not None and b is not None and a!=b:conflicts.append(dict(run=ri,positions=[s+k,t+k],messages=[mi,mj],gaps=[a,b],excluded_cycle_lengths_at_least=max(a,b)))
print('Tightest conditional orbit bounds:',sorted(conflicts,key=lambda r:r['excluded_cycle_lengths_at_least'])[:10])
