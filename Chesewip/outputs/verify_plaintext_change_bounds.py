"""Independent certificate check: DP segmentation and inverse-index replay."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
raw=json.loads((ROOT/'ciphertext.json').read_text());names=list(raw);messages=list(raw.values())

def segment_bound(a,b):
    n=min(len(a),len(b));dp=[0]+[n+1]*n
    for left in range(n):
        forward={};reverse={}
        for right in range(left,n):
            x,y=a[right],b[right]
            if (x in forward and forward[x]!=y) or (y in reverse and reverse[y]!=x):break
            forward[x]=y;reverse[y]=x;dp[right+1]=min(dp[right+1],dp[left]+1)
    return dp[n]-1

bounds=json.loads((ROOT/'plaintext_change_bounds.json').read_text());checked=0
for r in bounds['pairs']:
    a,b=[raw[name] for name in r['messages']]
    assert segment_bound(a,b)==r['minimum_changes_required_by_intervals']
    previous=-1
    for iv in r['disjoint_conflict_certificate']:
        s,t=iv['witness_positions'];assert (a[s]==a[t])!=(b[s]==b[t])
        assert iv['left']==s+1 and iv['right']==t and previous<iv['left'];previous=t
    checked+=1

artifact=json.loads((ROOT/'sharp_prefix_counterexample.json').read_text());key=artifact['common_initial_deck'];perms=artifact['per_letter_permutations']
assert sorted(key)==list(range(83))
assert all(sorted(q)==list(range(83)) for q in perms)
sources=[q.index(0) for q in perms];assert len(set(sources))==len(perms) and 0 not in sources
inverse=[[q.index(y) for y in range(83)] for q in perms]
pts=artifact['plaintext_tokens'];ciphertexts=[];states=[]
for pt in pts:
    deck=key.copy();ct=[];trace=[]
    for p in pt:
        deck=[deck[x] for x in inverse[p]];ct.append(deck[0]);trace.append(deck.copy())
    ciphertexts.append(ct);states.append(trace)
assert ciphertexts==[m[:50] for m in messages[:2]]
differences=[t for t,(a,b) in enumerate(zip(*pts)) if a!=b];assert differences==[0,25,33]
assert segment_bound(*ciphertexts)+1==len(differences)==3
support=[sum(a!=b for a,b in zip(x,y)) for x,y in zip(*states)]
assert all(r>0 for r in support) and support[37:50]==[7]*13
out={'pairwise_bounds_checked_by_independent_dp':checked,'all_disjoint_witnesses_valid':True,
     'counterexample_ciphertext_replay_verified':True,'reversible_alphabet_size':len(sources),
     'plaintext_difference_positions_zero_based':differences,'sharp_common_initial_deck_bound':3,
     'different_state_positions_during_last_13_matching_outputs':7,
     'warning':'The engineered counterexample supplies no meaningful Noita plaintext or key.'}
(ROOT/'checked_plaintext_change_bounds.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(out)
