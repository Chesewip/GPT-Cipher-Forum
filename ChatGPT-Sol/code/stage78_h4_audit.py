#!/usr/bin/env python3
"""Stage 78: audit the lag-4 H4 collision-fix inverse and optimizer calibration.

Model under audit (mod 83):
    q_i = p_i + p_{i-4}
    q'_i = q_i + 1 if q_i == q'_{i-1}, otherwise q_i
    c_i = PI(q'_i)

This script does NOT claim a plaintext. It:
  1) proves/validates that the +1 collision repair is non-injective;
  2) gives the exact set-valued inverse once PI^-1 is known;
  3) verifies that the existing raw-H4 algebra exactly inverts raw synthetic H4;
  4) tests whether a stronger, labeled Finnish-IID likelihood optimizer can recover
     a synthetic raw-H4 key from random starts.

Input ciphertext is only used for message lengths here; synthetic calibration uses
those exact body lengths. The frequency table is the same top-83 Finnish syllable
count vector used in stages 73-76 of the supplied handoff.
"""
from __future__ import annotations
import argparse, json, math, time
from pathlib import Path
import numpy as np

MOD=83
COUNTS=np.array([
6496,4854,4360,4017,3572,2939,2909,2579,2573,2558,2183,2161,2072,2042,
1891,1874,1736,1645,1632,1618,1608,1584,1533,1512,1438,1425,1361,1342,
1342,1332,1272,1253,1208,1204,1128,1063,1037,995,964,955,936,933,922,
893,876,874,852,848,834,829,765,765,752,709,707,706,675,669,663,662,
648,642,639,639,637,635,626,619,604,596,592,589,580,578,576,572,570,
568,560,554,543,539,530],dtype=float)
PROB=COUNTS/COUNTS.sum(); LOGP=np.log(PROB)


def load_lengths(path: Path):
    data=json.loads(path.read_text(encoding='utf-8'))
    names=list(data)
    return names,[len(data[n]['body']) for n in names]


def repair_map(q: int, prev: int) -> int:
    return (q+1)%MOD if q==prev else q


def inverse_repair_candidates(y: int, prev_y: int|None):
    if prev_y is None:
        return (y,)
    if y==prev_y:
        return ()  # collision-fix output can never equal previous output
    if y==(prev_y+1)%MOD:
        return (y,prev_y)  # un-repaired q=y OR repaired q=prev_y
    return (y,)


def synth(lengths, seed=781, fix=False):
    rng=np.random.default_rng(seed)
    pi=rng.permutation(MOD)
    inv=np.empty(MOD,dtype=np.int16)
    for q,c in enumerate(pi): inv[c]=q
    neg=rng.choice(MOD,size=4,p=PROB).astype(np.int16)
    seqs=[]; plains=[]; raws=[]; repairs=[]
    for n in lengths:
        p=rng.choice(MOD,size=n,p=PROB).astype(np.int16)
        hist=np.concatenate([neg,p])
        c=np.empty(n,dtype=np.int16); qr=np.empty(n,dtype=np.int16)
        fixed=np.zeros(n,dtype=bool); prev=None
        for i in range(n):
            q=(int(hist[i])+int(hist[i+4]))%MOD
            qr[i]=q
            y=q
            if fix and prev is not None and q==prev:
                y=(q+1)%MOD; fixed[i]=True
            c[i]=pi[y]; prev=y
        seqs.append(c); plains.append(p); raws.append(qr); repairs.append(fixed)
    return seqs,inv,neg,np.concatenate(plains),raws,repairs


def build_AB(seqs):
    """Raw H4 linear form p = A*s + B*seed mod83, s=PI^-1."""
    rows=[]; bs=[]
    for c in seqs:
        for i in range(len(c)):
            r=i%4; t=i//4
            a=np.zeros(MOD,dtype=np.int16)
            for k in range(t+1):
                j=r+4*k
                a[int(c[j])] += 1 if ((t-k)%2==0) else -1
            b=np.zeros(4,dtype=np.int16)
            b[r]=-1 if t%2==0 else 1
            rows.append(a); bs.append(b)
    return np.array(rows,dtype=np.int16),np.array(bs,dtype=np.int16)


def calc_p(A,B,s,seeds):
    return ((A.astype(np.int32)@s.astype(np.int32)+B.astype(np.int32)@seeds.astype(np.int32))%MOD).astype(np.int16)


def score(p): return float(LOGP[p].mean())


