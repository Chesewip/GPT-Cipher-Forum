"""Independent set-based check of arbitrary-header reachability exclusions.

Constructs physical forward position transitions, unlike the discovery
code's inverse bit masks. Recomputes every relation and removes unsupported
values. A Hall witness, when needed, is checked directly as a set inequality.
"""
from pathlib import Path
import json,time
ROOT=Path(__file__).resolve().parent

def physical_move(n,p,b):
    deck=list(range(n))
    if p:
        r=1+p%(n-1);deck[0],deck[p],deck[r]=deck[p],deck[r],deck[0]
    if b:deck=[deck[0]]+deck[-b:]+deck[1:-b]
    position=[deck.index(card) for card in range(n)]
    return position

def check(messages,n,A,b):
    universe=set(range(n));trans=[physical_move(n,p,b) for p in range(1,A+1)]
    possible=[{x} for x in range(n)];layers=[{0}]
    destinations=[set(q[x] for q in trans) for x in range(n)]
    for _ in range(max(map(len,messages))):
        possible=[set().union(*(destinations[x] for x in s)) for s in possible]
        layer={x for x,s in enumerate(possible) if 0 in s};layers.append(layer)
        if layer==universe:
            layers.extend([universe]*(max(map(len,messages))+1-len(layers)));break
    domains=[universe.copy() for _ in range(n)];relations=[]
    moves=[physical_move(n,p,b) for p in range(n)]
    for m in messages:
        head=m[0];allowed={}
        for t,c in enumerate(m[1:],1):allowed[c]=allowed.get(c,universe)&layers[t]
        for c,allowed_positions in allowed.items():
            if allowed_positions==universe:continue
            rows=[{x for x in universe if move[x] in allowed_positions} for move in moves]
            if head==c:domains[c]&={h for h in universe if h in rows[h]}
            else:
                for h,row in enumerate(rows):row.discard(h)
                relations.append((head,c,rows))
    removed=0;iterations=0
    while True:
        iterations+=1;changed=False
        if any(not d for d in domains):return {'excluded':True,'reason':'empty_domain','iterations':iterations,'removed_values':removed}
        fixed=[next(iter(d)) for d in domains if len(d)==1]
        if len(fixed)!=len(set(fixed)):return {'excluded':True,'reason':'duplicate_singleton','iterations':iterations,'removed_values':removed}
        for d in domains:
            if len(d)>1:
                old=len(d);d.difference_update(fixed);removed+=old-len(d);changed|=old!=len(d)
        for head,c,rows in relations:
            hp={h for h in domains[head] if rows[h]&domains[c]}
            cp=set().union(*(rows[h] for h in hp))&domains[c]
            removed+=len(domains[head])+len(domains[c])-len(hp)-len(cp)
            changed|=hp!=domains[head] or cp!=domains[c];domains[head]=hp;domains[c]=cp
        if not changed:break
    # This routine only discovers a witness; verify its inequality directly.
    from alphabet_reachability import matching
    witness=matching([sum(1<<x for x in d) for d in domains],n)
    if witness['status']=='excluded':
        labels=witness['labels'];neighbors=set().union(*(domains[c] for c in labels))
        assert len(neighbors)<len(labels)
        return {'excluded':True,'reason':'Hall','labels':labels,'neighbors':sorted(neighbors),
                'iterations':iterations,'removed_values':removed}
    return {'excluded':False,'iterations':iterations,'removed_values':removed}

if __name__=='__main__':
    start=time.time();messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    targets=[(27,b) for b in [0,1,41,81]]+[(41,1),(42,81)]
    results=[]
    for A,b in targets:
        result=check(messages,83,A,b);assert result['excluded'];result.update(alphabet_bound=A,shuffle_offset=b)
        results.append(result);print(A,b,result['reason'],flush=True)
    out={'independently_recomputed_exclusions':results,'seconds':time.time()-start,
         'scope':'Arbitrary common initial key and arbitrary first symbol per message; subsequent inputs in contiguous specified alphabet. No repeated plaintext assumption.'}
    (ROOT/'checked_header_reachability.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('seconds',out['seconds'])
