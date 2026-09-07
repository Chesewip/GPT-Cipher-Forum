"""Positive-control ladder for a contiguous 27-position plaintext alphabet."""
from pathlib import Path
import json,argparse
import numpy as np
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_three_cycle_scan import encrypt_physical
from inverse_position_solver import solve
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--length',type=int,default=32);ap.add_argument('--timeout',type=int,default=20000);a=ap.parse_args()
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cl=make_plaintexts(raw,assumptions(raw));rng=np.random.default_rng(20261117);key=rng.permutation(83).tolist();value={x:int(rng.integers(1,28)) for row in cl for x in row};pt=[[value[x] for x in row] for row in cl]
for i,row in enumerate(pt):row[0]=i+1
ct=[encrypt_physical(row,key,1,9) for row in pt];ct=[row[:a.length] for row in ct];classes=[row[:a.length] for row in cl]
r=solve(ct,classes,9,timeout=a.timeout,alphabet_bound=27,unrestricted_first=True);r.update(control=True,seed=20261117,exact_planted_plaintext_recovered=r.get('plaintext_positions')==[row[:a.length] for row in pt],initial_key_unpinned=True)
(ROOT/f'inverse_alphabet27_control_{a.length}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions']},flush=True)
