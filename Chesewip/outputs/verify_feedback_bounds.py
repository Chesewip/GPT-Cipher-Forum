"""Independent verification of translation-union and quinary matrix bounds.

Does not import either discovery script. Translation lower bounds use a
breadth-first set of feasible partial unions, with a fixed bound rather than
an incumbent-driven depth-first optimizer. Matrix scores use unnormalized
pair differences, without projective representatives.
"""
from pathlib import Path
from collections import Counter,defaultdict
import itertools,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parent

def vec(x):return np.array([(x//25)%5,(x//5)%5,x%5],dtype=np.int64)
V=np.array([vec(i) for i in range(125)])

def plus(a,b,group):
    if group=='xor128':return a^b
    if group=='quinary':
        u=vec(a);v=vec(b);w=(u+v)%5
        return int(25*w[0]+5*w[1]+w[2])
    return (a+b)%int(group[1:])

def verify_union(case):
    group=case['group'];n=125 if group=='quinary' else 128 if group=='xor128' else int(group[1:])
    sets=case.get('successor_sets',case.get('sets'));k=case['exact_minimum_union']
    shifted=[]
    for s in sets:
        shifted.append([frozenset(plus(c,t,group) for c in s) for t in range(n)])
    chosen=set().union(*(r[t] for r,t in zip(shifted,case['witness_translations'])))
    assert len(chosen)==k and sorted(chosen)==case['witness_union']
    # A full solution with union smaller than k would retain every partial
    # union below k. Exhaust all such distinct partial unions, no greedy order.
    states={shifted[0][0]} if len(shifted[0][0])<k else set()
    counts=[len(states)]
    for r in shifted[1:]:
        states={u|v for u in states for v in r if len(u|v)<k}
        counts.append(len(states))
    assert not states
    return counts


def raw_pair_table(x,y):
    # Difference orientation is kept, including every nonzero vector separately.
    table=np.zeros((125,125),dtype=np.int64)
    for i in range(len(x)):
        dx=(x[i+1:]-x[i])%5;dy=(y[i+1:]-y[i])%5
        xc=dx[:,0]*25+dx[:,1]*5+dx[:,2]
        yc=dy[:,0]*25+dy[:,1]*5+dy[:,2]
        table+=np.bincount(125*xc+yc,minlength=15625).reshape(125,125)
    assert int(table.sum())==len(x)*(len(x)-1)//2
    return table


def verify_matrix(case,messages):
    pi=np.array(case['direction_mapping']);x=[];y=[]
    for m in messages:
        d=pi[V[m[1:]]];x.extend(d[:-1]);y.extend(d[1:])
    x=np.array(x);y=np.array(y);table=raw_pair_table(x,y)
    scores=np.full((125,125,125),int(table[0,0]),dtype=np.int64)
    for d in range(1,125):
        dots=(V@V[d])%5
        # Directly consult all 124 unnormalized previous-difference vectors.
        codes=25*dots[:,None,None]+5*dots[None,:,None]+dots[None,None,:]
        scores+=table[d,codes]
    maximum=int(scores.max());n=len(x)
    hist=Counter(map(int,scores.ravel()))
    assert {int(k):v for k,v in case['collision_score_histogram'].items()}==hist
    assert maximum==case['maximum_collision_pairs']
    def floor_pairs(k):
        q,r=divmod(n,k);return (k-r)*q*(q-1)//2+r*(q+1)*q//2
    bound=next(k for k in range(1,126) if floor_pairs(k)<=maximum)
    assert bound==case['universal_support_lower_bound']
    a=np.array(case['first_maximizing_matrix']);res=(y-x@a.T)%5
    counts=Counter(map(tuple,res));assert len(counts)==case['maximizer_support']
    assert sum(v*(v-1)//2 for v in counts.values())==maximum
    if 'planted_plaintext' in case:
        r=(y-x@np.array(case['matrix']).T)%5
        assert (25*r[:,0]+5*r[:,1]+r[:,2]).tolist()==case['planted_plaintext']
        assert len(set(case['planted_plaintext']))==27 and bound<=27
    return dict(maximum_collision_pairs=maximum,universal_support_lower_bound=bound)


def main():
    raw=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(raw).values())
    source=json.loads((ROOT/'translation_set_bound.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(raw).hexdigest()==source['corpus_sha256']
    out=dict(status='Independently verified; cipher remains unsolved.',translation_cases=[])
    for case in source['cases']:
        pi=case['direction_mapping'];sets=defaultdict(set);loc=defaultdict(list)
        for mi,row in enumerate(messages):
            ix=list(range(1,len(row)))
            if case['reverse']:ix.reverse()
            for i,j in zip(ix,ix[1:]):
                v=vec(row[j]);w=[pi[int(z)] for z in v];sets[row[i]].add(25*w[0]+5*w[1]+w[2]);loc[row[i]].append([mi,i,j,row[j]])
        keys=sorted(sets,key=lambda k:(-len(sets[k]),k))[:5]
        assert keys==case['context_labels']
        assert [sorted(sets[k]) for k in keys]==case['successor_sets']
        assert [loc[k] for k in keys]==case['observations']
        states=verify_union(case)
        out['translation_cases'].append(dict(group=case['group'],direction_mapping=pi,reverse=case['reverse'],exact_subset_minimum=case['exact_minimum_union'],feasible_partial_unions_below_bound=states))
    for control in source['controls']:
        for shift,s in zip(control['planted_shifts'],control['sets']):
            assert sorted(plus(c,shift,control['group']) for c in control['planted_alphabet'])==s
        assert control['exact_minimum_union']==27
        verify_union(control)
    out['translation_generated_controls']=len(source['controls'])
    # Verify the six affine orbits of all 120 direction permutations exactly.
    reps=set();permutations=0
    for pi in itertools.permutations(range(5)):
        scale=(pi[1]-pi[0])%5;inv=pow(scale,-1,5)
        norm=tuple(((c-pi[0])*inv)%5 for c in pi);reps.add(norm)
        assert all((scale*norm[i]+pi[0])%5==pi[i] for i in range(5));permutations+=1
    assert len(reps)==6
    out['direction_permutations_partitioned']=permutations;out['affine_direction_orbits']=6
    q=json.loads((ROOT/'quinary_feedback_screen.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(raw).hexdigest()==q['corpus_sha256']
    assert set(tuple(c['direction_mapping']) for c in q['cases'])==reps
    out['matrix_cases']=[]
    for i,case in enumerate(q['cases']):
        out['matrix_cases'].append(verify_matrix(case,messages));print('Independent matrix case',i+1,'passed',flush=True)
    for i,case in enumerate(q['controls']):
        verify_matrix(case,case['ciphertext']);print('Independent matrix control',i+1,'passed',flush=True)
    out['real_matrices_checked']=len(q['cases'])*125**3
    out['matrix_controls_checked']=len(q['controls'])
    out['scope']='Bounds on encoded plaintext support in stated common-feedback models, not universal cipher exclusions.'
    (ROOT/'checked_feedback_bounds.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ['translation_cases','matrix_cases']},indent=2))

if __name__=='__main__':main()
