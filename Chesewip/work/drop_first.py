from pathlib import Path
import sys,json,time
sys.path.insert(0,str(Path('outputs').resolve()))
from cycle_subset_bound import bound_for
m=[v[1:] for v in json.load(open('outputs/ciphertext.json')).values()]
start=time.time();results=[bound_for(m,83,t,8,40) for t in range(83)]
Path('outputs/cycle_subset_drop_first_8_40.json').write_text(json.dumps(dict(seconds=time.time()-start,results=results,all_unsat=all(r['status']=='unsat' for r in results)),indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('First symbols treated as metadata. All 83 tops exclude 40-symbol alphabet:',all(r['status']=='unsat' for r in results))
