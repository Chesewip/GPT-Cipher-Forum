"""Periodic arbitrary reset relaxation for relabeled additive feedback.

At reset outputs we discard the usual additive transition constraint. Thus
contradictions exclude a relaxation; survivors are not recovered Eye keys.
"""
from pathlib import Path
import json,hashlib,itertools,random
import numpy as np
from recurrence_transfer_audit import equations
ROOT=Path(__file__).resolve().parent

def eliminate(rows):
    matrix=np.asarray(rows,dtype=np.int64).reshape((-1,83));count=len(matrix)
    a=np.concatenate((matrix,np.eye(count,dtype=np.int64)),axis=1);pivots=[];r=0
    for col in range(83):
        choices=np.flatnonzero(a[r:,col])
        if not len(choices):continue
        chosen=r+int(choices[0]);a[[r,chosen]]=a[[chosen,r]]
        a[r]=a[r]*pow(int(a[r,col]),-1,83)%83
        mult=a[:,col].copy();mult[r]=0;a=(a-mult[:,None]*a[r])%83
        pivots.append(col);r+=1
    free=[j for j in range(83) if j not in pivots];kernel=np.zeros((83,len(free)),dtype=np.int64)
    kernel[free,np.arange(len(free))]=1
    if pivots:kernel[pivots,:]=-a[:r,free]%83
    seen={};pair=None
    for label,row in enumerate(kernel):
        signature=row.tobytes()
        if signature in seen:pair=[label,seen[signature]];break
        seen[signature]=label
    out=dict(rank=r,nullity=83-r)
    if pair:
        target=np.zeros(83,dtype=np.int64);target[pair[0]]=1;target[pair[1]]=82
        coefficients=np.zeros(count,dtype=np.int64)
        for i,p in enumerate(pivots):
            x=target[p];target=(target-x*a[i,:83])%83;coefficients=(coefficients+x*a[i,83:])%83
        assert not target.any()
        out.update(status='forced_output_collision',labels=pair,coefficients=coefficients.tolist())
    else:
        out['status']='no_forced_collision'
        active=[j for j in range(83) if matrix[:,j].any()];inactive=sorted(set(range(83))-set(active))
        out.update(active_nullity=len(active)-r,unconstrained_labels=inactive)
        if len(active)-r==2 and len(inactive)<=1:
            x,y=active[:2];column=next(j for j in range(kernel.shape[1]) if kernel[x,j]!=kernel[y,j]);v=kernel[:,column]
            inv=pow(int((v[y]-v[x])%83),-1,83)
            partial={j:int((v[j]-v[x])*inv%83) for j in active}
            if len(set(partial.values()))==len(active):
                unused=sorted(set(range(83))-set(partial.values()))
                key=[partial[j] if j in partial else unused[0] for j in range(83)]
                out.update(normalized_label_to_residue=key,anchor_labels=[x,y])
    return out

class Screen:
    def __init__(self,messages,equalities):
        self.eqs=equations(messages,equalities);self.rows=[e['row'] for e in self.eqs]
        self.proofs=[];self.masks=[];self.cache={}
    def active(self,period,phases):
        return [i for i,e in enumerate(self.eqs) if all((t-1-phases[mi])%period for mi,t in e['positions'])]
    def test(self,period,phases):
        active=self.active(period,phases);mask=sum(1<<i for i in active)
        if mask in self.cache:return self.cache[mask].copy()
        for i,needed in enumerate(self.masks):
            if mask&needed==needed:
                result=dict(status='forced_output_collision',proof_id=i,active_equations=len(active));self.cache[mask]=result;return result.copy()
        result=eliminate([self.rows[i] for i in active]);result['active_equations']=len(active)
        if result['status']=='forced_output_collision':
            coeff=result.pop('coefficients');terms=[[i,c] for i,c in zip(active,coeff) if c]
            proof=dict(labels=result.pop('labels'),terms=terms)
            result['proof_id']=len(self.proofs);self.proofs.append(proof);self.masks.append(sum(1<<i for i,c in terms))
        self.cache[mask]=result
        return result.copy()
    def export(self):
        return dict(equation_positions=[e['positions'] for e in self.eqs],proofs=self.proofs,distinct_active_equation_sets=len(self.cache))

