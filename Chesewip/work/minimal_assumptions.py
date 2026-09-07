from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent.parent/'outputs'
sys.path.insert(0,str(ROOT))
from synchronized_isomorph import test
from progressive_reduction import RUNS
messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
chosen=list(range(len(RUNS)))
for index in chosen[1:]:
    trial=[i for i in chosen if i!=index]
    results=[test(messages,L,[RUNS[i] for i in trial]) for L in range(1,9)]
    if all(r['status']=='excluded_conditionally' for r in results):chosen=trial
    print('removed',index,index not in chosen,'retained',chosen,flush=True)
results=[test(messages,L,[RUNS[i] for i in chosen]) for L in range(1,9)]
out={'run_indices':chosen,'runs':[RUNS[i] for i in chosen],
     'description':'Greedily reduced sufficient internal-plaintext equalities; not a proven globally minimal set. Run 0 retains the return-gap witness for top cycles >=9.',
     'results':results}
(ROOT/'reduced_isomorph_assumptions.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
