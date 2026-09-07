from pathlib import Path
import json
from integer_return_paths import solve
from component_return_paths import components
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from return_displacement import graph
ROOT=Path(__file__).resolve().parent
base=json.loads((ROOT/'component_returns_20_9_free.json').read_text());warm={}
for r in base['components']:
    for x,v in r['selector_assignment']:warm[tuple(x)]=v
ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());pts=make_plaintexts(ct,assumptions(ct));groups=components(pts,[e for e in graph(ct,pts) if e[2]<=24])
r=solve(ct,pts,9,gap_limit=24,timeout=30000,edge_subset=groups[0],eliminate_free=True,warm=warm)
r['initial_values_only_not_pinned']=True
(ROOT/'warm_component_returns_24_9.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print({k:v for k,v in r.items() if k!='selector_assignment'},flush=True)
