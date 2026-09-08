"""Minimum relaxations of repeated-input assumptions for additive feedback.

Columns remove a whole shared-template slot. Occurrences instead let specific
input positions differ while all remaining copies of the slot still agree.
Minima concern forced linear collisions, not necessarily bijective keys.
"""
from pathlib import Path
import hashlib,itertools,json,random,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work'/'pydeps'))
import z3
from periodic_reset_screen import eliminate

def groups_from(equalities):
    parent={}
    def root(v):
        parent.setdefault(v,v)
        if parent[v]!=v:parent[v]=root(parent[v])
        return parent[v]
    for i,s,j,t,n in equalities:
        for d in range(n):
            a,b=root((i,s+d)),root((j,t+d));parent[b]=a
    groups={}
    for v in sorted(parent):groups.setdefault(root(v),[]).append(list(v))
    return sorted(groups.values())

class Problem:
    def __init__(self,messages,equalities,metric):
        self.messages=messages;self.groups=groups_from(equalities);self.metric=metric
        self.positions=sorted({tuple(p) for g in self.groups for p in g})
        self.units=self.groups if metric=='columns' else [list(p) for p in self.positions]
        index={p:i for i,p in enumerate(self.positions)}
        self.eqs=[];self.edges={}
        for gi,g in enumerate(self.groups):
            for a,b in itertools.combinations(g,2):
                if min(a[1],b[1])<2:raise ValueError('This audit requires internal body positions.')
                row=[0]*83
                for (mi,t),sgn in zip([a,b],[1,-1]):row[messages[mi][t]]+=sgn;row[messages[mi][t-1]]-=sgn
                self.edges[tuple(a),tuple(b)]=len(self.eqs)
                self.eqs.append(dict(positions=[a,b],row=[v%83 for v in row],units=[gi] if metric=='columns' else [index[tuple(a)],index[tuple(b)]]))
        self.pos_index=index

    def active(self,dropped):
        dropped=set(dropped);ids=[]
        for gi,g in enumerate(self.groups):
            if self.metric=='columns' and gi in dropped:continue
            good=g if self.metric=='columns' else [p for p in g if self.pos_index[tuple(p)] not in dropped]
            if good:
                for b in good[1:]:ids.append(self.edges[tuple(good[0]),tuple(b)])
        return ids

    def run_rows(self,ids):return eliminate([self.eqs[i]['row'] for i in ids])

    def proof(self,ids,r):
        # Greedily shrink a valid contradiction. Every retained subset remains
        # an actual set of equal-input constraints; no minimal-core claim.
        needed=[i for i,c in zip(ids,r['coefficients']) if c]
        for unit in sorted({u for i in needed for u in self.eqs[i]['units']}):
            trial=[i for i in needed if unit not in self.eqs[i]['units']]
            rr=self.run_rows(trial)
            if rr['status']=='forced_output_collision':
                ids=trial;r=rr;needed=[i for i,c in zip(ids,r['coefficients']) if c]
        terms=[[i,int(c)] for i,c in zip(ids,r['coefficients']) if c]
        units=sorted({u for i,c in terms for u in self.eqs[i]['units']})
        return dict(labels=r['labels'],terms=terms,units=units)

    def solve(self,max_seconds=90,max_iterations=2000,seed_proofs=(),column_lower_bound=0,z3_call_ms=5000,finite_domain=False):
        began=time.monotonic();flags=[z3.Bool('drop_'+str(i)) for i in range(len(self.units))]
        solver=z3.SolverFor('QF_FD') if finite_domain else z3.Solver()
        solver.set(timeout=z3_call_ms);proofs=[];k=column_lower_bound;iterations=0
        if column_lower_bound:
            assert self.metric=='occurrences'
            occupied=[z3.Or([flags[self.pos_index[tuple(p)]] for p in g]) for g in self.groups]
            solver.add(z3.PbGe([(b,1) for b in occupied],column_lower_bound))
        for old in seed_proofs:
            units=sorted({u for i,c in old['terms'] for u in self.eqs[i]['units']})
            proof=dict(labels=old['labels'],terms=old['terms'],units=units)
            proofs.append(proof);solver.add(z3.Or([flags[u] for u in units]))
        while time.monotonic()-began<max_seconds and iterations<max_iterations:
            bound=z3.PbLe([(f,1) for f in flags],k)
            if finite_domain:
                guard=z3.Bool('budget_'+str(k));solver.add(z3.Implies(guard,bound));check=solver.check(guard)
            else:check=solver.check(bound)
            if check==z3.unsat:k+=1;continue
            if check!=z3.sat:break
            model=solver.model();dropped=[i for i,f in enumerate(flags) if z3.is_true(model.eval(f,model_completion=True))]
            ids=self.active(dropped);r=self.run_rows(ids);iterations+=1
            if r['status']=='no_forced_collision':
                assert len(dropped)==k
                return dict(status='exact_minimum_for_no_forced_collision',metric=self.metric,units=self.units,groups=self.groups,
                    minimum=k,dropped=dropped,result=r,proofs=proofs,iterations=iterations,seed_proof_count=len(seed_proofs),
                    column_lower_bound=column_lower_bound,solver_kind='QF_FD' if finite_domain else 'default',limits=dict(seconds=max_seconds,iterations=max_iterations,z3_call_ms=z3_call_ms))
            proof=self.proof(ids,r);assert not set(dropped)&set(proof['units']);proofs.append(proof)
            solver.add(z3.Or([flags[u] for u in proof['units']]))
            if iterations%100==0:print(self.metric,'iterations',iterations,'lower bound',k,flush=True)
        return dict(status='bounded_search_incomplete',metric=self.metric,units=self.units,groups=self.groups,
                    lower_bound=k,proofs=proofs,iterations=iterations,seed_proof_count=len(seed_proofs),
                    column_lower_bound=column_lower_bound,solver_kind='QF_FD' if finite_domain else 'default',limits=dict(seconds=max_seconds,iterations=max_iterations,z3_call_ms=z3_call_ms))

