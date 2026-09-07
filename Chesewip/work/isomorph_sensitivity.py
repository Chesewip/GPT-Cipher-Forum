from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parent.parent/'outputs';sys.path.insert(0,str(ROOT))
from synchronized_isomorph import test
from progressive_reduction import RUNS
messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());out=[]
for skip in range(1,6):
    runs=[(i,s+skip-1,j,t+skip-1,n-skip+1) for i,s,j,t,n in RUNS]
    results=[test(messages,L,runs) for L in range(1,9)]
    item={'first_included_relative_plaintext_position':skip,'small_top_cycle_statuses':[r['status'] for r in results]}
    out.append(item);print(item,flush=True)
(ROOT/'isomorph_boundary_sensitivity.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
