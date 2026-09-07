"""Necessary plaintext-change intervals for arbitrary deterministic deck ciphers.

If plaintext selections agree at s+1,...,t, the relation between paired
ciphertext labels remains one fixed bijection from output s through output t.
A conflicting pair at s,t therefore requires a plaintext difference in (s,t].
This does not assume any observed isomorph corresponds to shared plaintext.
"""
from pathlib import Path
import json,itertools,random
ROOT=Path(__file__).resolve().parent

def conflicts(a,b):
    out=[]
    for t,(x,y) in enumerate(zip(a,b)):
        for s,(u,v) in enumerate(zip(a[:t],b[:t])):
            if (u==x)!=(v==y):
                out.append({'left':s+1,'right':t,'witness_positions':[s,t],
                            'ciphertext_pairs':[[u,v],[x,y]]})
    return out

def minimum_changes(intervals):
    # Intervals are closed integer sets. Greedy interval stabbing is exact.
    chosen=[];packing=[];last=-1
    for iv in sorted(intervals,key=lambda r:(r['right'],-r['left'])):
        if last<iv['left']:
            last=iv['right'];chosen.append(last);packing.append(iv)
    assert all(any(iv['left']<=t<=iv['right'] for t in chosen) for iv in intervals)
    assert all(a['right']<b['left'] for a,b in zip(packing,packing[1:]))
    return {'minimum_changes_required_by_intervals':len(chosen),'one_minimum_hitting_set':chosen,
            'disjoint_conflict_certificate':packing}

def latest_changes(a,b):
    out=minimum_changes(conflicts(a,b));out['length_compared']=min(len(a),len(b))
    out['different_ciphertext_positions']=sum(x!=y for x,y in zip(a,b))
    out['common_initial_deck_first_difference_required']=int(bool(a and b and a[0]!=b[0]))
    out['minimum_total_with_common_initial_deck']=out['minimum_changes_required_by_intervals']+out['common_initial_deck_first_difference_required']
    return out

def encrypt(pt,key,permutations):
    deck=list(key);out=[]
    for p in pt:
        new=[None]*len(deck)
        for x,y in enumerate(permutations[p]):new[y]=deck[x]
        deck=new;out.append(deck[0])
    return out

def verify():
    rng=random.Random(20261021);checks=0
    for n in [7,19,83]:
        for trial in range(100):
            alphabet=min(12,n-1);perms=[]
            sources=rng.sample(range(1,n),alphabet)
            for source in sources:
                q=list(range(n));rng.shuffle(q)
                k=q.index(0);q[k],q[source]=q[source],q[k]
                perms.append(q)
            a=[rng.randrange(alphabet) for _ in range(100)];b=a.copy()
            for t in rng.sample(range(100),rng.randrange(1,20)):b[t]=rng.randrange(alphabet)
            ka=list(range(n));kb=ka.copy();rng.shuffle(ka)
            if trial%2:kb=ka.copy()
            else:rng.shuffle(kb)
            ca=encrypt(a,ka,perms);cb=encrypt(b,kb,perms);intervals=conflicts(ca,cb)
            changed={t for t,(x,y) in enumerate(zip(a,b)) if x!=y}
            assert all(any(iv['left']<=t<=iv['right'] for t in changed) for iv in intervals)
            assert minimum_changes(intervals)['minimum_changes_required_by_intervals']<=len(changed-{0})
            if ka==kb:assert latest_changes(ca,cb)['minimum_total_with_common_initial_deck']<=len(changed)
            checks+=1
    # Compare interval optimum with all possible cut sets on short arbitrary pairs.
    brute=0
    for _ in range(100):
        a=[rng.randrange(4) for _ in range(8)];b=[rng.randrange(4) for _ in range(8)]
        ivs=conflicts(a,b);best=8
        for mask in range(1<<7):
            points={t+1 for t in range(7) if mask>>t&1}
            if all(any(iv['left']<=t<=iv['right'] for t in points) for iv in ivs):best=min(best,len(points))
        assert minimum_changes(ivs)['minimum_changes_required_by_intervals']==best;brute+=1
    return {'generated_arbitrary_permutation_controls':checks,'exhaustive_interval_checks':brute}

if __name__=='__main__':
    out=verify();raw=json.loads((ROOT/'ciphertext.json').read_text());names=list(raw);messages=list(raw.values());pairs=[]
    for i,a in enumerate(messages):
        for j in range(i):
            r=latest_changes(messages[j],a);r.update(messages=[names[j],names[i]])
            pairs.append(r)
    focus=[]
    for end in [25,29,33,37,50,99]:
        r=latest_changes(messages[0][:end],messages[1][:end]);r['prefix_length']=end;focus.append(r)
    out.update(pairs=pairs,east1_west1_prefixes=focus,
               scope='Necessary bounds for a deterministic plaintext-selected permutation of a deck followed by reading one fixed output position. Any key, any per-letter permutations, no plaintext alphabet bound. Pairwise alignment is by message index.',
               caveat='The interval optimum is only a necessary lower bound on real plaintext Hamming distance. Its selected positions are not recovered plaintext edits.')
    (ROOT/'plaintext_change_bounds.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    for r in focus:print('prefix',r['prefix_length'],'minimum total',r['minimum_total_with_common_initial_deck'],'one hitting set',r['one_minimum_hitting_set'])
    print('pair bounds',[(r['messages'],r['minimum_total_with_common_initial_deck']) for r in pairs])
