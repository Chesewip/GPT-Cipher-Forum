"""Exact return-path constraints using linear integer differences and hit counts."""
from pathlib import Path
import sys,json,time,argparse,collections
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from return_displacement import graph
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts

def solve(ct,classes,b,n=83,gap_limit=12,timeout=3000,pinned=None,edge_subset=None,eliminate_free=False,warm=None):
    M=n-1;start=time.time();edges=graph(ct,classes) if edge_subset is None else edge_subset;edges=[e for e in edges if e[2]<=gap_limit]
    used=list(dict.fromkeys(x for _,_,_,mi,r,t in edges for x in classes[mi][r+1:t+1]))
    occurrences=collections.Counter(x for _,_,_,mi,r,t in edges for x in classes[mi][r+1:t+1])
    endpoints={x for u,v,*_ in edges for x in [u,v]}
    free={x for x,c in occurrences.items() if c==1 and x not in endpoints} if eliminate_free and pinned is None else set()
    p={x:z3.Int('p_'+str(i)) for i,x in enumerate(used) if x not in free};parent={x:x for x in used if x not in free}
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    solver=z3.Solver();solver.set(timeout=timeout);solver.add(*(z3.And(v>=0,v<M) for v in p.values()))
    steps=0
    for edge_id,(_,_,gap,mi,r,t) in enumerate(edges):
        values=classes[mi];base=p[values[r+1]];count=z3.IntVal(0)
        for s in range(r+2,t):
            if values[s] in free:
                next_count=z3.Int(f'k_{edge_id}_{s}')
                solver.add(next_count>=count,next_count<=count+1);count=next_count;steps+=1
                continue
            parent[root(values[s])]=root(values[r+1]);D=p[values[s]]-base-((s-r-1)*b%M)+count
            # D lies in [-2M+2, M-1+(s-r-2)]. Enumerate only relevant congruences.
            multiples=range(-2,3+(s-r)//M)
            solver.add(*(D!=1+k*M for k in multiples))
            hit=z3.Or(*[D==k*M for k in multiples]);next_count=z3.Int(f'k_{edge_id}_{s}')
            solver.add(next_count==count+z3.If(hit,1,0),next_count>=0,next_count<=s-r-1);count=next_count;steps+=1
        parent[root(values[t])]=root(values[r+1]);D=p[values[t]]-base-((gap-1)*b%M)+count
        solver.add(z3.Or(*[D==1+k*M for k in range(-2,3+gap//M)]))
    if pinned is None:
        for x in {root(x) for x in parent}:solver.add(p[x]==0)
    else:
        for pt,cl in zip(pinned,classes):
            for value,x in zip(pt,cl):
                if x in p:solver.add(p[x]==value-1)
    if warm:
        for x,v in p.items():
            if x in warm:solver.set_initial_value(v,z3.IntVal(warm[x]))
    status=str(solver.check());out={'rotation':b,'gap_limit':gap_limit,'status':status,'seconds':time.time()-start,'return_intervals':len(edges),'hit_steps':steps,'variables':len(p),'components':len({root(x) for x in parent}),'eliminated_free_selectors':len(free)}
    if status=='unknown':out['reason']=solver.reason_unknown()
    if status=='sat':
        model=solver.model();selection={x:model.eval(v).as_long() for x,v in p.items()}
        # Replay actual tracked-card positions independently of the hit-count encoding.
        for edge_id,(_,_,_,mi,r,t) in enumerate(edges):
            vals=classes[mi];u=(selection[vals[r+1]]+1+b)%M
            for s in range(r+2,t):
                if vals[s] in free:
                    previous=0 if s==r+2 else model.eval(z3.Int(f'k_{edge_id}_{s-1}')).as_long()
                    now=model.eval(z3.Int(f'k_{edge_id}_{s}')).as_long()
                    selection[vals[s]]=(u-1)%M if now>previous else (u+1)%M
                v=selection[vals[s]];assert v!=u
                u=(u+b-int(v==(u-1)%M))%M
            assert selection[vals[t]]==u
        out['selector_assignment']=[[x,v] for x,v in selection.items()]
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--gap',type=int,default=12);ap.add_argument('--timeout',type=int,default=3000);ap.add_argument('--rotations',nargs='*',type=int,default=[0,1,9,17,41,81]);args=ap.parse_args()
    ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(ct);classes=make_plaintexts(ct,eq);results=[]
    for b in args.rotations:
        r=solve(ct,classes,b,gap_limit=args.gap,timeout=args.timeout);results.append(r);print({k:v for k,v in r.items() if k!='selector_assignment'},flush=True)
    (ROOT/f'integer_returns_{args.gap}.json').write_text(json.dumps({'results':results,'assumed_equalities':eq,'warning':'Exact selected return paths, no initial-key constraints. SAT is a relaxation.'},indent=2)+'\n',encoding='utf-8',newline='\r\n')
