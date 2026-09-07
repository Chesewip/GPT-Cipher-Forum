"""Exact finite-domain packing of independent free coordinate components.
No SMT solver: enumerate each F83 parameter and require disjoint symbol images.
"""
from pathlib import Path
import json,time
import numpy as np
from affine_linear_certificate import matrix
ROOT=Path(__file__).resolve().parent

def solve(maps,multipliers,anchors):
    original=matrix(maps,multipliers,anchors);a=original.copy();r=0;piv=[];n=a.shape[1]-1;start=time.time()
    for c in range(n):
        nz=np.flatnonzero(a[r:,c])
        if not len(nz):continue
        p=r+int(nz[0]);a[[r,p]]=a[[p,r]];a[r]=a[r]*pow(int(a[r,c]),-1,83)%83;v=a[:,c].copy();v[r]=0;a=(a-v[:,None]*a[r])%83;piv.append(c);r+=1
        if r==len(a):break
    pr={c:i for i,c in enumerate(piv)};free=[c for c in range(n) if c not in pr];obs=sorted({x for m in maps for p in m.items() for x in p});expr={}
    for c in obs+list(range(83,n)):
        if c in pr:expr[c]=dict(constant=int(a[pr[c],-1]),coefficients={k:int(-a[pr[c],k]%83) for k in free if a[pr[c],k]})
        else:expr[c]=dict(constant=0,coefficients={c:1})
    assert all(len(e['coefficients'])<=1 for e in expr.values()),'Coupled free components require a different solver.'
    fixed={c:e['constant'] for c,e in expr.items() if c<83 and not e['coefficients']};assert len(set(fixed.values()))==len(fixed);occupied=sum(1<<v for v in fixed.values());variables=sorted({v for e in expr.values() for v in e['coefficients']});domains=[]
    for v in variables:
        labels=[c for c,e in expr.items() if c<83 and v in e['coefficients']];placements=[]
        for value in range(83):
            image=[(expr[c]['constant']+expr[c]['coefficients'][v]*value)%83 for c in labels]
            if len(set(image))!=len(image):continue
            mask=sum(1<<x for x in image)
            if mask&occupied:continue
            placements.append(dict(parameter=value,images=image,mask=mask))
        domains.append(dict(variable=v,labels=labels,placements=placements))
    nodes=0
    def visit(remaining,used,chosen):
        nonlocal nodes
        nodes+=1
        if not remaining:return chosen
        feasible={i:[p for p in domains[i]['placements'] if not p['mask']&used] for i in remaining};best=min(remaining,key=lambda i:len(feasible[i]))
        for placement in feasible[best]:
            answer=visit([i for i in remaining if i!=best],used|placement['mask'],{**chosen,domains[best]['variable']:placement['parameter']})
            if answer is not None:return answer
        return None
    assignment=visit(list(range(len(domains))),occupied,{})
    out=dict(status='affine_context_embedding' if assignment is not None else 'no_injective_embedding',multipliers=multipliers,fixed_coordinates=fixed,free_components=domains,expressions=expr,backtracking_nodes=nodes,seconds=time.time()-start)
    if assignment is not None:
        values={c:(e['constant']+sum(coeff*assignment[v] for v,coeff in e['coefficients'].items()))%83 for c,e in expr.items()};coords=[values.get(c,-1) for c in range(83)];unused=iter(x for x in range(83) if x not in coords);coords=[next(unused) if v<0 else v for v in coords];offsets=[values[83+i] for i in range(len(maps))];assert sorted(coords)==list(range(83))
        for mapping,mult,offset in zip(maps,multipliers,offsets):assert all(coords[y]==(mult*coords[x]+offset)%83 for x,y in mapping.items())
        out.update(coordinates=coords,offsets=offsets,assignment=assignment,all_observed_edges_verified=True)
    return out

if __name__=='__main__':
    data=json.loads((ROOT/'affine_strong_linear_trim3.json').read_text());maps=[dict(m) for m in data['observed_maps'][:2]];results=[]
    for pair in data['stage1_open_pairs']:
        r=solve(maps,pair,data['anchors']);results.append(r);print('multipliers',pair,r['status'],'domains',[len(d['placements']) for d in r['free_components']],'nodes',r['backtracking_nodes'],flush=True)
    (ROOT/'affine_last_family_packing.json').write_text(json.dumps(dict(results=results,scope='Complete affine embeddings of two last-family partial context maps only; not cipher keys for full messages.'),indent=2)+'\n',encoding='utf-8',newline='\r\n')
