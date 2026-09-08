"""Bounded unknown-permutation feedback candidates with a fixed fitting split.

No late-passage data enters key/codebook selection. Repair controls are marked
separately from blind recovery. No positive decipherment is assumed.
"""
from pathlib import Path
import hashlib,itertools,json,math,random
import numpy as np
from homophonic_language_probe import clean,ALPHABET
ROOT=Path(__file__).resolve().parent
TRAIN=list(range(6));TEST=[6,7,8]

def table(name):
    if name=='add':return np.arange(83,dtype=np.int64)
    if name=='square':return np.array([x*x%83 for x in range(83)],dtype=np.int64)
    if name=='inverse':return np.array([pow(x,-1,83) if x else 0 for x in range(83)],dtype=np.int64)
    raise ValueError(name)

class Fit:
    def __init__(self,messages,early,name,weight):
        self.f=table(name);self.allowed=np.array(sorted(set(range(83))-{(x-int(self.f[x]))%83 for x in range(83)}),dtype=np.int64)
        assert len(self.allowed)>=27
        self.positions=[(mi,t) for mi in TRAIN for t in range(2,len(messages[mi]))]
        self.current=np.array([messages[i][t] for i,t in self.positions]);self.previous=np.array([messages[i][t-1] for i,t in self.positions])
        index={p:i for i,p in enumerate(self.positions)}
        self.left=np.array([index[i,s+d] for i,s,j,t,n in early for d in range(n)])
        self.right=np.array([index[j,t+d] for i,s,j,t,n in early for d in range(n)])
        self.weight=weight
    def score(self,key,details=False):
        residual=(key[self.current]-self.f[key[self.previous]])%83
        counts=np.bincount(residual,minlength=83)
        code=self.allowed[np.lexsort((self.allowed,-counts[self.allowed]))[:27]]
        outside=int(len(residual)-counts[code].sum());mismatch=int(np.count_nonzero(residual[self.left]!=residual[self.right]))
        energy=outside+self.weight*mismatch
        if details:return dict(energy=energy,outside_codebook=outside,early_pair_mismatches=mismatch,
            distinct_residuals=int(np.count_nonzero(counts)),codebook=sorted(code.tolist()),scored_transitions=len(residual))
        return energy

def attack(messages,early,name,weight,seed,initial=None,restarts=4,steps=6000):
    fit=Fit(messages,early,name,weight);rng=random.Random(seed);records=[]
    for restart in range(restarts):
        key=np.array(initial if initial is not None else rng.sample(range(83),83),dtype=np.int64)
        start_key=key.tolist();score=fit.score(key);best=score;best_key=key.copy();best_step=-1
        for step in range(steps):
            a,b=rng.sample(range(83),2);key[a],key[b]=key[b],key[a];candidate=fit.score(key)
            temperature=0.05+2.95*(1-step/steps)**2
            if candidate<=score or rng.random()<math.exp((score-candidate)/temperature):score=candidate
            else:key[a],key[b]=key[b],key[a]
            if score<best:best=score;best_key=key.copy();best_step=step
        # A deterministic one-swap descent starts from the retained best map.
        key=best_key.copy();score=best
        for a,b in itertools.combinations(range(83),2):
            key[a],key[b]=key[b],key[a];candidate=fit.score(key)
            if candidate<score:score=candidate
            else:key[a],key[b]=key[b],key[a]
        records.append(dict(restart=restart,initial_key=start_key,key=key.tolist(),training=fit.score(key,True),annealing_best_step=best_step))
    selected=min(range(len(records)),key=lambda i:records[i]['training']['energy'])
    return dict(name=name,equality_weight=weight,seed=seed,restarts=restarts,steps=steps,
        initial_mode='two_swap_repair' if initial is not None else 'blind_random_permutation',
        selected_restart=selected,runs=records,key=records[selected]['key'],codebook=records[selected]['training']['codebook'],
        allowed_code_values=fit.allowed.tolist(),training=records[selected]['training'])

