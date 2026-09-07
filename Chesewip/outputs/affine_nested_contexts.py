from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from affine_fixed_point_scan import scan
ct=list(json.load(open(ROOT/'ciphertext.json')).values());contexts=[(6,68,7,71,30),(6,68,8,69,30),(6,73,4,64,25)]
for trim in [1,3]:
 maps=[]
 for i,s,j,t,n in contexts:
  pairs=list(zip(ct[i][s+trim-1:s+n],ct[j][t+trim-1:t+n]));m=dict(pairs);assert len(m)==len(set(y for x,y in pairs));maps.append(m)
 r=scan(maps,12);r.update(contexts=contexts,trim=trim,observed_maps=[list(m.items()) for m in maps]);(ROOT/f'affine_nested_contexts_trim{trim}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k!='observed_maps'},flush=True)
