"""Recompute all 83 single-bottom-cycle necessary alphabet bounds."""
from pathlib import Path
import json,time
from cycle_subset_bound import bound_for
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
    start=time.time();messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    result=[]
    for top in range(83):
        r=bound_for(messages,83,top,10,44)
        assert r['status']=='unsat',r
        result.append(r)
        if top%10==0:print('Rechecked through initial top',top,flush=True)
    out={'all_83_rechecked':True,'passed':True,'seconds':time.time()-start,'results':result}
    (ROOT/'checked_cycle_subset_10_44.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('All 83 exclusions rechecked.')