def evaluate(messages,late,candidate):
    key=candidate['key'];f=table(candidate['name']);code=set(candidate['codebook'])
    decoded=[[None,None]+[(key[m[t]]-int(f[key[m[t-1]]]))%83 for t in range(2,len(m))] for m in messages]
    values=[decoded[i][t] for i in TEST for t in range(2,len(messages[i]))]
    checks=[[i,s+d,j,t+d] for i,s,j,t,n in late for d in range(n)]
    return dict(outside_frozen_codebook=sum(v not in code for v in values),transitions=len(values),
        late_pair_mismatches=sum(decoded[i][s]!=decoded[j][t] for i,s,j,t in checks),late_comparisons=len(checks),
        distinct_residuals=len(set(values)),decoded_residues=decoded)

def fixture(messages,early,late,name,seed,text):
    rng=random.Random(seed);plain=[]
    for m in messages:
        start=rng.randrange(len(text)-len(m));plain.append([None]+[ALPHABET.index(c) for c in text[start:start+len(m)-1]])
    # Ensure all 27 code values can be learned from the fitting split.
    plain[0][2:29]=list(range(27))
    for eqs in [early,late]:
        for i,s,j,t,n in eqs:plain[j][t:t+n]=plain[i][s:s+n]
    f=table(name);allowed=sorted(set(range(83))-{(x-int(f[x]))%83 for x in range(83)})
    steps=rng.sample(allowed,27);permutation=rng.sample(range(83),83);key=[permutation.index(v) for v in range(83)]
    initials=[rng.randrange(83) for _ in messages];cipher=[]
    for state,pt in zip(initials,plain):
        ct=[rng.randrange(83)]
        for p in pt[1:]:state=(int(f[state])+steps[p])%83;ct.append(permutation[state])
        cipher.append(ct)
    damaged=key.copy();swaps=[rng.sample(range(83),2) for _ in range(2)]
    for a,b in swaps:damaged[a],damaged[b]=damaged[b],damaged[a]
    return dict(name=name,seed=seed,ciphertext=cipher,plaintext=plain,true_key=key,input_codebook=steps,
        initial_states=initials,repair_start=damaged,repair_swaps=swaps,searches=[])

def main():
    raw=(ROOT/'ciphertext.json').read_bytes();parent=(ROOT/'state_memory_comparison.json').read_bytes()
    messages=list(json.loads(raw).values());sets=json.loads(parent)['assumption_sets'];early=sets['early'];late=sets['late']
    source=ROOT.parent/'work'/'pg1661.txt';text=clean(source)
    out=dict(status='Frozen candidate-generation pilot; no Eye decipherment.',executed_date='2026-09-08',
        ciphertext_sha256=hashlib.sha256(raw).hexdigest(),parent_sha256=hashlib.sha256(parent).hexdigest(),
        control_text_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),training_messages=TRAIN,heldout_messages=TEST,
        early_equalities=early,late_equalities=late,controls=[],eye=[])
    def save():(ROOT/'frozen_candidate_search.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    for index,name in enumerate(['add','square','inverse']):
        c=fixture(messages,early,late,name,909800+index,text);out['controls'].append(c)
        for mode in ['repair','blind']:
            r=attack(c['ciphertext'],early,name,3,909810+index*2+(mode=='blind'),
                initial=c['repair_start'] if mode=='repair' else None,restarts=1 if mode=='repair' else 4)
            r['heldout']=evaluate(c['ciphertext'],late,r)
            truth=np.array(c['true_key']);r['true_key_training']=Fit(c['ciphertext'],early,name,3).score(truth,True)
            r['literal_key_matches']=sum(a==b for a,b in zip(r['key'],c['true_key']))
            c['searches'].append(r);save()
            print('Control',name,mode,'energy',r['training']['energy'],'heldout outside',r['heldout']['outside_frozen_codebook'],'key matches',r['literal_key_matches'],flush=True)
    for index,name in enumerate(['add','square','inverse']):
        for weight in [0,3]:
            r=attack(messages,early,name,weight,909830+index*2+(weight>0));r['heldout']=evaluate(messages,late,r);out['eye'].append(r);save()
            print('Eyes',name,weight,'energy',r['training']['energy'],'train outside',r['training']['outside_codebook'],'heldout outside',r['heldout']['outside_frozen_codebook'],'late mismatches',r['heldout']['late_pair_mismatches'],flush=True)
    save()

if __name__=='__main__':main()
