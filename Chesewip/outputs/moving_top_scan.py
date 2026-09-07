"""Common full-deck affine permutation, preceded by one selection swap.

Q(x)=a*x+b mod 83. Swap selected position with Q^-1(0), apply Q,
then output at position zero. This allows Q to move the previous top card.
"""
from pathlib import Path
import numpy as np
import json,time
ROOT=Path(__file__).resolve().parent
PARAMS=np.array([(a,b) for a in range(1,83) for b in range(83)],dtype=np.int32)
A=PARAMS[:,0,None];B=PARAMS[:,1,None];IDX=np.arange(len(PARAMS))
ANCHOR=np.array([(-b*pow(int(a),-1,83))%83 for a,b in PARAMS],dtype=np.int32)

def scan(messages,initial):
    hist=np.zeros((len(PARAMS),83),dtype=np.int32)
    for m in messages:
        pos=np.tile(np.argsort(initial),(len(PARAMS),1)).astype(np.int32)
        for c in m:
            p=pos[:,c].copy();hist[IDX,p]+=1
            other=np.argmax(pos==ANCHOR[:,None],axis=1)
            pos[IDX,other]=p;pos[:,c]=ANCHOR
            pos=(A*pos+B)%83
    count=sum(map(len,messages));support=(hist>0).sum(axis=1)
    score=82*(hist*(hist-1)).sum(axis=1)/(count*(count-1))
    k=int(np.argmax(score));j=int(np.argmin(support))
    return dict(configurations=len(PARAMS),minimum_support=int(support[j]),
                minimum_support_parameters=PARAMS[j].tolist(),
                maximum_ioc=float(score[k]),maximum_ioc_parameters=PARAMS[k].tolist())

def encrypt(pt,a,b,initial):
    deck=initial[:];anchor=(-b*pow(a,-1,83))%83;out=[]
    for p in pt:
        deck[anchor],deck[p]=deck[p],deck[anchor]
        new=[None]*83
        for i,c in enumerate(deck):new[(a*i+b)%83]=c
        deck=new;out.append(deck[0])
    return out

if __name__=='__main__':
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    result={}
    for direction in ['forward','reverse']:
        m=messages if direction=='forward' else [x[::-1] for x in messages]
        for order in ['ascending','descending']:
            initial=list(range(83))
            if order=='descending':initial.reverse()
            key=direction+'_'+order
            result[key]=scan(m,initial);print(key,result[key],flush=True)
    (ROOT/'moving_top_scan_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
