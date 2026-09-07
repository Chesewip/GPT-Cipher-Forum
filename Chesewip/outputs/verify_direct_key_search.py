"""Independent replay and comparison checks for full-deck candidates."""
from pathlib import Path
import json
import numpy as np
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from rotation_vote_search import prepare,scores,direct_errors
from two_swap_prefix_repair import profiles
ROOT=Path(__file__).resolve().parent
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(raw);cl=make_plaintexts(raw,eq)
rng=np.random.default_rng(20261111);keys=np.array([rng.permutation(83) for _ in range(5)]);votes,C,invalid=scores(raw,keys,prepare(cl,82));vote_checks=0
for i,key in enumerate(keys):
    for b in range(82):
        error,_=direct_errors(raw,key.tolist(),b,cl)
        assert int(votes[i,b])==C-error-(C+1)*int(invalid[i]);vote_checks+=1
prefix=[m[:32] for m in raw];pcl=[m[:32] for m in cl];profile_checks=0
for b in [0,1,9,12,41,81]:
    masks,bad=profiles(prefix,keys,pcl,b)
    for i,key in enumerate(keys):
        error,_=direct_errors(prefix,key.tolist(),b,pcl)
        assert int(np.count_nonzero(~masks[i]))==error;profile_checks+=1

# Full physical replay, independent of the rotating-frame decoder.
def physical(pt,key,b):
    deck=key.copy();out=[]
    for p in pt:
        assert 1<=p<=82
        neighbor=1+p%82;old=deck[0];selected=deck[p];tail=deck[neighbor]
        deck[0]=selected;deck[p]=tail;deck[neighbor]=old;out.append(deck[0])
        if b:deck=[deck[0]]+deck[-b:]+deck[1:-b]
    return out
records=[]
for name in ['rotation_vote_eyes.json','rotation_vote_eyes_refined.json','common_key_prefix_32_refined.json','two_swap_prefix_repair.json']:
    r=json.loads((ROOT/name).read_text());key=r['initial_deck'];pt=r['plaintext_positions'];assert sorted(key)==list(range(83))
    assert [physical(m,key,r['rotation']) for m in pt]==[c[:len(m)] for c,m in zip(raw,pt)]
    seen={};errors=0
    for i,pts in enumerate(pt):
        for t,p in enumerate(pts):
            x=cl[i][t]
            if x in seen:errors+=p!=seen[x]
            else:seen[x]=p
    expected=r.get('shared_selection_disagreements',r.get('best_disagreements'));assert errors==expected
    records.append({'file':name,'positions_replayed':sum(map(len,pt)),'shared_selection_disagreements':errors})
r=json.loads((ROOT/'common_key_prefix_ladder.json').read_text())[0];assert r['prefix_length']==24 and r['shared_selection_disagreements']==0
assert [physical(m,r['initial_deck'],r['rotation']) for m in r['plaintext_positions']]==[m[:24] for m in raw]
seen={}
for i,pts in enumerate(r['plaintext_positions']):
    for t,p in enumerate(pts):
        x=cl[i][t]
        if x in seen:assert seen[x]==p
        seen[x]=p
out={'all_rotation_vote_checks':vote_checks,'fixed_rotation_profile_checks':profile_checks,'candidate_replays':records,'common_24_symbol_prefix_fit_verified':True,'prefix_outputs_verified':216,'warning':'No tested full-corpus key satisfies all shared-plaintext comparisons.'}
(ROOT/'checked_direct_key_search.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(out)
