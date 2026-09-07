from pathlib import Path
import json,argparse
import numpy as np
from rotation_vote_search import search
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');args=ap.parse_args()
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(raw);cl=make_plaintexts(raw,eq)
if args.control:
    rng=np.random.default_rng(20261106);key=rng.permutation(83);values={x:int(rng.integers(1,83)) for row in cl for x in row};pt=[[values[x] for x in row] for row in cl]
    for i,row in enumerate(pt):row[0]=i+1
    raw=[encrypt_physical(row,key,1,9) for row in pt]
name='rotation_vote_'+('control' if args.control else 'eyes');previous=json.loads((ROOT/(name+'.json')).read_text())
r=search(raw,cl,steps=80,restarts=1,start_key=previous['initial_deck'],seed=20261107,temperature=0.15,block_moves=160,temperature_floor=0)
r['assumed_equalities']=eq;r['resumed_from']=name+'.json'
if args.control:r['exact_planted_plaintext_recovered']=r['plaintext_positions']==pt
(ROOT/(name+'_refined.json')).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions','assumed_equalities']},flush=True)
