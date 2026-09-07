from pathlib import Path
import json
import numpy as np
from rotation_vote_search import prepare,scores
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent
p=ROOT/'common_key_prefix_ladder.json';results=json.loads(p.read_text());r=results[0]
ct=[x[:24] for x in json.loads((ROOT/'ciphertext.json').read_text()).values()];cl=make_plaintexts(list(json.loads((ROOT/'ciphertext.json').read_text()).values()),r['assumed_equalities']);cl=[x[:24] for x in cl]
v,C,bad=scores(ct,np.array([r['initial_deck']]),prepare(cl,82));r['compatible_rotations_at_same_key']=[b for b in range(82) if v[0,b]==C and bad[0]==0]
assert len(r['compatible_rotations_at_same_key'])==82
p.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('All 82 rotations fit the same 24-symbol-prefix key with their corresponding selections.')
