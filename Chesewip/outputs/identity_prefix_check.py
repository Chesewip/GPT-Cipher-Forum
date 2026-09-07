from pathlib import Path
import json
from clocked_key_attack import decode
from clocked_three_cycle_scan import encrypt_physical
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());classes=make_plaintexts(raw,assumptions(raw));key=list(range(83));length=16
pt=decode([m[:length] for m in raw],key,9);seen={}
for m,cl in zip(pt,classes):
    for p,x in zip(m,cl):
        assert 1<=p<=82
        if x in seen:assert seen[x]==p
        seen[x]=p
assert all(encrypt_physical(m,key,1,9)==c[:length] for m,c in zip(pt,raw))
out={'status':'common_deck_prefix_fit','length':length,'positions':9*length,'initial_deck':key,'rotation':9,'plaintext_positions':pt,'assumed_equalities':assumptions(raw),'warning':'Identity-deck prefix compatibility only. No meaningful text or rotation identification. Full-corpus constraints fail for this key.'}
(ROOT/'identity_common_prefix_16.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Verified common identity-deck prefix fit:',9*length,'outputs')
