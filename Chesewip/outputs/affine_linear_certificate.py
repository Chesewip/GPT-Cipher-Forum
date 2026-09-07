"""Auditable fixed-multiplier affine embeddings using exact modular elimination.
Open means this necessary linear test has not excluded an injective labeling.
Every exclusion carries a row-combination certificate, not a solver timeout.
"""
from pathlib import Path
import json,time,itertools,collections,argparse
import numpy as np
ROOT=Path(__file__).resolve().parent
P=83

def matrix(maps,multipliers,anchors):
    rows=[];n=83+len(maps)
    for g,(mapping,a) in enumerate(zip(maps,multipliers)):
        for x,y in mapping.items():
            row=np.zeros(n+1,dtype=np.int64);row[y]+=1;row[x]-=a;row[83+g]-=1;rows.append(row%P)
    for x,value in zip(anchors,[0,1]):
        row=np.zeros(n+1,dtype=np.int64);row[x]=1;row[-1]=value;rows.append(row)
    return np.array(rows,dtype=np.int64)

def analyze(maps,multipliers,anchors,certificate=True):
    original=matrix(maps,multipliers,anchors);a=original.copy();m,nplus=a.shape;n=nplus-1;transform=np.eye(m,dtype=np.int64) if certificate else None;r=0;pivots=[]
    for col in range(n):
        nz=np.flatnonzero(a[r:,col])
        if not len(nz):continue
        chosen=r+int(nz[0]);a[[r,chosen]]=a[[chosen,r]]
        if certificate:transform[[r,chosen]]=transform[[chosen,r]]
        scale=pow(int(a[r,col]),-1,P);a[r]=a[r]*scale%P
        if certificate:transform[r]=transform[r]*scale%P
        v=a[:,col].copy();v[r]=0;a=(a-v[:,None]*a[r])%P
        if certificate:transform=(transform-v[:,None]*transform[r])%P
        pivots.append(col);r+=1
        if r==m:break
    contradiction=next((k for k in range(r,m) if a[k,-1]),None)
    if contradiction is not None:
        out=dict(status='inconsistent',rank=r)
        if certificate:out['weights']=transform[contradiction].tolist();out['nonzero_constant']=int(a[contradiction,-1])
        return out
    pivotrow={c:i for i,c in enumerate(pivots)};free=[c for c in range(n) if c not in pivotrow];freeindex={c:i for i,c in enumerate(free)};seen={}
    for c in range(83):
        expression=np.zeros(len(free)+1,dtype=np.int64)
        if c in pivotrow:
            k=pivotrow[c];expression[:-1]=-a[k,free]%P;expression[-1]=a[k,-1]
        else:expression[freeindex[c]]=1
        sig=tuple(expression)
        if sig in seen:
            other=seen[sig];out=dict(status='forced_collision',rank=r,collision=[c,other])
            if certificate:
                w=np.zeros(m,dtype=np.int64)
                if c in pivotrow:w+=transform[pivotrow[c]]
                if other in pivotrow:w-=transform[pivotrow[other]]
                out['weights']=(w%P).tolist()
                target=np.zeros(nplus,dtype=np.int64);target[c]=1;target[other]=-1
                assert np.array_equal(np.array(out['weights'])@original%P,target%P)
            return out
        seen[sig]=c
    return dict(status='linear_test_open',rank=r)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--trim',type=int,default=3);args=ap.parse_args()
    source=json.loads((ROOT/f'affine_strong_contexts_trim{args.trim}.json').read_text());allmaps=[dict(pairs) for pairs in source['observed_maps']];maps=allmaps[1:];anchors=list(dict.fromkeys(x for pair in maps[0].items() for x in pair))[:2];stage1=[];open_pairs=[];start=time.time()
    for a in range(1,83):
        for b in range(1,83):
            r=analyze(maps,[a,b],anchors);r['multipliers']=[a,b];stage1.append(r)
            if r['status']=='linear_test_open':open_pairs.append([a,b])
        if a%10==0:print('first multiplier',a,'of 82','open',len(open_pairs),'seconds',round(time.time()-start,2),flush=True)
    print('stage1',dict(collections.Counter(r['status'] for r in stage1)),'open',open_pairs,flush=True)
    extended=maps+[allmaps[0]];stage2=[]
    for pair in open_pairs:
        for a in range(1,83):
            r=analyze(extended,pair+[a],anchors);r['multipliers']=pair+[a];stage2.append(r)
    remaining=[r['multipliers'] for r in stage2 if r['status']=='linear_test_open']
    out=dict(status='conditional_affine_exclusion' if not remaining else 'linear_test_inconclusive',modulus=83,trim=args.trim,anchors=anchors,contexts=source['contexts'],map_order=[1,2,0],observed_maps=[list(m.items()) for m in extended],stage1=stage1,stage2=stage2,stage1_open_pairs=open_pairs,remaining_multiplier_triples=remaining,seconds=time.time()-start,scope='Necessary affine embeddings of the three strong partial context maps under an arbitrary common bijective coordinate assignment. Conditional on repeated-plaintext interpretation. Does not decrypt or identify the cipher.',prior_art='Independent implementation of the staged multiplier strategy already published in mvelzel/eye-vibe scripts/prove_c82_combined_contexts.py; no first-discovery claim.')
    (ROOT/f'affine_strong_linear_trim{args.trim}.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n');print('result',out['status'],'stage2',dict(collections.Counter(r['status'] for r in stage2)),'seconds',out['seconds'],flush=True)
