"""Key search using explicit, conditional repeated-plaintext constraints."""
from pathlib import Path
import numpy as np,json,argparse,time
from key_swap_attack import canonical_q,encrypt,trace,objective
from progressive_reduction import RUNS
ROOT=Path(__file__).resolve().parent

def edges(lengths):
    starts=np.cumsum([0]+lengths[:-1]);u=[];v=[]
    for i,s,j,t,n in RUNS:
        for k in range(1,n):u.append(starts[i]+s+k);v.append(starts[j]+t+k)
    return np.array(u),np.array(v)

def candidates(hist,traces,u,v):
    n=len(hist);aa,bb=np.triu_indices(n,1);H=len(aa)
    out=np.tile(hist,(H,1))
    base=[pos[c] for steps in traces for c,h,pos in steps]
    pt=np.tile(np.array(base,dtype=np.int32),(H,1));t=0
    for steps in traces:
        x=aa.copy();y=bb.copy();active=np.ones(H,dtype=bool)
        for c,h,pos in steps:
            ids=np.flatnonzero(active&((x==c)|(y==c)))
            if len(ids):
                other=np.where(x[ids]==c,y[ids],x[ids]);p=pos[other]
                out[ids,p]+=1;out[ids,pos[c]]-=1;pt[ids,t]=p
                killed=(x[ids]==h)|(y[ids]==h);active[ids[killed]]=False
                live=ids[~killed];first=x[live]==c;x[live[first]]=h;y[live[~first]]=h
            t+=1
    return aa,bb,out,np.count_nonzero(pt[:,u]!=pt[:,v],axis=1)

def attack(messages,q,A,restarts,moves):
    rng=np.random.default_rng(20260916);n=len(q);N=sum(map(len,messages));u,v=edges(list(map(len,messages)))
    best=None;start=time.time()
    for restart in range(restarts):
        key=rng.permutation(n)
        for step in range(moves):
            hist,traces,pt=trace(messages,q,key);flat=np.array(sum(pt,[]))
            violations=int(np.count_nonzero(flat[u]!=flat[v]))
            score=int(objective(hist,A))-20*N*violations
            if best is None or score>best['score']:
                best=dict(score=score,violations=violations,selection_support=int(np.count_nonzero(hist)),
                          outside_alphabet=int(np.partition(hist,n-A)[:n-A].sum()),
                          initial_deck=np.argsort(key).tolist(),plaintext=pt,restart=restart,step=step)
            if best['violations']==0 and best['outside_alphabet']==0:break
            aa,bb,hh,vv=candidates(hist,traces,u,v)
            scores=objective(hh,A)-20*N*vv
            temp=20000*(1-step/moves)**2
            k=int(np.argmax(scores+temp*rng.gumbel(size=len(scores))))
            a,b=aa[k],bb[k];key[a],key[b]=key[b],key[a]
        print('restart',restart,'best violations',best['violations'],'outside',best['outside_alphabet'],flush=True)
        if best['violations']==0 and best['outside_alphabet']==0:break
    assert all(encrypt(pt,q,best['initial_deck'])==ct for pt,ct in zip(best['plaintext'],messages))
    best.update(seconds=time.time()-start,assumed_plaintext_equalities=len(u),exact_replay=True,permutation=q.tolist())
    return best

def control(q,A):
    rng=np.random.default_rng(20260917);initial=rng.permutation(83)
    letters=rng.choice(np.arange(1,83),size=A,replace=False)
    pts=[rng.choice(letters,size=n).tolist() for n in [99,103,118,102,137,124,119,120,114]]
    phrase=rng.choice(letters,size=25).tolist()
    pts[1][35:60]=phrase;pts[1][65:90]=phrase
    pts[2][40:63]=phrase[:23];pts[2][75:98]=phrase[:23]
    pts[0][41:50]=phrase[6:15];pts[0][69:78]=phrase[6:15]
    phrase=rng.choice(letters,size=13).tolist()
    for mi,s in [(3,19),(4,25),(5,24)]:pts[mi][s:s+13]=phrase
    phrase=rng.choice(letters,size=11).tolist()
    for mi,s in [(6,52),(7,54),(8,53)]:pts[mi][s:s+11]=phrase
    phrase=rng.choice(letters,size=32).tolist();pts[6][69:101]=phrase;pts[7][72:104]=phrase
    u,v=edges(list(map(len,pts)));flat=np.array(sum(pts,[]));assert np.all(flat[u]==flat[v])
    return [encrypt(pt,q,initial) for pt in pts],pts

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--case',choices=['control','eyes'],default='control')
    ap.add_argument('--cycle',type=int,default=4);ap.add_argument('--restarts',type=int,default=3)
    ap.add_argument('--moves',type=int,default=400);args=ap.parse_args()
    q=canonical_q(83,args.cycle);pts=None
    if args.case=='control':messages,pts=control(q,32)
    else:messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    result=attack(messages,q,32,args.restarts,args.moves)
    if pts is not None:
        def canon(seq):
            ids={};return [ids.setdefault(x,len(ids)) for x in seq]
        result['planted_plaintext_pattern_recovered']=canon(sum(pts,[]))==canon(sum(result['plaintext'],[]))
    (ROOT/('isomorph_key_'+args.case+'_'+str(args.cycle)+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['initial_deck','plaintext','permutation']},indent=2))
