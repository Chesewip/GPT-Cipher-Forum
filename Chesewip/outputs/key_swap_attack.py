"""Exact transposition deltas for a keyed deck and fixed common permutation.

One initial key transposition remains a transposition under ciphertext-driven
decryption, until it disappears. This makes all key-swap scores inexpensive.
Heuristic optimization does not certify impossibility.
"""
from pathlib import Path
import numpy as np
import random,json,argparse,time
ROOT=Path(__file__).resolve().parent

def canonical_q(n,top_cycle):
    q=np.arange(n,dtype=np.int32)
    for cycle in [list(range(top_cycle)),list(range(top_cycle,n))]:
        for i,c in enumerate(cycle):q[c]=cycle[(i+1)%len(cycle)]
    return q

def partition_q(parts):
    n=sum(parts);q=np.arange(n,dtype=np.int32);start=0
    for length in parts:
        assert length>0
        for i in range(length):q[start+i]=start+(i+1)%length
        start+=length
    return q

def encrypt(pt,q,initial):
    n=len(q);anchor=int(np.where(q==0)[0][0]);deck=list(initial);out=[]
    for p in pt:
        deck[anchor],deck[p]=deck[p],deck[anchor]
        new=[None]*n
        for i,j in enumerate(q):new[j]=deck[i]
        deck=new;out.append(int(deck[0]))
    return out

def trace(messages,q,pos0):
    n=len(q);anchor=int(np.where(q==0)[0][0]);hist=np.zeros(n,dtype=np.int32);traces=[];plain=[]
    for m in messages:
        pos=np.array(pos0,dtype=np.int32);steps=[];pt=[]
        for c in m:
            h=int(np.where(pos==anchor)[0][0]);p=int(pos[c])
            steps.append((c,h,pos.copy()));pt.append(p);hist[p]+=1
            pos[h]=p;pos[c]=anchor;pos=q[pos]
        traces.append(steps);plain.append(pt)
    return hist,traces,plain

def all_swap_histograms(hist,traces):
    n=len(hist);aa,bb=np.triu_indices(n,1);H=len(aa)
    out=np.tile(hist,(H,1))
    for steps in traces:
        x=aa.copy();y=bb.copy();active=np.ones(H,dtype=bool)
        for c,h,pos in steps:
            ids=np.flatnonzero(active&((x==c)|(y==c)))
            if not len(ids):continue
            other=np.where(x[ids]==c,y[ids],x[ids])
            out[ids,pos[other]]+=1;out[ids,pos[c]]-=1
            killed=(x[ids]==h)|(y[ids]==h)
            active[ids[killed]]=False
            live=ids[~killed];first=x[live]==c
            x[live[first]]=h;y[live[~first]]=h
    return aa,bb,out

def objective(hist,alphabet):
    n=hist.shape[-1];N=np.sum(hist,axis=-1)
    tail=np.partition(hist,n-alphabet,axis=-1)[...,:n-alphabet].sum(axis=-1)
    return -N*tail+np.sum(hist.astype(np.int64)**2,axis=-1)

def attack(messages,q,alphabet,restarts=5,moves=100,seed=20260912,escape=False,anneal=False):
    rng=np.random.default_rng(seed);n=len(q);best=None;start=time.time()
    for restart in range(restarts):
        if escape and best is not None and restart%4:
            pos0=np.argsort(best['initial_deck'])
            for _ in range(3+restart%11):
                a,b=rng.choice(n,size=2,replace=False)
                pos0[a],pos0[b]=pos0[b],pos0[a]
        else:
            pos0=rng.permutation(n)
        for step in range(moves):
            hist,traces,plain=trace(messages,q,pos0);score=int(objective(hist,alphabet))
            if best is None or score>best['score']:
                best=dict(score=score,initial_deck=np.argsort(pos0).tolist(),
                          plaintext=plain,histogram=hist.tolist(),support=int(np.count_nonzero(hist)),
                          outside_alphabet=int(np.partition(hist,n-alphabet)[:n-alphabet].sum()),
                          restart=restart,step=step)
            if best['outside_alphabet']==0:break
            aa,bb,candidates=all_swap_histograms(hist,traces)
            scores=objective(candidates,alphabet)
            if anneal:
                temperature=3500*(1-step/moves)**2
                k=int(np.argmax(scores+temperature*rng.gumbel(size=len(scores))))
            else:
                k=int(np.argmax(scores))
                if scores[k]<=score:break
            a,b=aa[k],bb[k];pos0[a],pos0[b]=pos0[b],pos0[a]
        print('restart',restart,'best outside',best['outside_alphabet'],'support',best['support'],'step',step,flush=True)
        if best['outside_alphabet']==0:break
    assert all(encrypt(pt,q,best['initial_deck'])==ct for pt,ct in zip(best['plaintext'],messages))
    best.update(seconds=time.time()-start,exact_replay=True,permutation=q.tolist(),alphabet_bound=alphabet,
                escape_restarts=escape,annealed_neighbors=anneal,
                requested_restarts=restarts,maximum_moves_per_restart=moves)
    return best

def verify_deltas():
    rng=np.random.default_rng(20260913);checks=0
    for L in [1,2,4,8,11]:
        n=11;q=canonical_q(n,L);initial=rng.permutation(n)
        pts=[rng.integers(1,n,size=40).tolist() for _ in range(3)]
        ct=[encrypt(pt,q,initial) for pt in pts]
        key=rng.permutation(n);hist,traces,_=trace(ct,q,key)
        aa,bb,found=all_swap_histograms(hist,traces)
        for k,(a,b) in enumerate(zip(aa,bb)):
            trial=key.copy();trial[a],trial[b]=trial[b],trial[a]
            actual,_,_=trace(ct,q,trial)
            assert np.array_equal(found[k],actual),(L,a,b)
            checks+=1
    return checks

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--case',choices=['control','eyes','verify'],default='control')
    ap.add_argument('--cycle',type=int,default=4);ap.add_argument('--alphabet',type=int,default=27)
    ap.add_argument('--restarts',type=int,default=5);ap.add_argument('--moves',type=int,default=100)
    ap.add_argument('--escape',action='store_true');ap.add_argument('--anneal',action='store_true');args=ap.parse_args()
    if args.case=='verify':print('Exact delta checks passed:',verify_deltas());raise SystemExit
    q=canonical_q(83,args.cycle);pts=None
    if args.case=='control':
        rng=np.random.default_rng(20260914);initial=rng.permutation(83)
        letters=rng.choice(np.arange(1,83),size=args.alphabet,replace=False)
        pts=[rng.choice(letters,size=120).tolist() for _ in range(9)]
        messages=[encrypt(pt,q,initial) for pt in pts]
    else:messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    result=attack(messages,q,args.alphabet,args.restarts,args.moves,escape=args.escape,anneal=args.anneal)
    if pts is not None:
        def canon(seq):
            ids={};return [ids.setdefault(x,len(ids)) for x in seq]
        result['planted_plaintext_pattern_recovered']=canon(sum(pts,[]))==canon(sum(result['plaintext'],[]))
    path=ROOT/('key_swap_'+args.case+'_'+str(args.cycle)+'_'+str(args.alphabet)+('_escape' if args.escape else '')+('_anneal' if args.anneal else '')+'.json')
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['initial_deck','plaintext','histogram','permutation']},indent=2))
