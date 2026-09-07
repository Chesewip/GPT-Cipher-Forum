"""Exact lazy-key search with bidirectional shared-plaintext propagation.

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

def solve(messages,n,alphabet,b,headers=False,max_nodes=10000,seconds=30,fixed=None,equalities=()):
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
    parent={(i,t):(i,t) for i,m in enumerate(messages) for t in range(len(m))}
    def root(x):
        if parent[x]!=x:parent[x]=root(parent[x])
        return parent[x]
    for i,s,j,t,length in equalities:
        for k in range(length):parent[root((i,s+k))]=root((j,t+k))
    from collections import Counter
    counts=Counter(root(x) for x in parent)
    classes={x:root(x) if counts[root(x)]>1 else None for x in parent}
    nodes=0;furthest=0;answer=None;limit_hit=False
    mapping=[-1]*n
    if fixed:
        for c,p in fixed.items():mapping[c]=p
    state=[(0,list(range(n)),list(range(n))) for _ in messages]
    def visit(mapping,state,plain_values):
        nonlocal nodes,furthest,answer,limit_hit
        nodes+=1
        if nodes>max_nodes or time.time()-start>seconds:limit_hit=True;return False
        state=[(t,d.copy(),pos.copy()) for t,d,pos in state]
        mapping=mapping.copy();plain_values=plain_values.copy()
        while True:
            before=(sum(v>=0 for v in mapping),len(plain_values),sum(x[0] for x in state))
            # Advance all outputs whose initial card identity is known.
            for i,(t,deck,pos) in enumerate(state):
                m=messages[i]
                while t<len(m):
                    cls=classes[(i,t)];c=m[t]
                    if mapping[c]<0 and cls in plain_values:
                        physical=plain_values[cls]
                        p=0 if physical==0 else 1+(physical-1-t*b)%M
                        slot=deck[p]
                        if slot in mapping:return False
                        mapping[c]=slot
                    if mapping[c]<0:break
                    slot=mapping[c];p=pos[slot];physical=0 if p==0 else 1+(p-1+t*b)%M
                    if cls is not None:
                        if cls in plain_values and plain_values[cls]!=physical:return False
                        plain_values[cls]=physical
                    if not (headers and t==0) and physical not in allowed_set:return False
                    r=0 if p==0 else 1+p%M;old=deck[0];tail=deck[r]
                    deck[0]=slot;deck[p]=tail;deck[r]=old
                    pos[slot]=0;pos[tail]=p;pos[old]=r;t+=1
                state[i]=(t,deck,pos)
            completed=sum(s[0] for s in state);furthest=max(furthest,completed)
            if all(t==len(m) for (t,_,_),m in zip(state,messages)):
                answer=mapping.copy();return True
            after=(sum(v>=0 for v in mapping),len(plain_values),completed)
            if after!=before:continue
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
            # Intersect possible selections at frontiers sharing a plaintext class.
            common={};front=[]
            for i,((t,deck,pos),m) in enumerate(zip(state,messages)):
                if t==len(m):continue
                cls=classes[(i,t)]
                if cls is None:continue
                c=m[t];choices={0 if pos[x]==0 else 1+(pos[x]-1+t*b)%M for x in bits(dom[c])}
                common[cls]=choices if cls not in common else common[cls]&choices
                if not common[cls]:return False
                front.append((cls,c,t,deck))
            for cls,c,t,deck in front:
                allowed=0
                for physical in common[cls]:
                    p=0 if physical==0 else 1+(physical-1-t*b)%M
                    allowed|=1<<deck[p]
                dom[c]&=allowed
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
                if visit(child,state,plain_values):return True
                if limit_hit:return False
            return False
    found=visit(mapping,state,{})
    out={'status':'model_fit' if found else 'inconclusive' if limit_hit else 'excluded',
         'nodes':nodes,'node_limit':max_nodes,'time_limit':seconds,'seconds':time.time()-start,
         'furthest_outputs_reached':furthest,'total_outputs':sum(map(len,messages)),
         'assumed_plaintext_equalities':equalities,'fixed_initial_positions':fixed,
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
        for i,s,j,t,length in equalities:
            assert pts[i][s:s+length]==pts[j][t:t+length]
        out.update(initial_deck=key,plaintext_positions=pts,exact_replay=True)
    return out

def decode_physical(messages,key,b):
    n=len(key);M=n-1;pts=[]
    for m in messages:
        deck=list(key);pt=[]
        for c in m:
            p=deck.index(c);pt.append(p);r=0 if p==0 else 1+p%M
            deck[0],deck[p],deck[r]=deck[p],deck[r],deck[0]
            if b:deck=[deck[0]]+deck[-b:]+deck[1:-b]
        pts.append(pt)
    return pts

def verify():
    rng=np.random.default_rng(20261016);checks=[]
    for n in [4,5]:
        for trial in range(24):
            alphabet=list(range(1,n if trial%2 else 3));headers=bool(trial%3);b=int(rng.integers(n-1))
            key=rng.permutation(n);pt=[rng.choice(alphabet,8).tolist() for _ in range(2)]
            pt[1][3:6]=pt[0][2:5];eq=[(0,2,1,3,3)]
            if headers:
                for m in pt:m[0]=int(rng.integers(n))
            ct=[encrypt_physical(m,key,1,b) for m in pt]
            if trial%2:ct[0][int(rng.integers(8))]=int(rng.integers(n))
            fixed={int(key[1]):1} if trial%4==0 else None
            possible=False
            for k in itertools.permutations(range(n)):
                if fixed and any(k[p]!=c for c,p in fixed.items()):continue
                decoded=decode_physical(ct,k,b)
                ok=all(p in alphabet for m in decoded for p in m[int(headers):])
                ok=ok and decoded[0][2:5]==decoded[1][3:6]
                if ok:possible=True;break
            result=solve(ct,n,alphabet,b,headers,100000,10,fixed,eq)
            assert result['status']!='inconclusive'
            assert (result['status']=='model_fit')==possible,(n,trial,result,possible)
            checks.append({'n':n,'trial':trial,'has_key':possible,'status':result['status']})
    return checks

if __name__=='__main__':
    from progressive_reduction import RUNS
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true')
    ap.add_argument('--shuffle',type=int,default=9);ap.add_argument('--alphabet',type=int,default=82)
    ap.add_argument('--seconds',type=int,default=30);ap.add_argument('--nodes',type=int,default=100000)
    ap.add_argument('--numbered-headers',action='store_true');ap.add_argument('--prefixes',action='store_true')
    ap.add_argument('--long-only',action='store_true');args=ap.parse_args();checks=verify()
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in RUNS if not args.long_only or n>=14]
    prefixes=[]
    if args.prefixes:
        for i in range(len(messages)):
            for j in range(i):
                t=1
                while t<min(len(messages[i]),len(messages[j])) and messages[i][t]==messages[j][t]:t+=1
                if t>1:prefixes.append((i,1,j,1,t-1))
        eq+=prefixes
    if args.control:
        rng=np.random.default_rng(20261017);key=rng.permutation(83)
        par={(i,t):(i,t) for i,m in enumerate(messages) for t in range(len(m))}
        def root(x):
            if par[x]!=x:par[x]=root(par[x])
            return par[x]
        for i,s,j,t,length in eq:
            for k in range(length):par[root((i,s+k))]=root((j,t+k))
        selections={root(x):int(rng.integers(1,args.alphabet+1)) for x in par}
        pts=[[selections[root((i,t))] for t in range(len(m))] for i,m in enumerate(messages)]
        if args.numbered_headers:
            for i,m in enumerate(pts):m[0]=i+1
        messages=[encrypt_physical(m,key,1,args.shuffle) for m in pts]
    fixed={m[0]:i+1 for i,m in enumerate(messages)} if args.numbered_headers else None
    assert fixed is None or len(fixed)==len(messages)
    result=solve(messages,83,list(range(1,args.alphabet+1)),args.shuffle,True,args.nodes,args.seconds,fixed,eq)
    result.update(small_exhaustive_controls=checks,prefix_equalities=prefixes,
                  numbered_headers_assumed=args.numbered_headers,
                  warning='A model fit is not authenticated plaintext; exclusions are conditional on listed equality and header assumptions.')
    if args.control:result['exact_planted_plaintext_recovered']=result.get('plaintext_positions')==pts
    name='shared_key_'+('control' if args.control else 'eyes')+'_'+str(args.shuffle)+'_'+str(args.alphabet)+('_numbered' if args.numbered_headers else '')+('_prefixes' if args.prefixes else '')+'.json'
    (ROOT/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in result.items() if k not in ['initial_deck','plaintext_positions','alphabet_positions','small_exhaustive_controls','assumed_plaintext_equalities','prefix_equalities','fixed_initial_positions']})
