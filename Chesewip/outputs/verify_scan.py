from pathlib import Path
import sys,json,random
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from deck_scan import scan
rng=random.Random(20260906)
a,b=17,9
pts=[]; cts=[]
for _ in range(9):
    pt=[rng.randrange(27) for _ in range(120)];pts.append(pt)
    deck=list(range(83));ct=[]
    for p in pt:
        deck[0],deck[p+1]=deck[p+1],deck[0]
        ct.append(deck[0]); old=deck[1:]; bottom=[0]*82
        for i,v in enumerate(old):bottom[(a*i+b)%82]=v
        deck[1:]=bottom
    cts.append(ct)
r=scan(cts,list(range(83)))
assert r['minimum_support']==27,r
assert r['maximum_ioc_parameters']==[a,b],r
(ROOT/'scan_control.json').write_text(json.dumps(dict(planted_parameters=[a,b],plaintext_alphabet=27,result=r),indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(r)
