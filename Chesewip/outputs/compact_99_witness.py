from pathlib import Path
import json, itertools
from compact_template_witnesses import construct
ROOT=Path(__file__).resolve().parent
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
if __name__=='__main__':
    witness=construct(raw[0],raw[1][:99],[0,25,33,50,59,68,73,78,89,99],cap=99,max_attempts=10000)
    witness['configured_token_run_cap']=witness.pop('maximum_token_run_length')
    witness['actual_maximum_token_run_length']=max(len(list(g)) for pt in witness['plaintext_tokens'] for _,g in itertools.groupby(pt))
    (ROOT/'compact_99_witness.json').write_text(json.dumps(witness,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in witness.items() if k not in ['common_initial_deck','plaintext_tokens','per_letter_permutations','relative_state_support_by_position']})
