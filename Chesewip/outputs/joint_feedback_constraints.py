"""Bounded simultaneous key/codebook constraints on existing short controls.

The rule is supplied. Truth-assisted missing-label tests are explicitly marked;
the blind stage supplies no key entries or input codes. No Eye search is run
unless a blind control qualifies. All solver unknowns remain inconclusive.
"""
from pathlib import Path
import hashlib,json,random,sys,time
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work'/'pydeps'))
import z3
from verify_frozen_candidates import f,heldout,decode

def canonical(name,key):
    if name!='add':return key.copy()
    scale=pow((key[1]-key[0])%83,81,83)
    return [(x-key[0])*scale%83 for x in key]

def make_solver(messages,eq,name,pins,timeout_ms,cap=27):
    solver=z3.Solver();solver.set(timeout=timeout_ms,random_seed=83)
    key=[z3.BitVec('r%d'%j,7) for j in range(83)]
    solver.add(*[z3.ULT(v,83) for v in key],z3.Distinct(key))
    if name=='add':solver.add(key[0]==0,key[1]==1)
    for label,value in pins:solver.add(key[label]==value)
    feedback=[]
    for j,v in enumerate(key):
        if name=='add':feedback.append(v);continue
        result=z3.BitVec('f%d'%j,7)
        solver.add(z3.Or(*[z3.And(v==x,result==f(name,x)) for x in range(83)]))
        feedback.append(result)
    codes=z3.BitVec('codebook',128)
    solver.add(z3.Extract(127,83,codes)==0)
    solver.add(z3.AtMost(*[z3.Extract(j,j,codes)==1 for j in range(83)],cap))
    edges=sorted({(m[t-1],m[t]) for m in messages[:6] for t in range(2,len(m))})
    residual={}
    for a,b in edges:
        # Seven-bit arithmetic is safe: the final residue is in 0..82 even
        # when a negative difference wraps before the correction by 83.
        d=z3.If(z3.UGE(key[b],feedback[a]),key[b]-feedback[a],key[b]-feedback[a]+83)
        residual[a,b]=d
        solver.add(z3.Extract(0,0,z3.LShR(codes,z3.ZeroExt(121,d)))==1)
    for i,s,j,t,n in eq:
        for k in range(n):
            a,b=messages[i],messages[j]
            solver.add(residual[a[s+k-1],a[s+k]]==residual[b[t+k-1],b[t+k]])
    return solver,key,dict(distinct_training_edges=len(edges),training_transitions=sum(len(m)-2 for m in messages[:6]))

def run(c,early,late,hidden,order,timeout_ms):
    truth=canonical(c['name'],c['true_key']);unknown=set(order[:hidden]);pins=[[j,x] for j,x in enumerate(truth) if j not in unknown]
    start=time.monotonic();solver,key,counts=make_solver(c['ciphertext'],early,c['name'],pins,timeout_ms)
    built=time.monotonic();answer=solver.check();end=time.monotonic()
    r=dict(name=c['name'],hidden_labels=hidden,pins=pins,mode='blind_key' if hidden==83 else 'truth_assisted_partial_key',
        rule_supplied=True,timeout_ms=timeout_ms,solver_seed=83,status=str(answer),build_seconds=built-start,solve_seconds=end-built,**counts)
    if answer==z3.sat:
        model=solver.model();candidate=[model.eval(v).as_long() for v in key]
        d=decode(c['ciphertext'],c['name'],candidate);code=sorted({x for row in d[:6] for x in row[2:]})
        r.update(key=candidate,codebook=code,canonical_truth_matches=sum(x==y for x,y in zip(candidate,truth)),
                 heldout=heldout(c['ciphertext'],late,c['name'],candidate,code))
    elif answer==z3.unknown:r['reason_unknown']=solver.reason_unknown()
    return r

def main():
    raw=(ROOT/'frozen_candidate_search.json').read_bytes();source=json.loads(raw)
    out=dict(executed_date='2026-09-08',source_sha256=hashlib.sha256(raw).hexdigest(),z3_version=z3.get_version_string(),
        status='Simultaneous key and <=27 codebook constraint calibration; no Eye key.',
        training_messages=list(range(6)),heldout_messages=[6,7,8],global_no_doubles_constraint=False,controls=[])
    def save():(ROOT/'joint_feedback_constraints.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    for index,c in enumerate(source['controls']):
        order=random.Random(909880+index).sample(range(83),83)
        record=dict(seed=c['seed'],mask_seed=909880+index,hide_order=order,runs=[]);out['controls'].append(record)
        for hidden in [0,8,24,83]:
            r=run(c,source['early_equalities'],source['late_equalities'],hidden,order,12000)
            record['runs'].append(r);save()
            print(c['name'],'hidden',hidden,r['status'],'seconds',round(r['solve_seconds'],2),'truth matches',r.get('canonical_truth_matches'),flush=True)
    save()

def guards():
    raw=(ROOT/'frozen_candidate_search.json').read_bytes();source=json.loads(raw);records=[]
    for c in source['controls']:
        pins=list(enumerate(canonical(c['name'],c['true_key'])))
        solver,_,_=make_solver(c['ciphertext'],source['early_equalities'],c['name'],pins,12000,cap=26)
        answer=solver.check();assert answer==z3.unsat
        records.append(dict(seed=c['seed'],name=c['name'],all_key_entries_pinned=True,cap=26,status=str(answer)))
    out=dict(executed_date='2026-09-08',source_sha256=hashlib.sha256(raw).hexdigest(),guards=records)
    (ROOT/'joint_feedback_guards.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('All three fully pinned cap-26 negative controls rejected.',flush=True)

if __name__=='__main__':
    if '--guards' in sys.argv:guards()
    else:main()
