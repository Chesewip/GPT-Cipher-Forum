"""Conditional constraints from repeated internal plaintext transitions."""
from pathlib import Path
import json,math,sys
from synchronized_cycle_bound import reduction
from progressive_reduction import RUNS
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3

def top_selections(messages,L):
    out=[]
    for m in messages:
        w=next(t for t in range(L,len(m)+1) if len(set(m[t-L:t]))==L)
        orbit=list(reversed(m[w-L:w]));known={}
        for t in range(w,len(m)):
            c=m[t];anchor=orbit[-1]
            j=orbit.index(c) if c in orbit else None;known[t]=j
            if j is not None:orbit[j]=anchor
            orbit[-1]=c;orbit=[orbit[-1]]+orbit[:-1]
        out.append(known)
    return out

def invalid_component(edges,deleted,n):
    adj={}
    for u,v,d in edges:
        if u in deleted or v in deleted:continue
        adj.setdefault(u,[]).append((v,d));adj.setdefault(v,[]).append((u,-d))
    pot={}
    for root in adj:
        if root in pot:continue
        pot[root]=0;stack=[root];vertices=[];g=0
        while stack:
            u=stack.pop();vertices.append(u)
            for v,d in adj[u]:
                if v not in pot:pot[v]=pot[u]+d;stack.append(v)
                else:g=math.gcd(g,pot[u]+d-pot[v])
        allowed=[M for M in range(len(vertices),n+1) if (not g or g%M==0) and len({pot[v]%M for v in vertices})==len(vertices)]
        if not allowed:return vertices
    return None

def test(messages,L,runs=None):
    eq=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in (RUNS if runs is None else runs)]
    top=top_selections(messages,L)
    for i,s,j,t,n in eq:
        for k in range(n):
            if s+k in top[i] and t+k in top[j] and top[i][s+k]!=top[j][t+k]:
                return dict(top_cycle=L,status='excluded_conditionally',reason='incompatible_known_top_cycle_selections',
                            positions=[[i,s+k],[j,t+k]],selections=[top[i][s+k],top[j][t+k]])
    rows,F,ws,obs=reduction(messages,83,L);lookup={(mi,t):b for mi,t,b in obs};edges=[]
    for i,s,j,t,n in eq:
        for k in range(n):
            a=lookup.get((i,s+k));b=lookup.get((j,t+k))
            if a is not None and b is not None and a not in F and b not in F:edges.append((a,b,s-t))
    labels=set(u for u,v,d in edges)|set(v for u,v,d in edges)
    deleted={b:z3.Bool('omit_'+str(b)) for b in labels}
    solver=z3.Solver();solver.add(z3.AtMost(*deleted.values(),L));groups=[]
    for iteration in range(1000):
        answer=solver.check()
        if answer==z3.unsat:return dict(top_cycle=L,status='excluded_conditionally',reason='incompatible_reduced_permutation',bad_groups=groups,edges=edges)
        if answer!=z3.sat:break
        model=solver.model();omit={b for b in labels if z3.is_true(model.eval(deleted[b]))}
        group=invalid_component(edges,omit,83-L)
        if group is None:return dict(top_cycle=L,status='relaxation_survives',omitted_labels=sorted(omit),bad_groups=groups,edges=edges)
        for b in group[:]:
            trial=[c for c in group if c!=b]
            if invalid_component(edges,labels-set(trial),83-L) is not None:group=trial
        groups.append(group);solver.add(z3.Or(*[deleted[b] for b in group]))
    return dict(top_cycle=L,status='inconclusive',bad_groups=groups,edges=edges)

if __name__=='__main__':
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    results=[test(messages,L) for L in range(1,9)]
    (ROOT/'synchronized_isomorph_results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    for r in results:print({k:v for k,v in r.items() if k not in ['bad_groups','edges']},'groups',len(r.get('bad_groups',[])))
