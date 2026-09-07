from pathlib import Path
import sys,json,time
sys.path.insert(0,str(Path('outputs').resolve()))
from cycle_subset_bound import bound_for
path=Path('outputs/cycle_subset_10_44.json');data=json.loads(path.read_text());msgs=list(json.load(open('outputs/ciphertext.json')).values())
seen={x['top'] for x in data['results']};start=time.time()
for top in range(83):
    if top not in seen:data['results'].append(bound_for(msgs,83,top,10,44))
data['results'].sort(key=lambda x:x['top']);data['seconds']+=time.time()-start
data['all_unsat']=all(x['status']=='unsat' for x in data['results'])
path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('44-symbol bound cases:',len(data['results']),'all unsat:',data['all_unsat'])
