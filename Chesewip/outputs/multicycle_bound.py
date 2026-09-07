"""Necessary alphabet bounds for multiple residual shuffle cycles.

Only a proved UNSAT is an exclusion. SAT is a relaxation, never a key.
The synchronization reduction ignores prefix labels and at most L labels
from the unknown initial top orbit. Remaining labels have distinct phases
within whichever residual cycle contains them.
"""
from pathlib import Path
import sys,json,time,argparse,itertools
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from synchronized_cycle_bound import reduction
from cycle_subset_bound import feasible

def get_rows(messages,n,L,lengths):
    base,forbidden,warmups,observations=reduction(messages,n,L)
    rows={M:{b:0 for b in base} for M in set(lengths)}
    for mi,t,b in observations:
        for M,rr in rows.items():
            if b in rr:rr[b]|=1<<(t%M)
    return rows,forbidden,warmups

def pair_cost(p,q,M):
    mask=(1<<M)-1
    return min((p|(((q<<s)|(q>>(M-s)))&mask)).bit_count() for s in range(1,M)) if M>1 else 2

def prove(messages,parts,A,iterations=1000,node_limit=100000,seconds=240):
    start=time.time();n=sum(parts);L=parts[0];lengths=parts[1:]
    rows,forbidden,warmups=get_rows(messages,n,L,lengths)
    labels=sorted(next(iter(rows.values())))
    gaps=set()
    for m in messages:
        last={}
        for t,c in enumerate(m):
            if c in last and t-last[c]<=L:gaps.add(t-last[c])
            last[c]=t
    top_cost=len(gaps)
    solver=z3.Solver();solver.set(timeout=15000)
    color={b:[z3.Bool('cycle_'+str(b)+'_'+str(k)) for k in range(len(lengths)+1)] for b in labels}
    budgets=[[z3.Bool('alphabet_'+str(k)+'_at_least_'+str(a+1)) for a in range(M)] for k,M in enumerate(lengths)]
    for v in color.values():solver.add(z3.PbEq([(x,1) for x in v],1))
    solver.add(z3.AtMost(*[v[0] for v in color.values()],L))
    solver.add(z3.AtMost(*[x for bb in budgets for x in bb],A-top_cost))
    def at_least(k,cost):
        if cost<=0:return z3.BoolVal(True)
        if cost>lengths[k]:return z3.BoolVal(False)
        return budgets[k][cost-1]
    for k,M in enumerate(lengths):
        for a in range(1,M):solver.add(z3.Implies(budgets[k][a],budgets[k][a-1]))
        solver.add(z3.AtMost(*[v[k+1] for v in color.values()],M))
        for b in labels:
            solver.add(z3.Implies(color[b][k+1],at_least(k,rows[M][b].bit_count())))
        for b,c in itertools.combinations(labels,2):
            cost=pair_cost(rows[M][b],rows[M][c],M)
            solver.add(z3.Or(z3.Not(color[b][k+1]),z3.Not(color[c][k+1]),at_least(k,cost)))
        for j in range(k):
            if lengths[j]==M:
                for a in range(M):solver.add(z3.Implies(budgets[j][a],budgets[k][a]))
    groups=[];status='inconclusive';checks=0;model_summary=None
    for iteration in range(iterations):
        if time.time()-start>seconds:status='time_limit';break
        ans=solver.check()
        if ans==z3.unsat:status='excluded';break
        if ans!=z3.sat:status='solver_unknown';break
        model=solver.model();added=False
        model_summary={'budgets':[sum(z3.is_true(model.eval(x)) for x in bb) for bb in budgets],
                       'deleted':[b for b in labels if z3.is_true(model.eval(color[b][0]))]}
        for k,M in enumerate(lengths):
            bound=model_summary['budgets'][k]
            assigned=[b for b in labels if z3.is_true(model.eval(color[b][k+1]))]
            assigned.sort(key=lambda b:rows[M][b].bit_count(),reverse=True)
            if not assigned:continue
            group=assigned[:10]
            r=feasible([rows[M][b] for b in group],M,bound,node_limit=node_limit);checks+=1
            if r['status']!='unsat':continue
            for b in group[::-1]:
                trial=[c for c in group if c!=b]
                if not trial:continue
                r=feasible([rows[M][c] for c in trial],M,bound,node_limit=node_limit);checks+=1
                if r['status']=='unsat':group=trial
            groups.append(dict(length=M,labels=group,minimum_alphabet=bound+1))
            for j,Mj in enumerate(lengths):
                if Mj==M:
                    solver.add(z3.Or(*[z3.Not(color[b][j+1]) for b in group],at_least(j,bound+1)))
            added=True
        if not added:status='relaxation_survives';break
        if iteration%20==0:print(parts,'iteration',iteration,'groups',len(groups),'budgets',model_summary['budgets'],flush=True)
    return dict(status=status,solver_encoding='Boolean membership and unary alphabet budgets',cycle_partition=parts,alphabet_bound=A,top_cost=top_cost,
                warmups=warmups,excluded_prefix_labels=sorted(forbidden),bad_groups=groups,
                subset_checks=checks,last_relaxation=model_summary,seconds=time.time()-start)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--parts',default='1,41,41')
    ap.add_argument('--alphabet',type=int,default=40);ap.add_argument('--seconds',type=int,default=240)
    args=ap.parse_args();parts=list(map(int,args.parts.split(',')))
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    out=prove(messages,parts,args.alphabet,seconds=args.seconds)
    name='multicycle_bound_'+'_'.join(map(str,parts))+'_'+str(args.alphabet)+'.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in out.items() if k!='bad_groups'})
