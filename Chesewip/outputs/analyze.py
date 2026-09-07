from pathlib import Path
import csv, json, collections, math, random, hashlib
ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'ciphertext.json').read_text(encoding='utf-8'))
names=list(data)
msgs=list(data.values())
def ioc(x):
    f=collections.Counter(x); n=len(x)
    return 83*sum(v*(v-1) for v in f.values())/(n*(n-1))
# Nodes denote zero-based plaintext selection indices in the bottom 82 cards.
# Edge (u,v,d) means selection[v] = P**d(selection[u]).
def recurrence_edges(messages):
    edges=[]; base=0
    for m in messages:
        last={}
        for t,c in enumerate(m):
            if c in last:
                r=last[c]
                if t==r+1: raise ValueError('adjacent repeat outside no-doubles family')
                edges.append((base+r+1,base+t,t-r-1))
            last[c]=t
        base+=len(m)
    return edges

def analyze_graph(messages, equalities=()):
    sizes=[len(m) for m in messages]; offsets=[0]
    for n in sizes: offsets.append(offsets[-1]+n)
    edges=recurrence_edges(messages)
    for mi,si,mj,sj,n in equalities:
        edges.extend((offsets[mi]+si+k,offsets[mj]+sj+k,0) for k in range(n))
    adj=[[] for _ in range(offsets[-1])]
    for u,v,d in edges: adj[u].append((v,d)); adj[v].append((u,-d))
    component=[-1]*len(adj); potential=[0]*len(adj); gcds=[]; members=[]
    for root in range(len(adj)):
        if component[root]>=0: continue
        idx=len(gcds); component[root]=idx; stack=[root]; g=0; group=[]
        while stack:
            u=stack.pop(); group.append(u)
            for v,d in adj[u]:
                if component[v]<0:
                    component[v]=idx; potential[v]=potential[u]+d; stack.append(v)
                else: g=math.gcd(g,potential[u]+d-potential[v])
        gcds.append(abs(g)); members.append(group)
    # Distinct already-seen cards must occupy distinct bottom positions.
    failures=[]
    for mi,m in enumerate(messages):
        last={}; base=offsets[mi]
        for t,c in enumerate(m):
            expressions=[]
            for label,r in last.items():
                if r==t-1: continue  # this card is at top, not bottom
                u=base+r+1
                expressions.append((label,component[u],potential[u]+t-r-1,r))
            for a in range(len(expressions)):
                ca,ga,ea,ra=expressions[a]
                for cb,gb,eb,rb in expressions[a+1:]:
                    if ga!=gb: continue
                    g=gcds[ga]; diff=ea-eb
                    if (diff==0 if g==0 else diff%g==0):
                        failures.append(dict(message=mi,position=t,cards=[ca,cb],last_positions=[ra,rb],component=ga,cycle_divides=g,exponent_difference=diff))
                        break
                if failures: break
            if failures: break
            last[c]=t
        if failures: break
    return dict(nodes=len(adj),edges=len(edges),components=len(gcds),nonzero_cycle_constraints=sorted([g for g in gcds if g]),largest_components=sorted([len(g) for g in members],reverse=True)[:10],contradiction=failures[:1])

# Published exact isomorphs. All positions zero-based.
equalities=[(1,34,1,64,26),(2,39,2,74,24),(0,40,0,68,10),(1,40,2,45,11),(1,40,2,80,11),(3,18,4,24,14),(3,18,5,23,14),(6,51,7,53,12),(6,51,8,52,12),(6,68,7,71,33)]
def signature(s):
    ids={}; return [ids.setdefault(v,len(ids)) for v in s]
for mi,si,mj,sj,n in equalities:
    assert signature(msgs[mi][si:si+n])==signature(msgs[mj][sj:sj+n]),(mi,si,mj,sj,n)
res={'data':dict(lengths=[len(m) for m in msgs],total=sum(map(len,msgs)),alphabet=sorted(set(sum(msgs,[]))),ioc=ioc(sum(msgs,[])),adjacent_repeats=sum(a==b for m in msgs for a,b in zip(m,m[1:])),crosscheck='GitHub ngraham20 CSV equals Lymm37 wiki ASCII data'), 'graph':{}}
res['graph']['no_plaintext_assumptions']=analyze_graph(msgs)
for k,e in enumerate(equalities): res['graph']['isomorph_'+str(k)]=dict(equality=e,result=analyze_graph(msgs,[e]))
res['graph']['full_output_plaintext_assumption']=analyze_graph(msgs,equalities)
transition_equalities=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in equalities]
res['graph']['internal_transition_plaintext_assumption']=analyze_graph(msgs,transition_equalities)
res['boundary_audit']=[dict(ciphertext_match=e,preceding_output_preserves_pattern=signature(msgs[i][s-1:s+n])==signature(msgs[j][t-1:t+n])) for e in equalities for i,s,j,t,n in [e]]
# Positive controls: encryption under arbitrary random bottom permutation and initial deck.
rng=random.Random(20260906)
def encrypt(pt,P,initial):
    deck=initial[:]; out=[]
    for p in pt:
        deck[0],deck[p+1]=deck[p+1],deck[0]
        out.append(deck[0]); old=deck[1:]; bottom=[0]*82
        for i,j in enumerate(P): bottom[j]=old[i]
        deck[1:]=bottom
    return out
checks=[]
for trial in range(20):
    P=list(range(82)); rng.shuffle(P); initial=list(range(83)); rng.shuffle(initial)
    phrase=[rng.randrange(27) for _ in range(26)]
    pt=[rng.randrange(27) for _ in range(34)]+phrase+[rng.randrange(27) for _ in range(4)]+phrase+[rng.randrange(27) for _ in range(20)]
    ct=encrypt(pt,P,initial)
    result=analyze_graph([ct],[(0,34,0,64,26)])
    assert not result['contradiction'],result
    checks.append(True)
res['positive_controls']=dict(random_permutation_ciphers=len(checks),passed=sum(checks))
# Initial-order-independent information for move-to-front encoding.
mtf=[]
for m in msgs:
    last={}
    for t,c in enumerate(m):
        if c in last: mtf.append(len(set(m[last[c]+1:t])))
        last[c]=t
res['move_to_front']=dict(forced_ranks=sorted(set(mtf)),observations=len(mtf),minimum_plaintext_symbols=len(set(mtf)))
(ROOT/'results.json').write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Verified corpus:',res['data']['total'],'symbols; observed alphabet size:',len(res['data']['alphabet']))
print('Positive controls:',res['positive_controls'])
print('Corrected transition assumptions:',res['graph']['internal_transition_plaintext_assumption'])
print('Move-to-front minimum selection alphabet:',res['move_to_front']['minimum_plaintext_symbols'])
