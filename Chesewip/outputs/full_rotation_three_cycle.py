"""A variable three-cycle followed by rotation of the entire83-card deck.

Anchor a=-b mod83. f(p) advances d steps in the ring of82 positions
excluding a. Cycle old p->a, old f(p)->p, old a->f(p), then rotate by b.
An identity selection p=a is allowed. Selection p=0 causes a double.
"""
from pathlib import Path
import json,time,argparse
import numpy as np
ROOT=Path(__file__).resolve().parent

def encrypt(pt,key,d,b):
    n=len(key);a=(-b)%n;deck=list(key);out=[]
    for p in pt:
        r=a if p==a else (a+1+(((p-a-1)%n+d)%(n-1)))%n
        old,chosen,tail=deck[a],deck[p],deck[r]
        deck[a]=chosen;deck[p]=tail;deck[r]=old
        if b:deck=deck[-b:]+deck[:-b]
        out.append(int(deck[0]))
    return out

def histograms(messages,keys,ds,bs):
    B,n=keys.shape;ids=np.arange(B);hist=np.zeros((B,n),dtype=np.int32)
    for m in messages:
        deck=keys.copy();pos=np.argsort(keys,axis=1)
        for t,c in enumerate(m):
            a=(-(t+1)*bs)%n;p=pos[:,c].copy()
            r=np.where(p==a,a,(a+1+(((p-a-1)%n+ds)%(n-1)))%n)
            physical=(p+t*bs)%n;hist[ids,physical]+=1
            old=deck[ids,a].copy();tail=deck[ids,r].copy()
            deck[ids,a]=c;deck[ids,p]=tail;deck[ids,r]=old
            pos[:,c]=a;pos[ids,tail]=p;pos[ids,old]=r
    return hist

def verify():
    rng=np.random.default_rng(20261005);checks=0
    for n in [11,31,83]:
        for trial in range(20):
            key=rng.permutation(n);d=int(rng.integers(1,n-1));b=int(rng.integers(n))
            pt=[rng.integers(n,size=70).tolist() for _ in range(3)]
            ct=[encrypt(p,key,d,b) for p in pt]
            h=histograms(ct,np.array([key]),np.array([d]),np.array([b]))[0]
            assert np.array_equal(h,np.bincount(sum(pt,[]),minlength=n)),(n,trial)
            checks+=1
    return checks

def scan(messages,key):
    n=len(key);ds=np.repeat(np.arange(1,n-1),n);bs=np.tile(np.arange(n),n-2)
    h=histograms(messages,np.tile(key,(len(ds),1)),ds,bs);support=np.count_nonzero(h,axis=1)
    minimum=int(min(support));best=np.flatnonzero(support==minimum)
    return {'configurations':len(ds),'minimum_alphabet':minimum,
            'minimizers':[{'neighbor_offset':int(ds[k]),'whole_deck_rotation':int(bs[k])} for k in best]},support

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');args=ap.parse_args()
    start=time.time();controls=verify()
    if args.control:
        rng=np.random.default_rng(20261006);key=np.arange(83);alphabet=rng.choice(np.arange(1,83),27,replace=False)
        pt=[rng.choice(alphabet,120).tolist() for _ in range(9)];ct=[encrypt(p,key,19,17) for p in pt]
        r,support=scan(ct,key);assert support[(19-1)*83+17]==27
        out={'physical_vs_rotating_frame_controls':controls,'planted_alphabet_recovered':True,
             'planted_neighbor_offset':19,'planted_whole_deck_rotation':17,**r};name='full_rotation_three_cycle_control.json'
    else:
        raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());results=[]
        for skip in [False,True]:
            for reverse in [False,True]:
                ct=[m[1:] if skip else m[:] for m in raw]
                if reverse:ct=[m[::-1] for m in ct]
                for descending in [False,True]:
                    key=np.arange(83)
                    if descending:key=key[::-1]
                    r,_=scan(ct,key);r.update(first_omitted=skip,reversed=reverse,descending_initial_deck=descending)
                    results.append(r);print({k:v for k,v in r.items() if k!='minimizers'},flush=True)
        out={'physical_vs_rotating_frame_controls':controls,'results':results,
             'total_configurations':sum(r['configurations'] for r in results),
             'scope':'Only the listed initial decks and reading conventions; arbitrary keys remain unexcluded.'}
        name='full_rotation_three_cycle_scan.json'
    out['seconds']=time.time()-start
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Completed',name,out['seconds'])