def anneal_fast(seqs,iters,seed,T0=.05,T1=1e-6):
    A,B=build_AB(seqs); Ai=A.astype(np.int32); Bi=B.astype(np.int32)
    rng=np.random.default_rng(seed)
    s=rng.permutation(MOD).astype(np.int16); seeds=rng.integers(MOD,size=4,dtype=np.int16)
    p=calc_p(A,B,s,seeds); sc=score(p); best=(sc,s.copy(),seeds.copy(),p.copy())
    for t in range(iters):
        T=T0*(T1/T0)**(t/max(1,iters-1))
        if rng.random()<.10:
            r=int(rng.integers(4)); old=int(seeds[r]); new=int(rng.integers(MOD)); d=new-old
            p2=(p.astype(np.int32)+Bi[:,r]*d)%MOD; q=score(p2)
            if q>=sc or rng.random()<math.exp((q-sc)/T):
                seeds[r]=new; p=p2.astype(np.int16); sc=q
        else:
            a,b=map(int,rng.choice(MOD,2,replace=False)); xa,xb=int(s[a]),int(s[b])
            dvec=Ai[:,a]*(xb-xa)+Ai[:,b]*(xa-xb)
            p2=(p.astype(np.int32)+dvec)%MOD; q=score(p2)
            if q>=sc or rng.random()<math.exp((q-sc)/T):
                s[a],s[b]=s[b],s[a]; p=p2.astype(np.int16); sc=q
        if sc>best[0]: best=(sc,s.copy(),seeds.copy(),p.copy())
    return best


def local_descent(seqs,seed,max_epochs=30,start_s=None,start_seeds=None):
    A,B=build_AB(seqs); Ai=A.astype(np.int32); Bi=B.astype(np.int32)
    rng=np.random.default_rng(seed)
    s=(rng.permutation(MOD) if start_s is None else np.array(start_s,copy=True)).astype(np.int16)
    seeds=(rng.integers(MOD,size=4) if start_seeds is None else np.array(start_seeds,copy=True)).astype(np.int16)
    p=calc_p(A,B,s,seeds); sc=score(p)
    for ep in range(max_epochs):
        improved=False
        for r in rng.permutation(4):
            cur=int(seeds[r]); vals=np.arange(MOD,dtype=np.int32); ds=vals-cur
            P=(p[None,:].astype(np.int32)+ds[:,None]*Bi[:,r][None,:])%MOD
            scores=LOGP[P].mean(axis=1); v=int(np.argmax(scores)); q=float(scores[v])
            if q>sc+1e-12:
                p=P[v].astype(np.int16); seeds[r]=v; sc=q; improved=True
        for a in rng.permutation(MOD):
            xa=int(s[a]); bs=np.array([b for b in range(MOD) if b!=a],dtype=np.int32); xbs=s[bs].astype(np.int32)
            D=(xbs-xa)[:,None]*Ai[:,a][None,:]+(xa-xbs)[:,None]*Ai[:,bs].T
            P=(p[None,:].astype(np.int32)+D)%MOD
            scores=LOGP[P].mean(axis=1); k=int(np.argmax(scores)); q=float(scores[k])
            if q>sc+1e-12:
                b=int(bs[k]); p=P[k].astype(np.int16); s[a],s[b]=s[b],s[a]; sc=q; improved=True
        if not improved: break
    return sc,s,seeds,p,ep+1


