from pathlib import Path
import json
from rotation_vote_search import search,direct_errors
from permutation_action_fold import make_plaintexts
from shared_update_support import assumptions
ROOT=Path(__file__).resolve().parent
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(raw);cl=make_plaintexts(raw,eq);base=json.loads((ROOT/'common_key_prefix_ladder.json').read_text())[-1]
r=search([m[:32] for m in raw],[m[:32] for m in cl],steps=100,restarts=2,start_key=base['initial_deck'],seed=20261109,temperature=0.4,temperature_floor=0.05,block_moves=120)
r['assumed_equalities']=eq;r['prefix_length']=32;r['full_corpus_shared_selection_disagreements']=direct_errors(raw,r['initial_deck'],r['rotation'],cl)[0]
(ROOT/'common_key_prefix_32_refined.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions','assumed_equalities']},flush=True)
