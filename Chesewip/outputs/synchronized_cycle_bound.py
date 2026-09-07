"""Exact necessary alphabet constraints after synchronizing a small top orbit.

Class: swap Q^-1(top) with selected position, apply Q, output top.
Q has cycles of lengths L (containing top) and N-L. Initial deck is arbitrary.
Unknown initial top-orbit labels may invalidate at most L chosen support rows.
Bad support subsets must all be hit by these unknown labels. UNSAT of that
hitting-set problem certifies exclusion, independently of plaintext isomorphs.
"""
from pathlib import Path
import sys,json,time,argparse
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from cycle_subset_bound import feasible
from key_swap_attack import canonical_q,encrypt

def reduction(messages,n,L):
    warmups=[];forbidden=set();observations=[]
    for m in messages:
        w=next((t for t in range(L,len(m)+1) if len(set(m[t-L:t]))==L),None)
        if w is None:raise ValueError('No synchronizing block')
        warmups.append(w);forbidden.update(m[:w])
    for mi,(m,w) in enumerate(zip(messages,warmups)):
        orbit=list(reversed(m[w-L:w]));inverse=list(range(n))
        for t in range(w,len(m)):
            c=m[t];anchor=orbit[-1];b=inverse[c]
            observations.append((mi,t,b))
            if c in orbit:
                j=orbit.index(c);orbit[j]=anchor
            orbit[-1]=c
            orbit=[orbit[-1]]+orbit[:-1]
            inverse[c],inverse[anchor]=inverse[anchor],inverse[c]
    M=n-L;rows={c:0 for c in range(n) if c not in forbidden}
    for mi,t,b in observations:
        if b in rows:rows[b]|=1<<(t%M)
    return rows,forbidden,warmups,observations

def verify():
    rng=np.random.default_rng(20260918);checks=0
    for L in range(2,9):
        q=canonical_q(83,L)
        for trial in range(10):
            initial=rng.permutation(83);pos=np.argsort(initial)
            alphabet=rng.choice(np.arange(1,83),32,replace=False)
            pt=[rng.choice(alphabet,120).tolist() for _ in range(9)]
            ct=[encrypt(p,q,initial) for p in pt]
            rows,forbidden,warmups,observations=reduction(ct,83,L)
            unknown=set(initial[:L].tolist())
            for mi,t,b in observations:
                if b not in forbidden and b not in unknown:
                    expected=L+(int(pos[b])-L+t)%(83-L)
                    assert pt[mi][t]==expected,(L,trial,mi,t,b,pt[mi][t],expected)
                    checks+=1
    return checks

def prove(messages,n,L,A,iterations=300,core_minimize=True):
    start=time.time();rows,forbidden,warmups,_=reduction(messages,n,L)
    observed_gaps=set()
    for m in messages:
        last={}
        for t,c in enumerate(m):
            if c in last and t-last[c]<=L:observed_gaps.add(t-last[c])
            last[c]=t
    top_cost=len(observed_gaps);outside_bound=A-top_cost
    labels=sorted(rows,key=lambda c:rows[c].bit_count(),reverse=True)
    deleted={c:z3.Bool('initial_orbit_'+str(c)) for c in labels}
    solver=z3.Solver();solver.add(z3.AtMost(*deleted.values(),L))
    groups=[];status='inconclusive';searches=0;max_nodes=0
    for iteration in range(iterations):
        answer=solver.check()
        if answer==z3.unsat:status='excluded';break
        if answer!=z3.sat:status='solver_unknown';break
        model=solver.model()
        assumed=[c for c in labels if z3.is_true(model.eval(deleted[c],model_completion=True))]
        candidates=[c for c in labels if c not in assumed]
        group=candidates[:min(10,len(candidates))]
        r=feasible([rows[c] for c in group],n-L,outside_bound,node_limit=1000000)
        searches+=1;max_nodes=max(max_nodes,r['nodes'])
        if r['status']!='unsat':
            status='relaxation_'+r['status'];break
        if core_minimize:
            for c in group[::-1]:
                trial=[b for b in group if b!=c]
                r=feasible([rows[b] for b in trial],n-L,outside_bound,node_limit=1000000)
                searches+=1;max_nodes=max(max_nodes,r['nodes'])
                if r['status']=='unsat':group=trial
        groups.append(group);solver.add(z3.Or(*[deleted[c] for c in group]))
        if iteration%10==0:print('cycle',L,'iteration',iteration,'bad group size',len(group),flush=True)
    return dict(status=status,cycle_partition=[L,n-L],alphabet_bound=A,
                observed_small_gaps=sorted(observed_gaps),top_orbit_alphabet_lower_bound=top_cost,
                outside_alphabet_bound=outside_bound,warmups=warmups,
                excluded_prefix_labels=sorted(forbidden),bad_groups=groups,
                hitting_set_budget=L,subset_searches=searches,max_subset_nodes=max_nodes,
                seconds=time.time()-start)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--cycle',type=int,default=4)
    ap.add_argument('--alphabet',type=int,default=32);ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    if args.verify:print('Verified synchronized observations:',verify());raise SystemExit
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    r=prove(messages,83,args.cycle,args.alphabet)
    (ROOT/('synchronized_bound_'+str(args.cycle)+'_'+str(args.alphabet)+'.json')).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps({k:v for k,v in r.items() if k!='bad_groups'},indent=2))
