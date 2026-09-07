"""Heuristic unknown-key search for the surviving unit-neighbor model.

Candidates are scored by their decoded selection alphabet. The 'window'
objective assumes contiguous selection positions1..A. The 'support'
objective permits any A positions. Neither failed search is an exclusion.
"""
from pathlib import Path
import json,time,argparse
import numpy as np
from clocked_three_cycle_scan import histograms,encrypt_physical
from key_swap_attack import objective
ROOT=Path(__file__).resolve().parent

def decode(messages,key,b):
    n=len(key);M=n-1;out=[]
    for m in messages:
        deck=list(key);pt=[]
        for t,c in enumerate(m):
            p=deck.index(c);r=0 if p==0 else 1+p%M
            pt.append(0 if p==0 else 1+(p-1+t*b)%M)
            old,tail=deck[0],deck[r];deck[0]=c;deck[p]=tail;deck[r]=old
        out.append(pt)
    return out

def score(hist,A,mode):
    if mode=='support':return objective(hist,A)
    total=hist.sum(axis=-1);bad=total-hist[:,1:A+1].sum(axis=-1)
    return -total*bad+(hist.astype(np.int64)**2).sum(axis=-1)

def attack(messages,n,b,A,mode='window',restarts=2,steps=120,anneal=False,start_key=None):
    rng=np.random.default_rng(20261007);aa,bb=np.triu_indices(n,1);B=len(aa);best=None;start=time.time()
    for restart in range(restarts):
        key=np.array(start_key) if start_key is not None and restart==0 else rng.permutation(n)
        for step in range(steps):
            keys=np.tile(key,(B+1,1));ids=np.arange(B)
            keys[ids,aa]=key[bb];keys[ids,bb]=key[aa]
            # Adjacent block exchanges preserve most circular adjacencies.
            block=[]
            for _ in range(400):
                a,c,e=sorted(rng.choice(np.arange(1,n+1),3,replace=False).tolist())
                block.append(np.concatenate([key[:a],key[c:e],key[a:c],key[e:]]))
            keys=np.concatenate([np.array(block),keys]);Btotal=len(keys)
            hist=histograms(messages,keys,np.ones(Btotal,dtype=np.int32),np.full(Btotal,b,dtype=np.int32))
            scores=score(hist,A,mode);k=int(np.argmax(scores))
            if best is None or int(scores[k])>best['score']:
                best={'score':int(scores[k]),'initial_deck':keys[k].tolist(),
                      'outside_window':int(hist[k].sum()-hist[k,1:A+1].sum()),
                      'outside_best_alphabet':int(np.partition(hist[k],n-A)[:n-A].sum()),
                      'support':int(np.count_nonzero(hist[k])),'restart':restart,'step':step}
            error=best['outside_window'] if mode=='window' else best['outside_best_alphabet']
            if error==0:break
            if anneal:
                temp=3500*(1-step/steps)**2;k=int(np.argmax(scores+temp*rng.gumbel(size=Btotal)))
            elif scores[k]<=scores[-1]:break
            key=keys[k]
            if step%20==0:print('b',b,'restart',restart,'step',step,'best error',error,flush=True)
        print('restart',restart,'best',best['outside_window'],best['outside_best_alphabet'],flush=True)
        if error==0:break
    pt=decode(messages,best['initial_deck'],b)
    assert all(encrypt_physical(p,best['initial_deck'],1,b)==c for p,c in zip(pt,messages))
    best.update(plaintext=pt,neighbor_offset=1,shuffle_offset=b,alphabet_bound=A,objective=mode,
                annealed_neighbors=anneal,seconds=time.time()-start,restarts_requested=restarts,
                steps_requested=steps,exact_replay=True)
    return best

def signature(seq):
    labels={};return [labels.setdefault(c,len(labels)) for c in seq]

def control(A,b,near=False):
    rng=np.random.default_rng(20261008);key=rng.permutation(83)
    weights=np.arange(1,A+1,dtype=float)**(-0.9);weights/=weights.sum()
    pt=[rng.choice(np.arange(1,A+1),size=120,p=weights).tolist() for _ in range(9)]
    ct=[encrypt_physical(p,key,1,b) for p in pt]
    damaged=key.copy()
    if near:
        for _ in range(5):
            a,c=rng.choice(83,2,replace=False);damaged[a],damaged[c]=damaged[c],damaged[a]
    return ct,pt,key,damaged if near else None

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');ap.add_argument('--near',action='store_true')
    ap.add_argument('--shuffle',type=int,default=1);ap.add_argument('--alphabet',type=int,default=27)
    ap.add_argument('--mode',choices=['window','support'],default='window');ap.add_argument('--anneal',action='store_true')
    ap.add_argument('--resume')
    ap.add_argument('--restarts',type=int,default=2);ap.add_argument('--steps',type=int,default=120);args=ap.parse_args()
    if args.control:messages,pt,key,initial=control(args.alphabet,args.shuffle,args.near)
    else:messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());initial=None
    if args.resume:initial=json.loads((ROOT/args.resume).read_text())['initial_deck']
    result=attack(messages,83,args.shuffle,args.alphabet,args.mode,args.restarts,args.steps,args.anneal,initial)
    if args.control:
        result['planted_plaintext_pattern_recovered']=signature(sum(result['plaintext'],[]))==signature(sum(pt,[]))
        result['planted_exact_positions_recovered']=result['plaintext']==pt
        result['started_five_key_swaps_from_truth']=args.near
    if args.resume:result['resumed_from']=args.resume
    name='clocked_key_'+('control' if args.control else 'eyes')+'_'+str(args.shuffle)+'_'+args.mode+('_near' if args.near else '')+('_anneal' if args.anneal else '')+('_resumed' if args.resume else '')+'.json'
    (ROOT/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in result.items() if k not in ['plaintext','initial_deck']})
