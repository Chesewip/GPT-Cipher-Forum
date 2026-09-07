"""Exact quotient constraints when extra moves preserve ring phase classes.

For neighbor offset d on an82-position ring, g=gcd(d,82) divides d.
The extra neighbor move changes no phase mod g. At that quotient level,
the update is a top swap followed by adding b to every bottom phase.
This reduction is independent of the initial key and within-phase moves.
"""
from pathlib import Path
from collections import Counter
import json,math
import numpy as np
from progressive_reduction import deswap,RUNS
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent

def check(messages,n,top,g,b,eq):
    reduced=[deswap(m,top,n) for m in messages];cap=(n-1)//g
    adj={c:[] for c in range(n) if c!=top}
    for i,s,j,t,length in eq:
        for k in range(length):
            u,v=reduced[i][s+k],reduced[j][t+k]
            if u==top or v==top:raise ValueError('An equality includes a possible initial identity selection')
            w=((s-t)*b)%g;adj[u].append((v,w));adj[v].append((u,-w))
    phase={};components=[]
    for root in adj:
        if root in phase:continue
        phase[root]=0;stack=[root];vertices=[]
        while stack:
            u=stack.pop();vertices.append(u)
            for v,w in adj[u]:
                expected=(phase[u]+w)%g
                if v not in phase:phase[v]=expected;stack.append(v)
                elif phase[v]!=expected:return {'status':'excluded_conditionally','reason':'inconsistent_phase_cycle','witness':[u,v,w,phase[u],phase[v]]}
        counts=Counter(phase[v] for v in vertices)
        if max(counts.values())>cap:
            return {'status':'excluded_conditionally','reason':'phase_capacity_exceeded','component':vertices,'phases':{v:phase[v] for v in vertices},'capacity':cap}
        components.append([counts.get(k,0) for k in range(g)])
    if g==2:
        sums={0}
        for c in components:sums={s+x for s in sums for x in c if s+x<=cap}
        if cap not in sums:return {'status':'excluded_conditionally','reason':'two_phase_capacity_partition_impossible'}
    return {'status':'relaxation_survives','component_count':len(components)}

def verify():
    rng=np.random.default_rng(20261001);checks=0
    for g in [2,41]:
        for trial in range(20):
            key=rng.permutation(83);top=int(key[0]);z={int(c):(p-1)%g for p,c in enumerate(key) if p}
            d=g;b=int(rng.integers(0,82));pts=[rng.integers(1,83,size=100).tolist() for _ in range(3)]
            for pt in pts:
                ct=encrypt_physical(pt,key,d,b);base=deswap(ct,top,83)
                for t,(p,c) in enumerate(zip(pt,base)):
                    assert (p-1)%g==(z[c]+t*b)%g;checks+=1
    return checks

def main():
    controls=verify();messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());out=[]
    for long_only in [False,True]:
        eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in RUNS if not long_only or n>=14]
        for g in [2,41]:
            for b in [0,1]:
                results=[{'initial_top':top,**check(messages,83,top,g,b,eq)} for top in range(83)]
                item={'phase_modulus':g,'shuffle_offset_modulo_phase':b,'long_passages_only':long_only,
                      'all_initial_keys_excluded_conditionally':all(r['status']=='excluded_conditionally' for r in results),
                      'surviving_initial_top_labels':[r['initial_top'] for r in results if r['status']!='excluded_conditionally'],
                      'results':results}
                out.append(item);print({k:v for k,v in item.items() if k!='results'},flush=True)
    result={'generated_phase_checks_passed':controls,'cases':out,
            'scope':'Clocked three-cycle model, or any update whose extra bottom moves preserve these phase classes, under the stated plaintext equalities.'}
    (ROOT/'quotient_phase_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
