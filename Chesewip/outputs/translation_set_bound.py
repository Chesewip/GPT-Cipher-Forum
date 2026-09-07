"""Exact small-context bounds for arbitrary ciphertext-feedback translations.

Each predecessor chooses an arbitrary translation. Union size across a subset
of predecessor contexts lower-bounds any common plaintext residue alphabet.
"""
from pathlib import Path
from collections import defaultdict
import json,itertools,hashlib,time,random
ROOT=Path(__file__).resolve().parent
REPS=[(0,1)+p for p in itertools.permutations((2,3,4))]

def digits(x):return (x//25,(x//5)%5,x%5)
def number(v):return 25*v[0]+5*v[1]+v[2]
def add(a,b,group):
    if group=='xor128':return a^b
    if group=='quinary':return number(tuple((u+v)%5 for u,v in zip(digits(a),digits(b))))
    return (a+b)%int(group[1:])
def order(group):return 125 if group=='quinary' else 128 if group=='xor128' else int(group[1:])
def context_sets(messages,pi,reverse):
    sets=defaultdict(set);locations=defaultdict(list)
    for mi,row in enumerate(messages):
        indices=list(range(1,len(row)))
        if reverse:indices.reverse()
        for i,j in zip(indices,indices[1:]):
            sets[row[i]].add(number(tuple(pi[d] for d in digits(row[j]))))
            locations[row[i]].append([mi,i,j,row[j]])
    return sets,locations

def rotations(s,group):
    return [sum(1<<add(c,t,group) for c in s) for t in range(order(group))]

def optimize(sets,group):
    shifts=[rotations(s,group) for s in sets]
    best=order(group)+1;witness=None;nodes=[0]*len(sets)
    # One common translation is immaterial to support; fix the first to zero.
    u=shifts[0][0];greedy=[0]
    for r in shifts[1:]:
        j=min(range(len(r)),key=lambda j:(u|r[j]).bit_count());u|=r[j];greedy.append(j)
    best=u.bit_count();witness=greedy
    def walk(depth,u,ss):
        nonlocal best,witness
        nodes[depth-1]+=1
        if depth==len(shifts):best=u.bit_count();witness=ss;return
        choices=sorted(((u|v).bit_count(),j,u|v) for j,v in enumerate(shifts[depth]))
        for size,j,v in choices:
            if size>=best:break
            walk(depth+1,v,ss+[j])
    walk(1,shifts[0][0],[0])
    union=set()
    for s,t in zip(sets,witness):union.update(add(c,t,group) for c in s)
    assert len(union)==best
    return dict(exact_minimum_union=best,witness_translations=witness,
                witness_union=sorted(union),search_nodes_by_depth=nodes)

def controls():
    rng=random.Random(907310);out=[]
    for group in ['Z83','Z125','xor128','quinary']:
        n=order(group);alphabet=set(rng.sample(range(n),27));shifts=[rng.randrange(n) for _ in range(5)]
        # Each group observes the whole planted alphabet, so its minimum union
        # is exactly 27, independent of how the optimizer explores keys.
        sets=[{add(c,t,group) for c in alphabet} for t in shifts]
        r=optimize(sets,group);assert r['exact_minimum_union']==27
        out.append(dict(group=group,sets=[sorted(s) for s in sets],planted_alphabet=sorted(alphabet),planted_shifts=shifts,**r))
    # Small exact checks compare pruning with a separate full Cartesian product.
    small=0
    for group in ['Z3','Z5']:
        n=order(group)
        for _ in range(25):
            sets=[set(rng.sample(range(n),rng.randint(1,n))) for _ in range(4)]
            brute=min(len(set().union(*({add(c,t,group) for c in s} for s,t in zip(sets,(0,)+tail)))) for tail in itertools.product(range(n),repeat=3))
            assert optimize(sets,group)['exact_minimum_union']==brute;small+=1
    return out,small

def main():
    path=ROOT/'ciphertext.json';messages=list(json.loads(path.read_text(encoding='utf-8')).values())
    out=dict(status='Exact subset support bounds; cipher remains unsolved.',
             corpus_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
             model='C_t = P_t + F(C_(t-1)) in the stated group. F is any one shared keyed lookup table; P is any fixed plaintext-to-residue encoding.',
             first_symbol='Removed before forming adjacent body observations.',
             selection='Five contexts with most distinct successors; ties by canonical predecessor label.',cases=[])
    start=time.time();target=ROOT/'translation_set_bound.json'
    def save():target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    configs=[(g,REPS[0],r) for g in ['Z83','Z125','xor128'] for r in [False,True]]
    configs.extend(('quinary',p,r) for p in REPS for r in [False,True])
    for group,pi,reverse in configs:
        sets,locations=context_sets(messages,pi,reverse)
        keys=sorted(sets,key=lambda k:(-len(sets[k]),k))[:5]
        r=optimize([sets[k] for k in keys],group)
        r.update(group=group,direction_mapping=pi,reverse=reverse,context_labels=keys,
                 successor_sets=[sorted(sets[k]) for k in keys],observations=[locations[k] for k in keys])
        out['cases'].append(r);save()
        print(group,pi,'reverse',reverse,'bound',r['exact_minimum_union'],flush=True)
    out['controls'],out['small_exhaustive_control_count']=controls();out['seconds']=time.time()-start;save()

if __name__=='__main__':main()
