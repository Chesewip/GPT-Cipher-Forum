"""Heuristic keyed attack on (top, selected p, f(p)) three-cycles.

f rotates the 82 bottom positions by an offset. Up to arbitrary initial key
and plaintext relabeling, offsets 1,2,41 cover all 81 nonzero offsets.
Output old card p; move old f(p) to p and old top to f(p).
No additional common shuffle. A top selection is allowed as the identity.
"""
from pathlib import Path
import numpy as np
import json,time,argparse
from key_swap_attack import objective
ROOT=Path(__file__).resolve().parent

def encrypt(pt,initial,offset):
    deck=list(initial);out=[];n=len(deck)
    for p in pt:
        r=0 if p==0 else 1+(p-1+offset)%(n-1)
        a,b,c=deck[0],deck[p],deck[r]
        deck[0]=b;deck[p]=c;deck[r]=a;out.append(int(b))
    return out

def decrypt(messages,initial,offset):
    out=[];n=len(initial)
    for m in messages:
        deck=list(initial);pt=[]
        for c in m:
            p=deck.index(c);r=0 if p==0 else 1+(p-1+offset)%(n-1)
            a,b,d=deck[0],deck[p],deck[r]
            deck[0]=b;deck[p]=d;deck[r]=a;pt.append(p)
        out.append(pt)
    return out

def batch_hist(messages,initials,offset):
    B,n=initials.shape;ids=np.arange(B);hist=np.zeros((B,n),dtype=np.int32)
    for m in messages:
        deck=initials.copy();pos=np.argsort(initials,axis=1)
        for c in m:
            p=pos[:,c].copy();r=np.where(p==0,0,1+(p-1+offset)%(n-1))
            oldtop=deck[:,0].copy();tail=deck[ids,r].copy()
            hist[ids,p]+=1
            deck[:,0]=c;deck[ids,p]=tail;deck[ids,r]=oldtop
            pos[:,c]=0;pos[ids,tail]=p;pos[ids,oldtop]=r
    return hist

def verify():
    rng=np.random.default_rng(20260923);checks=0
    for n in [11,31,83]:
        for offset in [1,2,(n-1)//2]:
            initial=rng.permutation(n);pt=[rng.integers(1,n,size=80).tolist() for _ in range(3)]
            ct=[encrypt(p,initial,offset) for p in pt]
            assert decrypt(ct,initial,offset)==pt
            keys=np.array([rng.permutation(n) for _ in range(20)])
            hist=batch_hist(ct,keys,offset)
            for key,h in zip(keys,hist):
                pp=decrypt(ct,key,offset)
                assert np.array_equal(h,np.bincount(sum(pp,[]),minlength=n));checks+=1
    return checks

def attack(messages,n,offset,A,restarts=3,steps=80,seed=20260924,anneal=False):
    rng=np.random.default_rng(seed);aa,bb=np.triu_indices(n,1);B=len(aa)
    best=None;start=time.time()
    for restart in range(restarts):
        key=rng.permutation(n)
        for step in range(steps):
            keys=np.tile(key,(B+1,1));ids=np.arange(B)
            keys[ids,aa]=key[bb];keys[ids,bb]=key[aa]
            hist=batch_hist(messages,keys,offset);scores=objective(hist,A)
            k=int(np.argmax(scores))
            if best is None or int(scores[k])>best['score']:
                best={'score':int(scores[k]),'initial_deck':keys[k].tolist(),
                      'support':int(np.count_nonzero(hist[k])),
                      'outside_alphabet':int(np.partition(hist[k],n-A)[:n-A].sum()),
                      'restart':restart,'step':step}
            if best['outside_alphabet']==0:break
            if anneal:
                temperature=3500*(1-step/steps)**2
                k=int(np.argmax(scores+temperature*rng.gumbel(size=len(scores))))
            elif scores[k]<=scores[-1]:break
            key=keys[k]
            if step%10==0:print('offset',offset,'restart',restart,'step',step,'outside',best['outside_alphabet'],flush=True)
        print('offset',offset,'restart',restart,'best outside',best['outside_alphabet'],flush=True)
        if best['outside_alphabet']==0:break
    pt=decrypt(messages,best['initial_deck'],offset)
    assert all(encrypt(p,best['initial_deck'],offset)==c for p,c in zip(pt,messages))
    best.update(plaintext=pt,offset=offset,alphabet_bound=A,seconds=time.time()-start,
                requested_restarts=restarts,maximum_steps=steps,annealed_neighbors=anneal,exact_replay=True)
    return best

def signature(seq):
    labels={};return [labels.setdefault(x,len(labels)) for x in seq]

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--offset',type=int,default=1)
    ap.add_argument('--alphabet',type=int,default=27);ap.add_argument('--restarts',type=int,default=3)
    ap.add_argument('--steps',type=int,default=80);ap.add_argument('--control',action='store_true')
    ap.add_argument('--anneal',action='store_true')
    ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    if args.verify:print('Batch decoder comparisons passed:',verify());raise SystemExit
    if args.control:
        rng=np.random.default_rng(20260925);key=rng.permutation(83);alphabet=rng.choice(np.arange(1,83),args.alphabet,replace=False)
        pt=[rng.choice(alphabet,120).tolist() for _ in range(9)]
        messages=[encrypt(p,key,args.offset) for p in pt]
    else:messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    result=attack(messages,83,args.offset,args.alphabet,args.restarts,args.steps,anneal=args.anneal)
    if args.control:result['planted_plaintext_pattern_recovered']=signature(sum(result['plaintext'],[]))==signature(sum(pt,[]))
    name='three_cycle_'+('control' if args.control else 'eyes')+'_'+str(args.offset)+'_'+str(args.alphabet)+('_anneal' if args.anneal else '')+'.json'
    (ROOT/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in result.items() if k not in ['plaintext','initial_deck']})
