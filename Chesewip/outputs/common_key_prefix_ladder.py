from pathlib import Path
import json
from rotation_vote_search import search,direct_errors
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(raw);cl=make_plaintexts(raw,eq);key=list(range(83));out=[]
for length in [24,32,40]:
    r=search([m[:length] for m in raw],[m[:length] for m in cl],steps=30,restarts=1,start_key=key,temperature=0.05,temperature_floor=0,block_moves=80,seed=20261108)
    r['prefix_length']=length;r['assumed_equalities']=eq
    if r['status']=='structural_model_fit':
        key=r['initial_deck'];errors,_=direct_errors(raw,key,r['rotation'],cl);r['full_corpus_shared_selection_disagreements']=errors
    out.append(r);print('prefix',length,r['status'],r['shared_selection_disagreements'],r.get('full_corpus_shared_selection_disagreements'),flush=True)
    if r['status']!='structural_model_fit':break
(ROOT/'common_key_prefix_ladder.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