def make_control(messages,seed,faults):
    rng=random.Random(seed);starts=[rng.randrange(3,25) for _ in messages]
    word=[rng.randrange(27) for _ in range(60)]
    plain=[[None]+[rng.randrange(27) for _ in m[1:]] for m in messages]
    for pt,s in zip(plain,starts):pt[s:s+60]=word
    corrupted=[]
    for mi,offset in [(1,10),(3,25),(5,40)][:faults]:
        t=starts[mi]+offset;old=plain[mi][t];plain[mi][t]=(old+1)%27
        corrupted.append(dict(position=[mi,t],offset=offset,original=old,replacement=plain[mi][t]))
    steps=rng.sample(range(1,83),27);perm=rng.sample(range(83),83);key=[perm.index(i) for i in range(83)]
    initials=[rng.randrange(83) for _ in messages];cipher=[]
    for state,pt in zip(initials,plain):
        ct=[rng.randrange(83)]
        for p in pt[1:]:state=(state+steps[p])%83;ct.append(perm[state])
        cipher.append(ct)
    eq=[[0,starts[0],i,starts[i],60] for i in range(1,9)]
    return dict(seed=seed,ciphertext=cipher,plaintext=plain,true_label_to_residue=key,input_steps=steps,
                initial_states=initials,equalities=eq,corrupted=corrupted,results={})

def main():
    raw=(ROOT/'ciphertext.json').read_bytes();parent=(ROOT/'state_memory_comparison.json').read_bytes()
    messages=list(json.loads(raw).values());assumptions=json.loads(parent)['assumption_sets']
    out=dict(status='Conditional equality-sensitivity audit; no Eye plaintext.',ciphertext_sha256=hashlib.sha256(raw).hexdigest(),
        parent_sha256=hashlib.sha256(parent).hexdigest(),z3_version=z3.get_version_string(),
        assumption_sets={name:assumptions[name] for name in ['early','late','strong']},real={},controls=[])
    def save():(ROOT/'equality_sensitivity.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    for name,eq in out['assumption_sets'].items():
        out['real'][name]={}
        for metric in ['columns','occurrences']:
            r=Problem(messages,eq,metric).solve();out['real'][name][metric]=r;save()
            print(name,metric,r['status'],'minimum/bound',r.get('minimum',r.get('lower_bound')),'iterations',r['iterations'],flush=True)
    for seed,faults in [(909700,2),(909701,3)]:
        c=make_control(messages,seed,faults);out['controls'].append(c)
        for metric in ['columns','occurrences']:
            r=Problem(c['ciphertext'],c['equalities'],metric).solve();c['results'][metric]=r;save()
            if 'normalized_label_to_residue' in r.get('result',{}):
                a,b=r['result']['anchor_labels'];key=c['true_label_to_residue'];scale=pow((key[b]-key[a])%83,-1,83)
                assert r['result']['normalized_label_to_residue']==[((v-key[a])*scale)%83 for v in key]
            print('Control',seed,metric,r['status'],r.get('minimum',r.get('lower_bound')),'recovered map','normalized_label_to_residue' in r.get('result',{}),flush=True)
    save()

def refine(finite_domain=False):
    raw=(ROOT/'equality_sensitivity.json').read_bytes();source=json.loads(raw)
    messages=list(json.loads((ROOT/'ciphertext.json').read_bytes()).values())
    p=Problem(messages,source['assumption_sets']['strong'],'occurrences')
    seeds=source['real']['strong']['columns']['proofs']+source['real']['strong']['occurrences']['proofs']
    r=p.solve(max_seconds=120,seed_proofs=seeds,column_lower_bound=source['real']['strong']['columns']['minimum'],z3_call_ms=20000,finite_domain=finite_domain)
    out=dict(parent_sha256=hashlib.sha256(raw).hexdigest(),description='Reuse verified column and occurrence contradictions to refine the joint occurrence bound.',result=r)
    name='equality_sensitivity_sat.json' if finite_domain else 'equality_sensitivity_refinement.json'
    (ROOT/name).write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    print('Joint occurrence refinement',r['status'],r.get('minimum',r.get('lower_bound')),'new iterations',r['iterations'],flush=True)

if __name__=='__main__':
    if '--sat' in sys.argv:refine(True)
    elif '--refine' in sys.argv:refine()
    else:main()
