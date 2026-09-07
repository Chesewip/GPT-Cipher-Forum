"""Key-free return-displacement relaxation for rotating unit-neighbor 3-cycles.

Between consecutive appearances of one card at r and t, its next input slot
is p[r+1]+1+(t-r-1)*b-k modulo n-1, where 0<=k<=t-r-2 counts predecessor hits.
This necessary interval omits the conditions determining individual hits.
"""
from pathlib import Path
import sys,json,time,argparse,random
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_three_cycle_scan import encrypt_physical

def graph(messages,pts):
    edges=[]
    for mi,(ct,pt) in enumerate(zip(messages,pts)):
        last={}
        for t,c in enumerate(ct):
            if c in last:
                r=last[c];gap=t-r
                if gap<2:return None
                edges.append((pt[r+1],pt[t],gap,mi,r,t))
            last[c]=t
    return edges

def solve(edges,M,b,timeout=2000):
    start=time.time();nodes=list(dict.fromkeys(x for e in edges for x in e[:2]));p={x:z3.Int('p_'+str(i)) for i,x in enumerate(nodes)}
    solver=z3.Solver();solver.set(timeout=timeout);solver.add(*(z3.And(v>=0,v<M) for v in p.values()))
    parents={x:x for x in nodes}
    def root(x):
        while parents[x]!=x:parents[x]=parents[parents[x]];x=parents[x]
        return x
    count=0
    for u,v,gap,*_ in edges:
        if gap-2>=M-1:continue
        parents[root(u)]=root(v);offset=(1+(gap-1)*b)%M;lo=offset-(gap-2);hi=offset;d=p[v]-p[u]
        choices=[]
        for k in [-1,0,1]:
            left=lo+k*M;right=hi+k*M
            if right>=-(M-1) and left<=M-1:choices.append(z3.And(d>=left,d<=right))
        solver.add(z3.Or(*choices));count+=1
    for x in {root(x) for x in nodes}:solver.add(p[x]==0)
    status=str(solver.check());out={'rotation':b,'status':status,'seconds':time.time()-start,'active_edges':count,'variables':len(nodes),'components':len({root(x) for x in nodes})}
    if status=='unknown':out['reason']=solver.reason_unknown()
    if status=='sat':
        m=solver.model();values={x:m.eval(v).as_long() for x,v in p.items()}
        assert all((1+(gap-1)*b-(values[v]-values[u]))%M<=gap-2 for u,v,gap,*_ in edges if gap-2<M-1)
    return out

def controls():
    rng=random.Random(20261102);results=[]
    for n in [7,19,83]:
        for trial in range(5):
            b=rng.randrange(n-1);key=rng.sample(list(range(n)),n);shared=[rng.randrange(1,n) for t in range(25)]
            pts=[[rng.randrange(1,n) for t in range(8)]+shared+[rng.randrange(1,n) for t in range(15)] for mi in range(3)]
            ct=[encrypt_physical(pt,key,1,b) for pt in pts];edges=graph(ct,pts)
            assert all((1+(gap-1)*b-(v-u))%(n-1)<=gap-2 for u,v,gap,*_ in edges)
            r=solve(edges,n-1,b,10000);assert r['status']=='sat',r;results.append(r)
    return results

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--trim',type=int,default=1);ap.add_argument('--timeout',type=int,default=2000);ap.add_argument('--controls',action='store_true');args=ap.parse_args()
    if args.controls:
        out={'controls':controls()};name='return_displacement_controls.json';print(out,flush=True)
    else:
        ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(ct,args.trim);pts=make_plaintexts(ct,eq);edges=graph(ct,pts);results=[]
        for b in range(82):
            r=solve(edges,82,b,args.timeout);results.append(r)
            if b%10==0 or r['status']!='sat':print(r,flush=True)
        out={'trim':args.trim,'assumed_equalities':eq,'results':results,'warning':'SAT is a return-displacement relaxation, not a key or plaintext. UNSAT is conditional on the specified repeated-plaintext assumptions.'};name=f'return_displacement_trim{args.trim}.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
