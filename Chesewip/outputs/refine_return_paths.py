"""Incremental return and non-return constraints, checked on complete known runs.

A local model fit proves an arbitrary starting deck exists separately for each
known run. It does not establish a common initial deck across messages.
"""
from pathlib import Path
import json,sys,time,argparse
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from permutation_action_fold import make_plaintexts
from shared_update_support import assumptions
from return_displacement import graph
from component_return_paths import components
from clocked_three_cycle_scan import encrypt_physical

class Engine:
    def __init__(self,ct,classes,vertices,b,n=83,timeout=5000,pinned=None):
        self.ct=ct;self.classes=classes;self.n=n;self.M=n-1;self.b=b;self.constraints=set();self.hits=0
        self.solver=z3.Solver();self.solver.set(timeout=timeout)
        self.p={x:z3.Int('p_'+str(i)) for i,x in enumerate(sorted(vertices))}
        self.solver.add(*(z3.And(v>=0,v<self.M) for v in self.p.values()))
        if pinned is None:self.solver.add(next(iter(self.p.values()))==0)
        else:
            for pt,cl in zip(pinned,classes):
                for v,x in zip(pt,cl):
                    if x in self.p:self.solver.add(self.p[x]==v-1)
    def add(self,mi,r,t,equal):
        tag=(mi,r,t,equal)
        if tag in self.constraints:return False
        assert not any(c==self.ct[mi][r] for c in self.ct[mi][r+1:t])
        assert (self.ct[mi][r]==self.ct[mi][t])==equal
        self.constraints.add(tag);edge=len(self.constraints);M=self.M;b=self.b;values=self.classes[mi]
        base=self.p[values[r+1]];count=z3.IntVal(0)
        for s in range(r+2,t):
            D=self.p[values[s]]-base-((s-r-1)*b%M)+count
            multiples=range(-2,3+(s-r)//M)
            self.solver.add(*(D!=1+k*M for k in multiples))
            hit=z3.Or(*[D==k*M for k in multiples]);nc=z3.Int(f'k_{edge}_{s}')
            self.solver.add(nc==count+z3.If(hit,1,0),nc>=0,nc<=s-r-1);count=nc;self.hits+=1
        D=self.p[values[t]]-base-((t-r-1)*b%M)+count
        choices=[D==1+k*M for k in range(-2,3+(t-r)//M)]
        self.solver.add(z3.Or(*choices) if equal else z3.Not(z3.Or(*choices)))
        return True
    def check(self):
        start=time.time();status=str(self.solver.check());result={'status':status,'seconds':time.time()-start,'constraints':len(self.constraints),'hit_steps':self.hits}
        if status=='unknown':result['reason']=self.solver.reason_unknown();return result,None
        if status=='unsat':return result,None
        m=self.solver.model();return result,{x:m.eval(v).as_long() for x,v in self.p.items()}

def runs(classes,vertices):
    out=[]
    for mi,cl in enumerate(classes):
        start=None
        for t in range(len(cl)+1):
            active=t<len(cl) and cl[t] in vertices
            if active and start is None:start=t
            if not active and start is not None:out.append((mi,start,t));start=None
    return out

def violations(ct,classes,assignment,blocks,b,n):
    out=[];M=n-1
    for mi,start,end in blocks:
        for r in range(max(0,start-1),end-2):
            u=(assignment[classes[mi][r+1]]+1+b)%M
            for t in range(r+2,end):
                p=assignment[classes[mi][t]];expected=ct[mi][r]==ct[mi][t];actual=p==u
                if expected!=actual:out.append((mi,r,t,expected));break
                if expected:break
                u=(u+b-int(p==(u-1)%M))%M
    return sorted(set(out),key=lambda x:(x[2]-x[1],x))

def local_keys(ct,classes,assignment,blocks,b,n):
    keys=[]
    for mi,start,end in blocks:
        slots=encrypt_physical([assignment[x]+1 for x in classes[mi][start:end]],range(n),1,b)
        pairs=list(zip(slots,ct[mi][start:end]))
        if start>0:pairs.insert(0,(0,ct[mi][start-1]))
        f={};g={}
        for slot,card in pairs:
            if (slot in f and f[slot]!=card) or (card in g and g[card]!=slot):return None
            f[slot]=card;g[card]=slot
        deck=[None]*n
        for slot,card in f.items():deck[slot]=card
        unused=iter(x for x in range(n) if x not in g)
        deck=[next(unused) if x is None else x for x in deck]
        assert encrypt_physical([assignment[x]+1 for x in classes[mi][start:end]],deck,1,b)==ct[mi][start:end]
        keys.append({'message':mi,'start':start,'end':end,'deck_at_run_start':deck})
    return keys

def refine(ct,classes,edges,b,n=83,timeout=5000,rounds=12,batch=12,pinned=None,warm=None):
    vertices={x for _,_,_,mi,r,t in edges for x in classes[mi][r+1:t+1]};blocks=runs(classes,vertices)
    engine=Engine(ct,classes,vertices,b,n,timeout,pinned)
    for _,_,_,mi,r,t in edges:engine.add(mi,r,t,True)
    if warm:
        for x,v in engine.p.items():
            if x in warm:engine.solver.set_initial_value(v,z3.IntVal(warm[x]))
    history=[];start=time.time();out=None
    for iteration in range(rounds):
        r,assignment=engine.check();r['round']=iteration
        if assignment is None:history.append(r);out={'status':r['status']};break
        errors=violations(ct,classes,assignment,blocks,b,n);r['violations']=len(errors);history.append(r)
        print(r,flush=True)
        if not errors:
            keys=local_keys(ct,classes,assignment,blocks,b,n);assert keys is not None
            out={'status':'local_model_fit','selector_assignment':[[x,v] for x,v in assignment.items()],'local_keys':keys};break
        new=0
        for mi,r0,t,equal in errors:
            if engine.add(mi,r0,t,equal):new+=1
            if new>=batch:break
        assert new>0
    if out is None:out={'status':'round_limit'}
    out.update(history=history,seconds=time.time()-start,vertices=len(vertices),initial_returns=len(edges),runs=blocks,
               added_constraints=[list(x) for x in sorted(engine.constraints)],warning='A local model fit has separate starting decks per run; it is not a common key or plaintext.')
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--gap',type=int,default=20);ap.add_argument('--component',type=int,default=0);ap.add_argument('--timeout',type=int,default=5000);ap.add_argument('--rounds',type=int,default=12);args=ap.parse_args()
    ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(ct);cl=make_plaintexts(ct,eq);groups=components(cl,[e for e in graph(ct,cl) if e[2]<=args.gap])
    r=refine(ct,cl,groups[args.component],9,timeout=args.timeout,rounds=args.rounds);r.update(component=args.component,gap=args.gap,rotation=9,assumed_equalities=eq)
    (ROOT/f'refined_returns_{args.gap}_{args.component}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in r.items() if k not in ['history','selector_assignment','local_keys','runs','assumed_equalities','added_constraints']},flush=True)
