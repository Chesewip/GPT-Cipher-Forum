from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('outputs').resolve()))
from progressive_reduction import deswap,RUNS,graph_certificate
m=list(json.load(open('outputs/ciphertext.json')).values())
for top in [0,1,2,10,20,40,82]:
    bs=[deswap(x,top,83) for x in m]
    e,w,z=bs[6][52:63],bs[7][54:65],bs[8][53:64]
    maps={};proof=[]
    for k,(a,b,c) in enumerate(zip(e,w,z)):
        for u,v,edge in [(b,c,'W4 -> E5'),(c,a,'E5 -> E4')]:
            if u in maps and maps[u][0]!=v:proof.append((u,maps[u],(v,k,edge)))
            maps[u]=(v,k,edge)
    print('top',top,'table',list(zip(e,w,z)),'conflicts',proof)
