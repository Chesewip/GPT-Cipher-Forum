"""Key-free reduction of the top-swap/fixed-bottom-shuffle family.

Conjugate initial positions by card labels, so initial deck is identity and
common positional permutation Q fixes initial top label T. Undo only the swaps
in ciphertext to obtain b_t. Then plaintext selection p_t = Q**t(b_t).
"""
from pathlib import Path
import json, math, random
ROOT=Path(__file__).resolve().parent

def deswap(ct, top, n):
    position=list(range(n)); deck=list(range(n)); out=[]
    for c in ct:
        p=position[c]
        out.append(p)
        old=deck[top]
        deck[top],deck[p]=deck[p],deck[top]
        position[c]=top; position[old]=p
    return out

def graph_certificate(messages, n, top, equalities):
    reduced=[deswap(m,top,n) for m in messages]
    edges=[]
    for mi,si,mj,sj,length in equalities:
        for k in range(length):
            # Q**(si+k)(b_i) = Q**(sj+k)(b_j).
            edges.append((reduced[mi][si+k],reduced[mj][sj+k],si-sj))
    # Q(top)=top. Selecting top is forbidden.
    edges.append((top,top,1))
    adj=[[] for _ in range(n)]
    for u,v,d in edges:
        adj[u].append((v,d)); adj[v].append((u,-d))
    comp=[-1]*n; pot=[0]*n; components=[]
    for root in range(n):
        if comp[root]>=0:continue
        idx=len(components); comp[root]=idx; stack=[root]; vertices=[]; g=0
        while stack:
            u=stack.pop(); vertices.append(u)
            for v,d in adj[u]:
                if comp[v]<0:
                    comp[v]=idx;pot[v]=pot[u]+d;stack.append(v)
                else:g=math.gcd(g,pot[u]+d-pot[v])
        allowed=[]
        for L in range(len(vertices),n+1):
            if g and g%L:continue
            if len({pot[v]%L for v in vertices})==len(vertices):allowed.append(L)
        components.append(dict(vertices=vertices,offsets=[pot[v] for v in vertices],
                               cycle_gcd=abs(g),allowed_cycle_lengths=allowed))
    invalid=[c for c in components if not c['allowed_cycle_lengths']]
    if any(top in b for b in reduced):
        return dict(top=top,contradiction='forbidden top selection')
    return dict(top=top,contradiction=bool(invalid),invalid_components=invalid,
                components=components,edges=edges)

def verify_reduction():
    rng=random.Random(20260907)
    for trial in range(100):
        n=83 if trial>=50 else 11
        top=rng.randrange(n)
        bottom=[i for i in range(n) if i!=top]
        q=list(range(n)); shuffled=bottom[:];rng.shuffle(shuffled)
        for i,j in zip(bottom,shuffled):q[i]=j
        selections=[rng.choice(bottom) for _ in range(150)]
        deck=list(range(n)); ct=[]
        for p in selections:
            deck[top],deck[p]=deck[p],deck[top]
            ct.append(deck[top]); new=[None]*n
            for i,j in enumerate(q):new[j]=deck[i]
            deck=new
        base=deswap(ct,top,n)
        for t,(b,p) in enumerate(zip(base,selections)):
            for _ in range(t):b=q[b]
            assert b==p,(trial,t,b,p)
    return 100

RUNS=[(1,34,1,64,26),(2,39,2,74,24),(0,40,0,68,10),
      (1,40,2,45,11),(1,40,2,80,11),(3,18,4,24,14),
      (3,18,5,23,14),(6,51,7,53,12),(6,51,8,52,12),(6,68,7,71,33)]

if __name__=='__main__':
    controls=verify_reduction()
    msgs=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in RUNS]
    results=[graph_certificate(msgs,83,top,eq) for top in range(83)]
    out=dict(reduction_controls_passed=controls,assumed_equalities=eq,
             survivors=[r['top'] for r in results if not r['contradiction']],results=results)
    (ROOT/'progressive_reduction_results.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Reduction controls:',controls,'Surviving initial top labels:',out['survivors'])
