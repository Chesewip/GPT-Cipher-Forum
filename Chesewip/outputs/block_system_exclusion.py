"""Conditional block-system obstruction, allowing arbitrary quotient shuffles.

Model: swap top with selected bottom position; apply any within-block
permutation; apply common Q which fixes top and permutes equal-size bottom
blocks. Each of the82 bottom positions belongs to one of k blocks.
Both k=2 and k=41 are tested; no numerical ordering or affine assumption.
"""
from pathlib import Path
from collections import Counter
import json,math
import numpy as np
from progressive_reduction import deswap,RUNS
ROOT=Path(__file__).resolve().parent

def check(messages,n,top,blocks,eq):
    capacity=(n-1)//blocks;reduced=[deswap(m,top,n) for m in messages]
    adj={c:[] for c in range(n) if c!=top}
    for i,s,j,t,length in eq:
        for k in range(length):
            u,v=reduced[i][s+k],reduced[j][t+k];d=s-t
            if top in [u,v]:raise ValueError('Possible identity selection in assumed equality')
            adj[u].append((v,d));adj[v].append((u,-d))
    offsets={};components=[]
    for root in adj:
        if root in offsets:continue
        offsets[root]=0;stack=[root];members=[];g=0
        while stack:
            u=stack.pop();members.append(u)
            for v,d in adj[u]:
                if v not in offsets:offsets[v]=offsets[u]+d;stack.append(v)
                else:g=math.gcd(g,offsets[u]+d-offsets[v])
        failures=[];allowed=[]
        for L in range(1,blocks+1):
            if g and g%L:continue
            counts=Counter(offsets[v]%L for v in members);peak=max(counts.values())
            if peak<=capacity:allowed.append(L)
            else:failures.append({'quotient_cycle_length':L,'overfull_phase_count':peak})
        if not allowed:
            return {'status':'excluded_conditionally','component':members,'offsets':{v:offsets[v] for v in members},
                    'cycle_length_must_divide':abs(g),'capacity':capacity,'candidate_cycle_failures':failures}
        components.append({'vertices':len(members),'allowed_lengths':allowed})
    return {'status':'relaxation_survives','components':components}

def verify():
    rng=np.random.default_rng(20261002);checks=0
    for blocks in [2,41]:
        size=82//blocks
        for trial in range(15):
            key=rng.permutation(83);top=int(key[0]);quotient=rng.permutation(blocks)
            # Q may arbitrarily rearrange positions within each destination block.
            q=np.arange(83)
            for block in range(blocks):
                q[1+block*size:1+(block+1)*size]=1+quotient[block]*size+rng.permutation(size)
            alph=rng.choice(np.arange(1,83),27,replace=False)
            updates={}
            for p in alph:
                within=np.arange(83)
                for block in range(blocks):within[1+block*size:1+(block+1)*size]=1+block*size+rng.permutation(size)
                updates[int(p)]=within
            pt=rng.choice(alph,180).tolist();deck=key.tolist();ct=[]
            for p in pt:
                deck[0],deck[p]=deck[p],deck[0]
                new=[None]*83
                for x,y in enumerate(updates[p]):new[int(q[y])]=deck[x]
                deck=new;ct.append(deck[0])
            base=deswap(ct,top,83);initial_block={int(c):(p-1)//size for p,c in enumerate(key) if p}
            power=np.arange(blocks)
            for p,c in zip(pt,base):
                assert (p-1)//size==power[initial_block[c]]
                power=quotient[power];checks+=1
    return checks

def main():
    controls=verify();messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cases=[]
    for mode in ['all','at_least_14','three_longest']:
        runs=[r for i,r in enumerate(RUNS) if mode=='all' or (mode=='at_least_14' and r[-1]>=14) or (mode=='three_longest' and i in [0,1,9])]
        eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in runs]
        for blocks in [2,41]:
            results=[{'initial_top':top,**check(messages,83,top,blocks,eq)} for top in range(83)]
            case={'blocks':blocks,'block_size':82//blocks,'assumption_mode':mode,
                  'all_initial_keys_excluded_conditionally':all(r['status']=='excluded_conditionally' for r in results),
                  'surviving_initial_top_labels':[r['initial_top'] for r in results if r['status']!='excluded_conditionally'],
                  'equalities':eq,'results':results}
            cases.append(case);print({k:v for k,v in case.items() if k not in ['results','equalities']},flush=True)
    out={'generated_block_projection_checks_passed':controls,'cases':cases,'model':__doc__}
    (ROOT/'block_system_exclusion.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