def best_plain_given_true_map_fix(c, inv, seed4):
    """Known PI^-1 and seed: maximize IID log-likelihood over exact repair branches."""
    y=inv[c].astype(int)
    cand=[]
    for i,v in enumerate(y): cand.append(inverse_repair_candidates(int(v),None if i==0 else int(y[i-1])))
    if any(len(x)==0 for x in cand): return None
    p=np.empty(len(c),dtype=np.int16); chosen=np.empty(len(c),dtype=np.int16)
    for r in range(4):
        idx=list(range(r,len(c),4))
        # state is previous plaintext value; initialize with fixed negative-history seed
        states={int(seed4[r]):(0.0,[])}
        for i in idx:
            nxt={}
            for prev,(sc,path) in states.items():
                for q in cand[i]:
                    cur=(int(q)-prev)%MOD; val=sc+float(LOGP[cur])
                    old=nxt.get(cur)
                    if old is None or val>old[0]: nxt[cur]=(val,path+[(cur,int(q))])
            states=nxt
        _,path=max(states.values(),key=lambda z:z[0])
        for i,(cur,q) in zip(idx,path): p[i]=cur; chosen[i]=q
    return p,chosen,cand


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--ciphertext',default=str(Path(__file__).with_name('ciphertext_stage78.json')))
    ap.add_argument('--anneal',type=int,default=0,help='run one random-start anneal at this iteration budget')
    ap.add_argument('--local-restarts',type=int,default=0)
    args=ap.parse_args()
    names,lengths=load_lengths(Path(args.ciphertext))
    print('Stage78 H4 mechanism/optimizer audit')
    print('body lengths',dict(zip(names,lengths)),'total',sum(lengths))

    # Repair-map theorem/check.
    prev=17; outs=[repair_map(q,prev) for q in range(MOD)]
    print('\nCOLLISION FIX MAP')
    print('for fixed previous internal output r=17: distinct outputs',len(set(outs)))
    print('missing output',sorted(set(range(MOD))-set(outs)))
    dup=[v for v in set(outs) if outs.count(v)>1]
    print('duplicated output',dup,'preimages',[q for q in range(MOD) if repair_map(q,prev)==dup[0]])
    print('therefore the +1 repair is non-injective; no ordinary permutation can equal this map')

    # Fix positive control and exact set-valued inversion.
    fseqs,finv,fneg,fplain,fraws,frepairs=synth(lengths,seed=782,fix=True)
    amb=actual=raw_wrong=coverage=0; total=0
    best_parts=[]; branch_correct=0; branch_total=0
    off=0
    for c,raw,rep,n in zip(fseqs,fraws,frepairs,lengths):
        y=finv[c].astype(int)
        for i in range(n):
            cc=inverse_repair_candidates(int(y[i]),None if i==0 else int(y[i-1]))
            total+=1; amb+=len(cc)==2; actual+=bool(rep[i]); raw_wrong+=int(int(y[i])!=int(raw[i])); coverage+=int(int(raw[i]) in cc)
        z=best_plain_given_true_map_fix(c,finv,fneg)
        if z:
            pp,qq,cands=z; truth=fplain[off:off+n]
            best_parts.append(pp)
            for i in range(n):
                if len(cands[i])==2:
                    branch_total+=1; branch_correct+=int(int(qq[i])==int(raw[i]))
            off+=n
    pbest=np.concatenate(best_parts)
    print('\nEXACT FIX INVERSE POSITIVE CONTROL seed=782')
    print('repairs',actual,'ambiguous inverse positions',amb,'raw-inverse mismatches',raw_wrong,'candidate coverage',f'{coverage}/{total}')
    print('with true PI^-1 and true four seeds, IID-likelihood branch optimization:')
    print('plaintext accuracy',round(float(np.mean(pbest==fplain)),6),'ambiguous-branch accuracy',f'{branch_correct}/{branch_total}')

    # Raw positive control verifies algebra exactly.
    seqs,inv,neg,truep,_,_=synth(lengths,seed=781,fix=False)
    A,B=build_AB(seqs); exact=calc_p(A,B,inv,neg)
    print('\nRAW H4 POSITIVE CONTROL seed=781')
    print('exact algebra plaintext recovery',round(float(np.mean(exact==truep)),6))
    print('true-key avg log-likelihood',round(score(truep),9),'true seeds',neg.tolist())

    if args.anneal:
        st=time.time(); b=anneal_fast(seqs,args.anneal,seed=1000+args.anneal)
        print('\nRANDOM-START ANNEAL')
        print('iterations',args.anneal,'seconds',round(time.time()-st,3))
        print('best log-likelihood',round(b[0],9),'key accuracy',round(float(np.mean(b[1]==inv)),6),'plaintext accuracy',round(float(np.mean(b[3]==truep)),6),'seeds',b[2].tolist())

    if args.local_restarts:
        st=time.time(); rows=[]
        for r in range(args.local_restarts):
            b=local_descent(seqs,500+r); rows.append((b[0],float(np.mean(b[1]==inv)),float(np.mean(b[3]==truep)),b[4]))
        rows.sort(reverse=True)
        print('\nRANDOM-START COORDINATE DESCENT')
        print('restarts',args.local_restarts,'seconds',round(time.time()-st,3))
        print('best',tuple(round(x,6) if isinstance(x,float) else x for x in rows[0]))
        print('median score',round(float(np.median([x[0] for x in rows])),9),'max key accuracy',round(max(x[1] for x in rows),6))

    # Basin probe: deliberately start close to truth.
    print('\nNEAR-TRUE BASIN PROBE')
    rng=np.random.default_rng(991)
    for swaps in [1,2,5,10]:
        ss=inv.copy();
        for _ in range(swaps):
            a,b=map(int,rng.choice(MOD,2,replace=False)); ss[a],ss[b]=ss[b],ss[a]
        b=local_descent(seqs,900+swaps,start_s=ss,start_seeds=neg)
        print('start swaps',swaps,'end score',round(b[0],9),'key accuracy',round(float(np.mean(b[1]==inv)),6),'plaintext accuracy',round(float(np.mean(b[3]==truep)),6))

if __name__=='__main__': main()
