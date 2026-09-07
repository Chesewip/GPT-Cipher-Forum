from pathlib import Path
import json,sys,random,time,argparse,collections
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from synchronized_cycle_bound import reduction
from cycle_subset_bound import feasible

def resume(L,A,iterations=1000):
    path=ROOT/('synchronized_bound_'+str(L)+'_'+str(A)+'.json')
    data=json.loads(path.read_text())
    if data['status']=='excluded':return data
    msgs=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    rows,_,_,_=reduction(msgs,83,L);M=83-L;bound=data['outside_alphabet_bound']
    labels=sorted(rows,key=lambda c:rows[c].bit_count(),reverse=True)
    deleted={c:z3.Bool('d'+str(c)) for c in labels};solver=z3.Solver()
    solver.add(z3.AtMost(*deleted.values(),L));groups=data['bad_groups']
    counts=collections.Counter(c for g in groups for c in g)
    for g in groups:solver.add(z3.Or(*[deleted[c] for c in g]))
    start=time.time()
    for iteration in range(iterations):
        answer=solver.check()
        if answer==z3.unsat:data['status']='excluded';break
        if answer!=z3.sat:data['status']='solver_unknown';break
        model=solver.model()
        candidates=[c for c in labels if not z3.is_true(model.eval(deleted[c],model_completion=True))]
        if iteration%3:
            diverse=sorted(candidates,key=lambda c:rows[c].bit_count()-0.05*counts[c],reverse=True)
        else:diverse=candidates
        group=diverse[:10]
        r=feasible([rows[c] for c in group],M,bound,node_limit=1000000)
        data['subset_searches']+=1
        if r['status']!='unsat':
            group=candidates[:10]
            r=feasible([rows[c] for c in group],M,bound,node_limit=1000000)
            data['subset_searches']+=1
        if r['status']!='unsat':data['status']='relaxation_'+r['status'];break
        order=group[:];random.Random(iteration).shuffle(order)
        for c in order:
            trial=[b for b in group if b!=c]
            r=feasible([rows[b] for b in trial],M,bound,node_limit=1000000)
            data['subset_searches']+=1
            data['max_subset_nodes']=max(data['max_subset_nodes'],r['nodes'])
            if r['status']=='unsat':group=trial
        groups.append(group);counts.update(group)
        solver.add(z3.Or(*[deleted[c] for c in group]))
        if iteration%25==0:print('cycle',L,'total bad groups',len(groups),'core',len(group),flush=True)
    data['seconds']+=time.time()-start
    data['resumed_with_diverse_cores']=True
    path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('cycle',L,'status',data['status'],'groups',len(groups),flush=True)
    return data

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cycle',type=int,default=6);args=ap.parse_args()
    resume(args.cycle,40)
