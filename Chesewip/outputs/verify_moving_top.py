from pathlib import Path
import random,json
from moving_top_scan import encrypt,scan
ROOT=Path(__file__).resolve().parent
rng=random.Random(20260910)
pts=[[rng.randrange(1,28) for _ in range(120)] for _ in range(9)]
initial=list(range(83))
cts=[encrypt(pt,17,9,initial) for pt in pts]
result=scan(cts,initial)
assert result['minimum_support']==27,result
assert result['maximum_ioc_parameters']==[17,9],result
(ROOT/'moving_top_control.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(result)
