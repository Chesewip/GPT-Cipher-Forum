import numpy as np
import json, math, time
from pathlib import Path
root=Path(__file__).resolve().parent
msgs=list(json.loads((root/'ciphertext.json').read_text()).values())
params=np.array([(a,b) for a in range(82) if math.gcd(a,82)==1 for b in range(82)],dtype=np.int32)
a=params[:,0,None]; b=params[:,1,None]; H=len(params); idx=np.arange(H)
def scan(messages, initial):
    hist=np.zeros((H,83),dtype=np.int32)
    for m in messages:
        pos=np.tile(np.argsort(initial),(H,1)).astype(np.int32)
        top=np.full(H,initial[0],dtype=np.int32)
        for c in m:
            p=pos[:,c].copy()
            hist[idx,p]+=1
            pos[idx,top]=p; pos[:,c]=0; top[:]=c
            pos=np.where(pos==0,0,1+(a*(pos-1)+b)%82)
    n=sum(map(len,messages))
    support=(hist>0).sum(axis=1)
    ioc=82*(hist*(hist-1)).sum(axis=1)/(n*(n-1))
    best=int(np.argmax(ioc)); small=int(np.argmin(support))
    return dict(candidates=H,minimum_support=int(support[small]),minimum_support_parameters=params[small].tolist(),maximum_normalized_ioc=float(ioc[best]),maximum_ioc_parameters=params[best].tolist(),maximum_ioc_support=int(support[best]))
if __name__=='__main__':
    res={}
    for direction in ('forward','reverse'):
        for first in ('included','excluded'):
            mm=[(m if first=='included' else m[1:]) for m in msgs]
            if direction=='reverse':mm=[list(reversed(m)) for m in mm]
            for initial in ('ascending','descending'):
                deck=list(range(83))
                if initial=='descending':deck.reverse()
                label=f'{direction}_{first}_{initial}'
                res[label]=scan(mm,deck)
                print(label,res[label],flush=True)
    (root/'deck_scan_results.json').write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8',newline='\r\n')