def make_control(messages,seed,period,phase):
    rng=random.Random(seed);starts=[rng.randrange(2,25) for _ in messages];word=[rng.randrange(27) for _ in range(60)]
    eqs=[[0,starts[0],j,starts[j],60] for j in range(1,9)]
    steps=rng.sample(range(1,83),27);perm=rng.sample(range(83),83);key=[perm.index(j) for j in range(83)]
    ciphertext=[];plaintext=[];initial=[];resets=[]
    for mi,message in enumerate(messages):
        pt=[None]+[rng.randrange(27) for _ in message[1:]];pt[starts[mi]:starts[mi]+60]=word
        state=rng.randrange(83);initial.append(state);ct=[rng.randrange(83)];jumps=[]
        for t,p in enumerate(pt[1:],1):
            if (t-1-phase)%period==0:state=rng.randrange(83);jumps.append([t,state])
            state=(state+steps[p])%83;ct.append(perm[state])
        ciphertext.append(ct);plaintext.append(pt);resets.append(jumps)
    return dict(seed=seed,period=period,phase=phase,ciphertext=ciphertext,plaintext=plaintext,equalities=eqs,input_steps=steps,true_label_to_residue=key,initial_residues=initial,resets=resets)

def main():
    data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values());parent_bytes=(ROOT/'state_memory_comparison.json').read_bytes();parent=json.loads(parent_bytes)
    eqs=parent['assumption_sets']['strong'];screen=Screen(messages,eqs);limit=max(len(m)-1 for m in messages)
    out=dict(status='Conditional regular-reset test; no Eye plaintext or key.',ciphertext_sha256=hashlib.sha256(data).hexdigest(),parent_sha256=hashlib.sha256(parent_bytes).hexdigest(),equalities=eqs,period_limit=limit,common_schedule_cases=[],independent_phase_probes=[],controls=[])
    for period in range(1,limit+1):
        for phase in range(period):
            result=screen.test(period,[phase]*9);result.update(period=period,phase=phase);out['common_schedule_cases'].append(result)
        if period%20==0:print('Periods through',period,'proofs',len(screen.proofs),flush=True)
    # A bounded contrast only: stop after the first unresolved independent
    # phase vector or 1000 lexicographically ordered probes at each period.
    used=[1,2,6,7,8]
    for period in [4,7,13]:
        tried=[]
        for combo in itertools.islice(itertools.product(range(period),repeat=5),1000):
            phases=[0]*9
            for mi,p in zip(used,combo):phases[mi]=p
            r=screen.test(period,phases);r['phases']=phases;tried.append(r)
            if r['status']=='no_forced_collision':break
        out['independent_phase_probes'].append(dict(period=period,phase_messages=used,limit=1000,cases=tried))
        print('Independent phase',period,'trials',len(tried),'last',tried[-1]['status'],flush=True)
    out['real_certificates']=screen.export()
    for seed,period,phase in [(909500,7,2),(909501,11,5),(909502,17,3)]:
        c=make_control(messages,seed,period,phase);tester=Screen(c['ciphertext'],c['equalities']);cases=[]
        for b in range(1,33):
            for p in range(b):
                r=tester.test(b,[p]*9);r.update(period=b,phase=p);cases.append(r)
        c['cases']=cases;c['certificates']=tester.export();out['controls'].append(c)
        true=next(r for r in cases if (r['period'],r['phase'])==(period,phase));assert true['status']=='no_forced_collision'
        if 'normalized_label_to_residue' in true:
            a,b=true['anchor_labels'];scale=pow((c['true_label_to_residue'][b]-c['true_label_to_residue'][a])%83,-1,83)
            assert true['normalized_label_to_residue']==[((v-c['true_label_to_residue'][a])*scale)%83 for v in c['true_label_to_residue']]
        print('Control',seed,'survivors',[(r['period'],r['phase']) for r in cases if r['status']=='no_forced_collision'],'true map recovered','normalized_label_to_residue' in true,flush=True)
    (ROOT/'periodic_reset_screen.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    print('Real unresolved',[(r['period'],r['phase']) for r in out['common_schedule_cases'] if r['status']=='no_forced_collision'],flush=True)

if __name__=='__main__':main()
