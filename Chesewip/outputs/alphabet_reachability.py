"""Key-independent reachability for specified selection alphabets.

No repeated-plaintext assumptions. For each possible input word length,
compute which initial positions can reach the output. All occurrences of a
ciphertext label must admit the same initial position. A failed matching
has a finite Hall witness. A successful matching is only a relaxation.
"""
from pathlib import Path
import json,math,time,argparse
import numpy as np
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent

def predecessors(n,alphabet,b):
    M=n-1;pre=[0]*n
    for p in alphabet:
        r=1+p%M
        q=[0]+[1+(x-1+b)%M for x in range(1,n)]
        # Original selected card -> top; neighbor -> p; old top -> neighbor.
        q[0],q[p],q[r]=q[r],q[0],q[p]
        for x,y in enumerate(q):pre[y]|=1<<x
    return pre

def domains(messages,n,alphabet,b):
    pre=predecessors(n,alphabet,b);full=(1<<n)-1;reachable=1;layers=[]
    for t in range(max(map(len,messages))):
        nxt=0;bits=reachable
        while bits:
            bit=bits&-bits;bits-=bit;nxt|=pre[bit.bit_length()-1]
        reachable=nxt;layers.append(reachable)
        if reachable==full:
            layers.extend([full]*(max(map(len,messages))-len(layers)));break
    allowed=[full]*n
    for m in messages:
        for t,c in enumerate(m):allowed[c]&=layers[t]
    return allowed,layers

def matching(allowed,n):
    owner=[-1]*n;assigned=[-1]*n
    def augment(label,seen):
        bits=allowed[label]
        while bits:
            bit=bits&-bits;bits-=bit;p=bit.bit_length()-1
            if p in seen:continue
            seen.add(p)
            if owner[p]<0 or augment(owner[p],seen):
                owner[p]=label;assigned[label]=p;return True
        return False
    for c in sorted(range(n),key=lambda c:allowed[c].bit_count()):augment(c,set())
    missing=[c for c in range(n) if assigned[c]<0]
    if not missing:return {'status':'relaxation_survives','position_assignment':assigned}
    labels=set(missing);positions=set();stack=missing[:]
    while stack:
        c=stack.pop();bits=allowed[c]
        while bits:
            bit=bits&-bits;bits-=bit;p=bit.bit_length()-1
            if p in positions:continue
            positions.add(p)
            if owner[p]>=0 and owner[p] not in labels:labels.add(owner[p]);stack.append(owner[p])
    assert len(positions)<len(labels)
    return {'status':'excluded','labels':sorted(labels),'possible_initial_positions':sorted(positions),
            'matching_size':sum(p>=0 for p in assigned)}

def test(messages,n,A,b,stride=1):
    alphabet=[1+(k*stride)%(n-1) for k in range(A)]
    allowed,layers=domains(messages,n,alphabet,b);r=matching(allowed,n)
    if r['status']=='excluded':
        neighbors=0
        for c in r['labels']:neighbors|=allowed[c]
        assert neighbors.bit_count()<len(r['labels'])
    r.update(alphabet_bound=A,shuffle_offset=b,alphabet_stride=stride,
             output_reachability_counts=[v.bit_count() for v in layers[:15]])
    return r

def verify():
    rng=np.random.default_rng(20261009);checks=0
    for n in [11,83]:
        M=n-1;units=[u for u in range(1,M) if math.gcd(u,M)==1]
        for trial in range(30):
            A=min(27,n//2);b=int(rng.integers(M));stride=int(rng.choice(units));key=rng.permutation(n)
            alphabet=[1+k*stride%M for k in range(A)]
            pt=[rng.choice(alphabet,100).tolist() for _ in range(5)]
            ct=[encrypt_physical(p,key,1,b) for p in pt]
            allowed,_=domains(ct,n,alphabet,b);pos=np.argsort(key)
            assert all(allowed[c]>>int(pos[c])&1 for c in range(n))
            assert matching(allowed,n)['status']=='relaxation_survives';checks+=1
    return checks

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--alphabet',type=int,default=27)
    ap.add_argument('--all-strides',action='store_true');args=ap.parse_args()
    start=time.time();controls=verify();messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    strides=[s for s in range(1,82) if math.gcd(s,82)==1] if args.all_strides else [1]
    results=[]
    for stride in strides:
        results.extend(test(messages,83,args.alphabet,b,stride) for b in range(82))
        print('stride',stride,'excluded so far',sum(r['status']=='excluded' for r in results),'of',len(results),flush=True)
    out={'positive_controls_passed':controls,'results':results,
         'excluded_count':sum(r['status']=='excluded' for r in results),'tested_count':len(results),
         'scope':'Unknown common initial key; specified arithmetic-progression selection alphabet; no plaintext equalities assumed.',
         'seconds':time.time()-start}
    name='alphabet_reachability_'+str(args.alphabet)+('_all_strides' if args.all_strides else '')+'.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Excluded',out['excluded_count'],'of',out['tested_count'],'seconds',out['seconds'])
