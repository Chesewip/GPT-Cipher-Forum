"""Independent modular certificate checks and repeated-plaintext controls."""
from pathlib import Path
from collections import Counter
import json,math
import numpy as np
from block_system_exclusion import check
from progressive_reduction import RUNS,deswap
ROOT=Path(__file__).resolve().parent

def positive_controls(messages):
    rng=np.random.default_rng(20261003);lengths=list(map(len,messages));offsets=np.cumsum([0]+lengths).tolist()
    parent=list(range(offsets[-1]))
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in RUNS]
    for i,s,j,t,n in eq:
        for k in range(n):parent[root(offsets[i]+s+k)]=root(offsets[j]+t+k)
    results=[]
    for blocks in [2,41]:
        size=82//blocks
        for trial in range(10):
            key=rng.permutation(83);quotient=rng.permutation(blocks);q=np.arange(83)
            for block in range(blocks):q[1+block*size:1+(block+1)*size]=1+quotient[block]*size+rng.permutation(size)
            alphabet=rng.choice(np.arange(1,83),32,replace=False)
            letters={r:int(rng.choice(alphabet)) for r in {root(x) for x in parent}}
            pt=[[letters[root(offsets[i]+t)] for t in range(n)] for i,n in enumerate(lengths)]
            updates={}
            for p in alphabet:
                within=np.arange(83)
                for block in range(blocks):within[1+block*size:1+(block+1)*size]=1+block*size+rng.permutation(size)
                perm=q[within];perm=perm.copy();perm[0],perm[p]=perm[p],perm[0]
                updates[int(p)]=perm
            ct=[]
            for pp in pt:
                deck=key.tolist();cc=[]
                for p in pp:
                    new=[None]*83
                    for x,y in enumerate(updates[p]):new[int(y)]=deck[x]
                    deck=new;cc.append(deck[0])
                ct.append(cc)
            result=check(ct,83,int(key[0]),blocks,eq)
            assert result['status']=='relaxation_survives',(blocks,trial,result)
            results.append({'blocks':blocks,'trial':trial,'passed':True})
    return results

def verify_case(messages,case):
    blocks=case['blocks'];capacity=case['block_size'];checks=0
    for cert in case['results']:
        assert cert['status']=='excluded_conditionally'
        top=cert['initial_top'];base=[deswap(m,top,83) for m in messages]
        members=set(cert['component']);adj={v:[] for v in members}
        for i,s,j,t,n in case['equalities']:
            for k in range(n):
                u,v=base[i][s+k],base[j][t+k]
                if u in members and v in members:adj[u].append((v,s-t));adj[v].append((u,t-s))
        for period in range(1,blocks+1):
            phase={next(iter(members)):0};stack=list(phase);conflict=False
            while stack:
                u=stack.pop()
                for v,d in adj[u]:
                    p=(phase[u]+d)%period
                    if v not in phase:phase[v]=p;stack.append(v)
                    elif phase[v]!=p:conflict=True
            assert set(phase)==members
            overloaded=max(Counter(phase.values()).values())>capacity
            assert conflict or overloaded,(top,blocks,period)
            checks+=1
    return checks

def canonical_parameters():
    units=[u for u in range(1,82) if math.gcd(u,82)==1];orbits={}
    for d in range(1,82):
        for b in range(82):
            rep=min((d*u%82,b*u%82) for u in units)
            orbits[rep]=orbits.get(rep,0)+1
    assert len(orbits)==168
    remaining={p:count for p,count in orbits.items() if p[0]==1}
    assert len(remaining)==82 and sum(remaining.values())==3280
    return {'total_parameter_pairs':6642,'equivalence_classes':168,
            'classes_excluded_by_block_obstruction':86,'remaining_classes':82,
            'remaining_representatives':sorted(remaining),
            'at_alphabet_40_or_less_shuffle_zero_also_excluded_by_reachability':True}

def main():
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    data=json.loads((ROOT/'block_system_exclusion.json').read_text());verified=[]
    for case in data['cases']:
        if case['all_initial_keys_excluded_conditionally']:
            count=verify_case(messages,case);verified.append({'blocks':case['blocks'],'assumption_mode':case['assumption_mode'],'modular_cases_rechecked':count})
    controls=positive_controls(messages)
    result={'passed':True,'independent_certificate_checks':verified,'repeated_plaintext_positive_controls':controls,
            'parameter_reduction':canonical_parameters()}
    (ROOT/'checked_block_system_exclusion.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Passed',sum(c['modular_cases_rechecked'] for c in verified),'independent modular checks and',len(controls),'repeated-plaintext controls.')
    print({k:v for k,v in result['parameter_reduction'].items() if k!='remaining_representatives'})

if __name__=='__main__':main()
