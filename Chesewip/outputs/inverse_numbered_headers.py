"""Test inverse-position solver with explicit numbered-header assumption."""
from pathlib import Path
import json,argparse
from inverse_position_solver import solve
from adaptive_equality_search import fixture
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');ap.add_argument('--length',type=int,default=32);ap.add_argument('--rotation',type=int,default=9);ap.add_argument('--all-rotations',action='store_true');ap.add_argument('--timeout',type=int,default=20000);a=ap.parse_args()
if a.control:ct,cl,key,pt=fixture()
else:ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cl=make_plaintexts(ct,assumptions(ct))
ct=[m[:a.length] for m in ct];cl=[m[:a.length] for m in cl];fixed={m[0]:i+1 for i,m in enumerate(ct)};assert len(fixed)==9
r=solve(ct,cl,None if a.all_rotations else a.rotation,timeout=a.timeout,fixed=fixed);r.update(control=a.control,numbered_headers=True,fixed_initial_positions=fixed)
if a.control:r['exact_planted_plaintext_recovered']=r.get('plaintext_positions')==[m[:a.length] for m in pt]
name='inverse_numbered_'+('control' if a.control else 'eyes')+'_'+str(a.length)+('_all' if a.all_rotations else '_'+str(a.rotation))+'.json'
(ROOT/name).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions']},flush=True)
