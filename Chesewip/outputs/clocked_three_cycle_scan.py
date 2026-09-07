"""Three variable-position cycle followed by a common bottom rotation.

Bottom positions are a ring of length82; f(p)=p+d and Q(p)=p+b on
that ring. In a rotating frame, deck evolution is independent of b;
the selected index is read with clock offset t*b. These scans only
test the explicitly recorded starting decks, not arbitrary keys.
"""
from pathlib import Path
import json,time,argparse,math
import numpy as np
ROOT=Path(__file__).resolve().parent

def encrypt_physical(pt,key,d,b):
    deck=list(key);out=[];M=len(deck)-1
    for p in pt:
        r=0 if p==0 else 1+(p-1+d)%M
        a,c,e=deck[0],deck[p],deck[r]
        deck[0]=c;deck[p]=e;deck[r]=a;out.append(int(c))
        if b:deck=[deck[0]]+deck[-b:]+deck[1:-b]
    return out

def histograms(messages,keys,ds,bs):
    B,n=keys.shape;M=n-1;ids=np.arange(B);hist=np.zeros((B,n),dtype=np.int32)
    for m in messages:
        deck=keys.copy();pos=np.argsort(keys,axis=1)
        for t,c in enumerate(m):
            p=pos[:,c].copy();r=np.where(p==0,0,1+(p-1+ds)%M)
            physical=np.where(p==0,0,1+(p-1+t*bs)%M)
            hist[ids,physical]+=1
            oldtop=deck[:,0].copy();tail=deck[ids,r].copy()
            deck[:,0]=c;deck[ids,p]=tail;deck[ids,r]=oldtop
            pos[:,c]=0;pos[ids,tail]=p;pos[ids,oldtop]=r
    return hist

def scan(messages,key):
    n=len(key);ds=np.repeat(np.arange(1,n-1),n-1);bs=np.tile(np.arange(n-1),n-2)
    keys=np.tile(key,(len(ds),1));h=histograms(messages,keys,ds,bs);support=np.count_nonzero(h,axis=1)
    low=int(min(support));best=np.flatnonzero(support==low)
    return {'configurations':len(ds),'minimum_alphabet':low,
            'minimizers':[{'neighbor_offset':int(ds[k]),'shuffle_offset':int(bs[k])} for k in best]},support

def verify():
    rng=np.random.default_rng(20260927);checks=0
    for n in [11,31,83]:
        for trial in range(20):
            key=rng.permutation(n);d=int(rng.integers(1,n-1));b=int(rng.integers(0,n-1))
            pt=[rng.integers(0,n,size=70).tolist() for _ in range(3)]
            ct=[encrypt_physical(p,key,d,b) for p in pt]
            h=histograms(ct,np.array([key]),np.array([d]),np.array([b]))[0]
            assert np.array_equal(h,np.bincount(sum(pt,[]),minlength=n));checks+=1
    return checks

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');args=ap.parse_args()
    start=time.time();controls=verify()
    if args.control:
        rng=np.random.default_rng(20260928);key=np.arange(83);alphabet=rng.choice(np.arange(1,83),27,replace=False)
        pts=[rng.choice(alphabet,120).tolist() for _ in range(9)]
        messages=[encrypt_physical(p,key,17,9) for p in pts];r,support=scan(messages,key)
        assert support[(17-1)*82+9]==27
        result={'physical_vs_rotating_frame_controls':controls,'planted_parameters':{'neighbor_offset':17,'shuffle_offset':9},
                'planted_alphabet_recovered':True,'distinct_ciphertext_labels':len(set(sum(messages,[]))),**r}
        name='clocked_three_cycle_control.json'
    else:
        raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());results=[]
        for skip in [False,True]:
            for reverse in [False,True]:
                messages=[(m[1:] if skip else m) for m in raw]
                if reverse:messages=[m[::-1] for m in messages]
                for descending in [False,True]:
                    key=np.arange(83)
                    if descending:key=key[::-1]
                    r,_=scan(messages,key);r.update(first_omitted=skip,reversed=reverse,descending_initial_deck=descending)
                    results.append(r);print({k:v for k,v in r.items() if k!='minimizers'},flush=True)
        result={'physical_vs_rotating_frame_controls':controls,'results':results,
                'total_configurations':sum(r['configurations'] for r in results)}
        name='clocked_three_cycle_scan_results.json'
    result['seconds']=time.time()-start
    (ROOT/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Completed',name,'seconds',result['seconds'])
