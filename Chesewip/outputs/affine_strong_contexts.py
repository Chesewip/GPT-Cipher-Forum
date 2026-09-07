from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from affine_fixed_point_scan import scan
root=Path(__file__).resolve().parent;ct=list(json.loads((root/'ciphertext.json').read_text()).values())
contexts=[(1,34,1,64,18),(6,68,7,71,30),(6,68,8,69,30)]
for trim in [1,2,3]:
 maps=[]
 for i,s,j,t,n in contexts:
  maps.append(dict(zip(ct[i][s+trim-1:s+n],ct[j][t+trim-1:t+n])))
 r=scan(maps,12);r['contexts']=contexts;r['trim']=trim;r['observed_maps']=[sorted(d.items()) for d in maps]
 (root/f'affine_strong_contexts_trim{trim}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
 print('trim',trim,{k:v for k,v in r.items() if k not in ['observed_maps']},flush=True)
