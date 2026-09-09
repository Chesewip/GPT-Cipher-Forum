#!/usr/bin/env python3
import numpy as np, time
MOD=83
LENS=[98,102,117,101,136,123,118,119,113]
COUNTS=np.array([6496,4854,4360,4017,3572,2939,2909,2579,2573,2558,2183,2161,2072,2042,1891,1874,1736,1645,1632,1618,1608,1584,1533,1512,1438,1425,1361,1342,1342,1332,1272,1253,1208,1204,1128,1063,1037,995,964,955,936,933,922,893,876,874,852,848,834,829,765,765,752,709,707,706,675,669,663,662,648,642,639,639,637,635,626,619,604,596,592,589,580,578,576,572,570,568,560,554,543,539,530],float)
PROB=COUNTS/COUNTS.sum(); OBS=2.259686

def gen_plain(T,n,target,rng):
    x=np.empty((T,n),dtype=np.int16)
    x[:,:min(8,n)]=rng.choice(MOD,size=(T,min(8,n)),p=PROB)
    pmatch=target/MOD
    for i in range(8,n):
        old=x[:,i-8]
        m=rng.random(T)<pmatch
        vals=rng.choice(MOD,size=T,p=PROB).astype(np.int16)
        bad=(~m)&(vals==old)
        while bad.any():
            vals[bad]=rng.choice(MOD,size=int(bad.sum()),p=PROB)
            bad=(~m)&(vals==old)
        x[:,i]=np.where(m,old,vals)
    return x

def run(target,T,seed):
    rng=np.random.default_rng(seed)
    plain_hits=np.zeros(T,int); raw_hits=np.zeros(T,int); fix_hits=np.zeros(T,int)
    repairs=np.zeros(T,int); raw_adj=np.zeros(T,int); fix_adj=np.zeros(T,int); pairs=0
    for n in LENS:
        p=gen_plain(T,n,target,rng)
        neg=rng.choice(MOD,size=(T,4),p=PROB).astype(np.int16)
        h=np.concatenate([neg,p],axis=1)
        raw=np.empty((T,n),np.int16); fix=np.empty((T,n),np.int16)
        prev=np.full(T,-1,np.int16)
        for i in range(n):
            q=((h[:,i].astype(np.int32)+h[:,i+4].astype(np.int32))%MOD).astype(np.int16)
            raw[:,i]=q
            cond=(i>0)&(q==prev)
            y=((q.astype(np.int32)+cond.astype(np.int32))%MOD).astype(np.int16)
            fix[:,i]=y
            if i>0:
                repairs += cond
                raw_adj += (raw[:,i]==raw[:,i-1])
                fix_adj += (fix[:,i]==fix[:,i-1])
            prev=y
        if n>8:
            plain_hits += (p[:,8:]==p[:,:-8]).sum(axis=1)
            raw_hits += (raw[:,8:]==raw[:,4:-4]).sum(axis=1)
            fix_hits += (fix[:,8:]==fix[:,4:-4]).sum(axis=1)
            pairs += n-8
    plain=MOD*plain_hits/pairs; rawr=MOD*raw_hits/pairs; fixr=MOD*fix_hits/pairs
    rows=np.column_stack([plain,rawr,fixr,repairs,raw_adj,fix_adj])
    return rows

def report(target,T,seed):
    rows=run(target,T,seed); names=['plain8','raw_g4','fix_g4','repairs','raw_adj','fix_adj']
    print(f'target {target:.6f} trials {T}')
    for j+n in enumerate(names):
        a=rows[:,j]
        print(f'  {n:8s} mean {a.mean():.6f} sd {a.std(ddof=1):.6f} p05 {np.quantile(a,.05):.6f} p50 {np.quantile(a,.5):.6f} p95 {np.quantile(a,.95):.6f}')
    h=(rows[:,2]>=OBS)
    print(f'  P(fix_g4 >= observed {OBS:.6f}) = {h.mean():.8f} ({h.sum()}/{T})')
    d=rows[:,2]-rows[:,1]
    print(f'  repair delta fix-raw mean {d.mean():.6f} sd {d.std(ddof=1):.6f}; P(delta>0)={(d>0).mean():.6f}')
    print(f'  corr(repairs, delta) {np.corrcoef(rows[:,3],d)[0,1]:.6f}')
    return rows

if __name__=='__main__':
    t=time.time()
    for k,x in enumerate([1.22,1.55,2.259686]):
        report(x,20000,7900+k); print()
    print('seconds',round(time.time()-t,3))
