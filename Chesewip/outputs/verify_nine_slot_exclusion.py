"""Independent exhaustive replay of the recorded nine-slot UNSAT neighborhood."""
from pathlib import Path
import itertools,json,time
import numpy as np
from two_swap_prefix_repair import profiles
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent
saved=json.loads((ROOT/'inverse_repair_prefix32.json').read_text());source=json.loads((ROOT/saved['source']).read_text());key=np.array(source['initial_deck']);slots=saved['free_slots'];assert len(slots)==9
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cl=make_plaintexts(raw,assumptions(raw));ct=[m[:32] for m in raw];cl=[m[:32] for m in cl];start=time.time();perms=itertools.permutations(key[slots]);tested=0;best=100000
while True:
    batch=list(itertools.islice(perms,8192))
    if not batch:break
    keys=np.tile(key,(len(batch),1));keys[:,slots]=np.array(batch);matched,invalid=profiles(ct,keys,cl,saved['rotation']);errors=(~matched).sum(axis=1)+10000*invalid;best=min(best,int(errors.min()));tested+=len(batch)
    assert best>0
assert tested==362880
out=dict(status='restricted_neighborhood_excluded',permutations_tested=tested,minimum_disagreements=best,free_slots=slots,source=saved['source'],rotation=saved['rotation'],seconds=time.time()-start,scope='Every permutation of these nine initial slots, with all other entries fixed; not a cipher-family exclusion.')
(ROOT/'checked_nine_slot_exclusion.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n');print(out,flush=True)
