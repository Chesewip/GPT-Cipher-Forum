from pathlib import Path
import json,numpy as np
from key_swap_attack import partition_q,attack,encrypt
ROOT=Path(__file__).resolve().parent
messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
parts_list=[[1,41,41],[2,54,18,6,1,1,1],[6,54,18,2,1,1,1],
            [2,40,41],[3,40,40],[4,39,40],[8,37,38]]
results=[]
for parts in parts_list:
    print('Cycle partition',parts,flush=True)
    q=partition_q(parts)
    r=attack(messages,q,32,restarts=3,moves=160)
    r['cycle_partition']=parts;results.append(r)
    (ROOT/'structured_key_results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Finished',len(results),'partitions.')
