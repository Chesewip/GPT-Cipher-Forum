"""Exact lazy-key search for the specified clocked three-cycle/alphabet model.

No score authenticates a key. A completed assignment is replayed, but remains
only a model fit on real data. Search limits report inconclusive, never excluded.
"""
from pathlib import Path
import json,time,argparse,itertools
import numpy as np
from clocked_three_cycle_scan import encrypt_physical
from alphabet_reachability import predecessors,matching
from header_reachability import bits
ROOT=Path(__file__).resolve().parent

def solve(messages,n,alphabet,b,headers=False,max_nodes=10000,seconds=30,fixed=None):
    start=time.time();M=n-1;full=(1<<n)-1;pre=predecessors(n,alphabet,b)
    layers=[];reach=1
    for _ in range(max(map(len,messages))):
        reach2=0
        for z in bits(reach):reach2|=pre[z]
        reach=reach2
        if reach==full:break
        layers.append(list(bits(reach)))
    positions={};allowed_set=set(alphabet)
    for t in range(max(map(len,messages))+1):
        positions[t]=[[0 if p==0 else 1+(p-1-t*b)%M for p in layer] for layer in layers]
    nodes=0;furthest=0;answer=None;limit_hit=False
    mapping=[-1]*n
    if fixed:
        for c,p in fixed.items():mapping[c]=p
    state=[(0,list(range(n)),list(range(n))) for _ in messages]
    def visit(mapping,state):
        nonlocal nodes,furthest,answer,limit_hit
        nodes+=1
        if nodes>max_nodes or time.time()-start>seconds:limit_hit=True;return False
        state=[(t,d.copy(),pos.copy()) for t,d,pos in state]
        while True:
            # Advance all outputs whose initial card identity is known.
            for i,(t,deck,pos) in enumerate(state):
                m=messages[i]
                while t<len(m) and mapping[m[t]]>=0:
                    slot=mapping[m[t]];p=pos[slot];physical=0 if p==0 else 1+(p-1+t*b)%M
                    if not (headers and t==0) and physical not in allowed_set:return False
                    r=0 if p==0 else 1+p%M;old=deck[0];tail=deck[r]
                    deck[0]=slot;deck[p]=tail;deck[r]=old
                    pos[slot]=0;pos[tail]=p;pos[old]=r;t+=1
                state[i]=(t,deck,pos)
            completed=sum(s[0] for s in state);furthest=max(furthest,completed)
            if all(t==len(m) for (t,_,_),m in zip(state,messages)):
                answer=mapping.copy();return True
            used=sum(1<<v for v in mapping if v>=0);free=full&~used
            dom=[1<<v if v>=0 else free for v in mapping];frontiers=set()
            for (t,deck,pos),m in zip(state,messages):
                if t==len(m):continue
                frontiers.add(m[t])
                if headers and t==0:continue
                for k,ps in enumerate(positions[t][:len(m)-t]):
                    mask=0
                    for p in ps:mask|=1<<deck[p]
                    c=m[t+k];dom[c]&=mask
                    if not dom[c]:return False
            singleton=[c for c,d in enumerate(dom) if mapping[c]<0 and d&(d-1)==0]
            if singleton:
                mapping=mapping.copy()
                for c in singleton:
                    p=dom[c].bit_length()-1
                    if used>>p&1:return False
                    used|=1<<p;mapping[c]=p
                continue
            if matching(dom,n)['status']=='excluded':return False
            c=min(frontiers,key=lambda c:dom[c].bit_count())
            for p in bits(dom[c]):
                child=mapping.copy();child[c]=p
                if visit(child,state):return True
                if limit_hit:return False
            return False
    found=visit(mapping,state)
    out={'status':'model_fit' if found else 'inconclusive' if limit_hit else 'excluded',
         'nodes':nodes,'node_limit':max_nodes,'time_limit':seconds,'seconds':time.time()-start,
         'furthest_outputs_reached':furthest,'total_outputs':sum(map(len,messages)),
         'shuffle_offset':b,'alphabet_positions':alphabet,'arbitrary_first_headers':headers}
    if found:
        available=iter(p for p in range(n) if p not in answer)
        answer=[next(available) if p<0 else p for p in answer]
        key=[-1]*n
        for c,p in enumerate(answer):key[p]=c
        # Independent physical decoder is deliberately simple.
        pts=[]
        for m in messages:
            deck=key.copy();pt=[]
            for c in m:
                p=deck.index(c);pt.append(p);r=0 if p==0 else 1+p%M
                old,selected,tail=deck[0],deck[p],deck[r]
                deck[0]=selected;deck[p]=tail;deck[r]=old
                if b:deck=[deck[0]]+deck[-b:]+deck[1:-b]
            assert all(p in allowed_set for p in pt[int(headers):])
            assert encrypt_physical(pt,key,1,b)==m;pts.append(pt)
        out.update(initial_deck=key,plaintext_positions=pts,exact_replay=True)
    return out

def controls():
    rng=np.random.default_rng(20261014);checks=0
    for n in [4,5]:
        for _ in range(20):
            alphabet=list(range(1,3));b=int(rng.integers(n-1));headers=bool(rng.integers(2))
            key=rng.permutation(n);pt=[rng.choice(alphabet,8).tolist() for _ in range(2)]
            if headers:
                for m in pt:m[0]=int(rng.integers(n))
            ct=[encrypt_physical(p,key,1,b) for p in pt]
            if rng.random()<0.5:ct[0][int(rng.integers(8))]=int(rng.integers(n))
            possible=False
            for k in itertools.permutations(range(n)):
                ok=True
                for m in ct:
                    deck=list(k)
                    for t,c in enumerate(m):
                        p=deck.index(c)
                        if not(headers and t==0) and p not in alphabet:ok=False;break
                        r=0 if p==0 else 1+p%(n-1);old,sel,tail=deck[0],deck[p],deck[r]
                        deck[0]=sel;deck[p]=tail;deck[r]=old
                        if b:deck=[deck[0]]+deck[-b:]+deck[1:-b]
                    if not ok:break
                if ok:possible=True;break
            result=solve(ct,n,alphabet,b,headers,max_nodes=100000,seconds=10)
            assert result['status']!='inconclusive'
            assert (result['status']=='model_fit')==possible;checks+=1
    return checks

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');ap.add_argument('--headers',action='store_true')
    ap.add_argument('--shuffle',type=int,default=9);ap.add_argument('--alphabet',type=int,default=27)
    ap.add_argument('--seconds',type=int,default=40);ap.add_argument('--nodes',type=int,default=100000)
    args=ap.parse_args();checked=controls()
    if args.control:
        from english_clocked_search import make_control
        messages,pt,key,_=make_control(args.shuffle)
    else:messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    out=solve(messages,83,list(range(1,args.alphabet+1)),args.shuffle,args.headers,args.nodes,args.seconds)
    out['small_exhaustive_controls']=checked
    if args.control:out['exact_planted_plaintext_recovered']=out.get('plaintext_positions')==pt
    filename='lazy_key_'+('control' if args.control else 'eyes')+'_'+str(args.shuffle)+('_headers' if args.headers else '')+'.json'
    (ROOT/filename).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in out.items() if k not in ['initial_deck','plaintext_positions','alphabet_positions']})
