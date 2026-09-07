"""Construct actual bijective embeddings for the four surviving last-family cases."""
from pathlib import Path
import json,sys,time
import numpy as np
from affine_linear_certificate import matrix
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3

def complete(maps,multipliers,anchors,timeout=10000):
    original=matrix(maps,multipliers,anchors);a=original.copy();rows,nplus=a.shape;n=nplus-1;r=0;pivots=[];start=time.time()
    for c in range(n):
        nz=np.flatnonzero(a[r:,c])
        if not len(nz):continue
        p=r+int(nz[0]);a[[r,p]]=a[[p,r]];a[r]=a[r]*pow(int(a[r,c]),-1,83)%83;v=a[:,c].copy();v[r]=0;a=(a-v[:,None]*a[r])%83;pivots.append(c);r+=1
        if r==rows:break
    free=[c for c in range(n) if c not in pivots];pr={c:i for i,c in enumerate(pivots)};observed=sorted({x for m in maps for pair in m.items() for x in pair});needed=observed+list(range(83,n));used=set()
    for c in needed:
        if c not in pr:used.add(c)
        else:used.update(k for k in free if a[pr[c],k])
    s=z3.Solver();s.set(timeout=timeout);var={k:z3.Int('free_'+str(k)) for k in sorted(used)}
    for v in var.values():s.add(v>=0,v<83)
    expression={}
    for c in needed:
        if c not in pr:expression[c]=var[c]
        else:
            row=a[pr[c]];expression[c]=(int(row[-1])-sum(int(row[k])*var[k] for k in free if row[k]))%83
    s.add(z3.Distinct(*[expression[c] for c in observed]));status=str(s.check());out=dict(status=status,multipliers=multipliers,active_free_coordinates=len(var),observed_symbols=len(observed),seconds=time.time()-start)
    if status=='unknown':out['reason']=s.reason_unknown()
    if status=='sat':
        model=s.model();values={c:model.eval(v).as_long() if isinstance(v,z3.AstRef) else int(v) for c,v in expression.items()};coordinates=[values.get(c,-1) for c in range(83)];unused=iter(x for x in range(83) if x not in coordinates);coordinates=[next(unused) if c<0 else c for c in coordinates];offsets=[values[83+i] for i in range(len(maps))]
        assert sorted(coordinates)==list(range(83))
        for m,mult,offset in zip(maps,multipliers,offsets):assert all(coordinates[y]==(mult*coordinates[x]+offset)%83 for x,y in m.items())
        out.update(coordinates=coordinates,offsets=offsets,all_observed_edges_verified=True)
    return out

if __name__=='__main__':
    data=json.loads((ROOT/'affine_strong_linear_trim3.json').read_text());maps=[dict(m) for m in data['observed_maps'][:2]];results=[]
    for pair in data['stage1_open_pairs']:
        r=complete(maps,pair,data['anchors']);results.append(r);print({k:v for k,v in r.items() if k!='coordinates'},flush=True)
    (ROOT/'affine_last_family_completions.json').write_text(json.dumps(dict(results=results,scope='Embeddings of two last-family context maps only. Not full-message cipher keys or plaintext.'),indent=2)+'\n',encoding='utf-8',newline='\r\n')
