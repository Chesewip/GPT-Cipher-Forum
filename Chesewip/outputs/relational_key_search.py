"""Exact affine parameterization of passage relationships, then bounded SMT.

No control truth or late messages enters parameterization or candidate search.
The supplied function links the two maps after passage equations are solved.
"""
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work'/'pydeps'))
import z3
from verify_frozen_candidates import rows_for,f,decode,heldout

def parameterize(messages,eq,name):
    original=rows_for(messages,eq)
    if name=='add':original=[[(r[j]+r[j+83])%83 for j in range(83)] for r in original]
    width=83 if name=='add' else 166
    rows=[r+[0] for r in original]
    if name=='add':rows+=[[int(j==i) for j in range(width)]+[i] for i in [0,1]]
    matrix=[r.copy() for r in rows];pivots=[];rank=0
    for col in range(width):
        found=next((i for i in range(rank,len(matrix)) if matrix[i][col]),None)
        if found is None:continue
        matrix[rank],matrix[found]=matrix[found],matrix[rank]
        inv=pow(matrix[rank][col],81,83);matrix[rank]=[x*inv%83 for x in matrix[rank]]
        for i in range(len(matrix)):
            if i==rank or not matrix[i][col]:continue
            scale=matrix[i][col];matrix[i]=[(a-scale*b)%83 for a,b in zip(matrix[i],matrix[rank])]
        pivots.append(col);rank+=1
    assert not any(not any(r[:width]) and r[-1] for r in matrix)
    free=sorted(set(range(width))-set(pivots));base=[0]*width;directions=[]
    for i,j in enumerate(pivots):base[j]=matrix[i][-1]
    for j in free:
        v=[0]*width;v[j]=1
        for i,p in enumerate(pivots):v[p]=-matrix[i][j]%83
        directions.append(v)
    inactive=[j for j in range(width) if all(row[j]==0 for row in original)]
    return dict(width=width,original_rows=original,augmented_rows=rows,rank=rank,free_columns=free,
        particular=base,directions=directions,inactive_columns=inactive)

def search(messages,eq,name,timeout_ms=30000,negative_pair=None):
    started=time.monotonic();info=parameterize(messages,eq,name);solver=z3.Solver();solver.set(timeout=timeout_ms,random_seed=83)
    # Inactive feedback columns never enter another expression. Compute these
    # from their output variables rather than adding unused free parameters.
    omitted={j for j in info['inactive_columns'] if j>=83}
    variables={j:z3.BitVec('t%d'%j,7) for j in info['free_columns'] if j not in omitted}
    solver.add(*[z3.ULT(x,83) for x in variables.values()])
    expressions=[];arithmetic_bounds=[]
    for i,constant in enumerate(info['particular']):
        if i in omitted:expressions.append(None);continue
        if i in variables:expressions.append(variables[i]);continue
        terms=[(v[i],variables[j]) for j,v in zip(info['free_columns'],info['directions']) if v[i]]
        bound=constant+sum(a*82 for a,_ in terms);arithmetic_bounds.append(bound);assert bound<2**32
        total=z3.BitVecVal(constant,32)
        for a,x in terms:total+=a*z3.ZeroExt(25,x)
        expressions.append(z3.Extract(6,0,z3.URem(total,83)))
    key=expressions[:83];solver.add(z3.Distinct(key))
    if negative_pair is not None:
        assert name=='square'
        a,b=negative_pair
        solver.add(z3.ZeroExt(1,key[a])+z3.ZeroExt(1,key[b])==83)
    if name=='add':feedback=key
    else:
        feedback=[]
        for j in range(83):
            value=expressions[j+83]
            if value is None:value=z3.BitVec('s%d'%j,7)
            solver.add(z3.Or(*[z3.And(key[j]==x,value==f(name,x)) for x in range(83)]))
            feedback.append(value)
    book=z3.BitVec('book',128);solver.add(z3.Extract(127,83,book)==0)
    solver.add(z3.AtMost(*[z3.Extract(j,j,book)==1 for j in range(83)],27))
    edges=sorted({(m[t-1],m[t]) for m in messages[:6] for t in range(2,len(m))})
    for a,b in edges:
        d=z3.If(z3.UGE(key[b],feedback[a]),key[b]-feedback[a],key[b]-feedback[a]+83)
        solver.add(z3.Extract(0,0,z3.LShR(book,z3.ZeroExt(121,d)))==1)
    built=time.monotonic();answer=solver.check();finished=time.monotonic()
    result=dict(name=name,parameterization=info,solver_parameter_columns=sorted(variables),
        omitted_inactive_feedback_columns=sorted(omitted),largest_linear_sum_bound=max(arithmetic_bounds,default=0),
        status=str(answer),timeout_ms=timeout_ms,solver_seed=83,negative_pair_cut=negative_pair,build_seconds=built-started,solve_seconds=finished-built,
        distinct_training_edges=len(edges),training_transitions=sum(len(m)-2 for m in messages[:6]))
    if answer==z3.sat:
        model=solver.model();candidate=[model.eval(x).as_long() for x in key]
        decoded=decode(messages,name,candidate);codes=sorted({v for row in decoded[:6] for v in row[2:]})
        result.update(key=candidate,codebook=codes,parameter_values={str(j):model.eval(v).as_long() for j,v in variables.items()})
    elif answer==z3.unknown:result['reason_unknown']=solver.reason_unknown()
    return result

