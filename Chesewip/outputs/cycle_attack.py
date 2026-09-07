"""Recover an unknown 82-cycle by histogram alignment after deswapping.
Heuristic search only: a negative result is not an exclusion.
"""
from pathlib import Path
import numpy as np
import random,json,time,argparse
from progressive_reduction import deswap
ROOT=Path(__file__).resolve().parent

def prepare(messages,n,top):
    labels=[i for i in range(n) if i!=top];lookup={c:i for i,c in enumerate(labels)}
    L=n-1;rows=np.zeros((L,L),dtype=np.int32)
    for m in messages:
        for t,b in enumerate(deswap(m,top,n)):
            if b==top:raise ValueError('forbidden top output')
            rows[lookup[b],t%L]+=1
    shifted=np.empty((L,L,L),dtype=np.int32)
    for i in range(L):
        for s in range(L):shifted[i,s]=np.roll(rows[i],s)
    return labels,rows,shifted

def attack(messages,n,top,restarts=10,steps=30000,seed=20260907):
    rng=random.Random(seed);labels,rows,shifted=prepare(messages,n,top)
    L=n-1;best=None;start=time.time()
    for restart in range(restarts):
        z=list(range(L));rng.shuffle(z)
        hist=shifted[np.arange(L),z].sum(axis=0)
        score=int(hist@hist)
        for k in range(steps):
            a,b=rng.sample(range(L),2);za,zb=z[a],z[b]
            change=shifted[a,zb]+shifted[b,za]-shifted[a,za]-shifted[b,zb]
            ds=int(2*(hist@change)+change@change)
            # Temperature in score units, cool and finish with greedy search.
            temp=150*(1-k/steps)**3+0.1
            if ds>=0 or rng.random()<np.exp(max(-700,ds/temp)):
                z[a],z[b]=zb,za;hist+=change;score+=ds
            if best is None or score>best['score']:
                best=dict(score=score,positions=z[:],histogram=hist.tolist(),
                          support=int(np.count_nonzero(hist)),restart=restart,step=k)
        print('restart',restart,'best support',best['support'],'score',best['score'],flush=True)
    z=best['positions'];q=list(range(n))
    inv=[None]*L
    for c,pos in zip(labels,z):inv[pos]=c
    for c,pos in zip(labels,z):q[c]=inv[(pos+1)%L]
    plain=[]
    for m in messages:
        plain.append([inv[(z[labels.index(b)]+t)%L] for t,b in enumerate(deswap(m,top,n))])
    # Independent direct deck simulation validates every candidate, even bad ones.
    from reduced_smt import encrypt
    assert all(encrypt(pt,q,top)==ct for pt,ct in zip(plain,messages))
    best.update(top=top,permutation=q,plaintext=plain,seconds=time.time()-start,exact_replay=True)
    return best

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--case',choices=['control','eyes'],default='control')
    ap.add_argument('--top',type=int,default=30);ap.add_argument('--restarts',type=int,default=6)
    ap.add_argument('--steps',type=int,default=30000);args=ap.parse_args()
    if args.case=='eyes':
        messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());top=args.top;pts=None
    else:
        from reduced_smt import encrypt
        rng=random.Random(20260909);top=30;labels=[i for i in range(83) if i!=top]
        cycle=labels[:];rng.shuffle(cycle);q=list(range(83))
        for i,c in enumerate(cycle):q[c]=cycle[(i+1)%82]
        letters=rng.sample(labels,27)
        pts=[[rng.choice(letters) for _ in range(120)] for _ in range(9)]
        messages=[encrypt(pt,q,top) for pt in pts]
    result=attack(messages,83,top,args.restarts,args.steps)
    if pts is not None:
        def canon(seq):
            ids={};return [ids.setdefault(x,len(ids)) for x in seq]
        result['planted_plaintext_pattern_recovered']=canon(sum(pts,[]))==canon(sum(result['plaintext'],[]))
    (ROOT/('cycle_attack_'+args.case+'_'+str(top)+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['positions','histogram','permutation','plaintext']},indent=2))
