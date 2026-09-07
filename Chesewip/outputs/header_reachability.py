"""Reachability with arbitrary first-symbol headers and a specified text alphabet.

Relaxation only: subsequent plaintext choices are not coupled across cards.
Unknown initial key is common to all messages; each message may choose any
first input position, including top. No repeated-plaintext assumptions.
"""
from pathlib import Path
import json,time,argparse
import numpy as np
from alphabet_reachability import predecessors,matching
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent

def bits(mask):
    while mask:
        bit=mask&-mask;mask-=bit;yield bit.bit_length()-1

def header_permutation(n,h,b):
    q=[0]+[1+(x-1+b)%(n-1) for x in range(1,n)]
    if h:
        r=1+h%(n-1);q[0],q[h],q[r]=q[r],q[0],q[h]
    return q

def constraints(messages,n,alphabet,b):
    full=(1<<n)-1;pre=predecessors(n,alphabet,b);layers=[1]
    for _ in range(max(map(len,messages))-1):
        reach=0
        for y in bits(layers[-1]):reach|=pre[y]
        layers.append(reach)
    perms=[header_permutation(n,h,b) for h in range(n)]
    unary=[full]*n;edges=[]
    for m in messages:
        hlabel=m[0];suffix={}
        for t,c in enumerate(m[1:],1):suffix[c]=suffix.get(c,full)&layers[t]
        for c,allowed in suffix.items():
            if allowed==full:continue
            relation=[sum(1<<x for x,y in enumerate(q) if allowed>>y&1) for q in perms]
            if c==hlabel:
                unary[c]&=sum(1<<h for h,row in enumerate(relation) if row>>h&1)
            else:
                relation=[row&~(1<<h) for h,row in enumerate(relation)]
                edges.append((hlabel,c,relation))
    return unary,edges

def propagate(dom,edges,n):
    dom=dom.copy();changed=True
    while changed:
        changed=False
        singles=0
        for d in dom:
            if not d:return None
            if d&(d-1)==0:
                if singles&d:return None
                singles|=d
        for c,d in enumerate(dom):
            if d&(d-1):
                v=d&~singles
                if not v:return None
                if v!=d:dom[c]=v;changed=True
        for h,c,rows in edges:
            hd=0;cd=0
            for p in bits(dom[h]):
                possible=rows[p]&dom[c]
                if possible:hd|=1<<p;cd|=possible
            if not hd or not cd:return None
            if hd!=dom[h]:dom[h]=hd;changed=True
            if cd!=dom[c]:dom[c]=cd;changed=True
    if matching(dom,n)['status']=='excluded':return None
    return dom

def solve(messages,n,alphabet,b,node_limit=3000):
    unary,edges=constraints(messages,n,alphabet,b);headers=set(m[0] for m in messages);nodes=0;witness=None
    def visit(dom):
        nonlocal nodes,witness
        nodes+=1
        if nodes>node_limit:return 'inconclusive'
        dom=propagate(dom,edges,n)
        if dom is None:return 'excluded'
        candidates=[h for h in headers if dom[h].bit_count()>1]
        if not candidates:
            witness=matching(dom,n)['position_assignment'];return 'relaxation_survives'
        h=min(candidates,key=lambda c:dom[c].bit_count());unknown=False
        for p in bits(dom[h]):
            child=dom.copy();child[h]=1<<p;status=visit(child)
            if status=='relaxation_survives':return status
            if status=='inconclusive':unknown=True;break
        return 'inconclusive' if unknown else 'excluded'
    status=visit(unary)
    return {'status':status,'shuffle_offset':b,'nodes':nodes,'node_limit':node_limit,
            'position_assignment':witness,'binary_constraints':len(edges)}

def controls():
    rng=np.random.default_rng(20261013);checks=0;formula=0
    for n in [7,11,83]:
        for _ in range(20):
            b=int(rng.integers(n-1));alphabet=list(range(1,min(28,n//2+1)));key=rng.permutation(n)
            pt=[[int(rng.integers(n))]+rng.choice(alphabet,25).tolist() for _ in range(4)]
            ct=[encrypt_physical(p,key,1,b) for p in pt];unary,edges=constraints(ct,n,alphabet,b);pos=np.argsort(key)
            assert all(unary[c]>>int(pos[c])&1 for c in range(n))
            assert all(rows[pos[h]]>>int(pos[c])&1 for h,c,rows in edges)
            fixed=[1<<int(p) for p in pos];assert propagate(fixed,edges,n) is not None
            assert solve(ct,n,alphabet,b,100)['status']!='excluded';checks+=1
            for h in range(n):
                q=header_permutation(n,h,b)
                # The second output for each possible next input equals the card at its predecessor position.
                for p in alphabet:
                    out=encrypt_physical([h,p],range(n),1,b)
                    assert q[out[1]]==p;formula+=1
    return {'positive_controls':checks,'header_formula_checks':formula}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--alphabet',type=int,default=27)
    ap.add_argument('--nodes',type=int,default=3000);ap.add_argument('--shuffle',type=int,nargs='*')
    args=ap.parse_args();start=time.time();out=controls();messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    results=[]
    for b in args.shuffle if args.shuffle is not None else range(82):
        r=solve(messages,83,list(range(1,args.alphabet+1)),b,args.nodes);results.append(r)
        print(b,r['status'],'nodes',r['nodes'],flush=True)
    out.update(results=results,seconds=time.time()-start,alphabet_bound=args.alphabet,
               scope='Unit neighbor, bottom rotation, contiguous text selection alphabet starting at 1, arbitrary initial key, arbitrary first header per message. No plaintext equalities.')
    (ROOT/f'header_reachability_{args.alphabet}.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('seconds',out['seconds'])