def main():
    raw=(ROOT/'frozen_candidate_search.json').read_bytes();source=json.loads(raw)
    out=dict(executed_date='2026-09-08',source_sha256=hashlib.sha256(raw).hexdigest(),z3_version=z3.get_version_string(),
        training_messages=list(range(6)),heldout_messages=[6,7,8],key_pins=[],function_supplied=True,
        global_no_doubles_constraint=False,status='Relational parameterization calibration; no Eye decipherment.',controls=[])
    for c in source['controls']:
        r=search(c['ciphertext'],source['early_equalities'],c['name']);entry=dict(seed=c['seed'],result=r)
        if 'key' in r:entry['heldout']=heldout(c['ciphertext'],source['late_equalities'],c['name'],r['key'],r['codebook'])
        out['controls'].append(entry)
        (ROOT/'relational_key_search.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
        print(c['name'],r['status'],'parameters',len(r['solver_parameter_columns']),'seconds',round(r['solve_seconds'],2),flush=True)

def pair_cut():
    raw=(ROOT/'frozen_candidate_search.json').read_bytes();source=json.loads(raw)
    proof_raw=(ROOT/'passage_domain_search.json').read_bytes();proof_source=json.loads(proof_raw)
    c=next(c for c in source['controls'] if c['name']=='square')
    old=next(c for c in proof_source['controls'] if c['name']=='square')['equations']
    match=[]
    for index,row in enumerate(old['rows']):
        support=[j for j,v in enumerate(row) if v]
        if len(support)==2 and all(j>=83 for j in support) and (row[support[0]]+row[support[1]])%83==0:
            match.append((index,[j-83 for j in support]))
    assert len(match)==1;index,pair=match[0]
    pairs=[[x,y] for x in range(83) for y in range(83) if x!=y and f('square',x)==f('square',y)]
    assert pairs==[[x,83-x] for x in range(1,83)]
    result=search(c['ciphertext'],source['early_equalities'],'square',negative_pair=pair)
    out=dict(executed_date='2026-09-08',source_sha256=hashlib.sha256(raw).hexdigest(),proof_source_sha256=hashlib.sha256(proof_raw).hexdigest(),
        seed=c['seed'],pair=pair,row=old['rows'][index],combination=old['combinations'][index],
        allowed_pairs=pairs,result=result)
    if 'key' in result:out['heldout']=heldout(c['ciphertext'],source['late_equalities'],'square',result['key'],result['codebook'])
    (ROOT/'relational_pair_cut.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    print('square explicit pair cut',pair,result['status'],round(result['solve_seconds'],2),flush=True)

if __name__=='__main__':
    if '--pair-cut' in sys.argv:pair_cut()
    else:main()
