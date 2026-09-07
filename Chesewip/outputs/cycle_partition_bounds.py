"""Safe cycle-alphabet bounds using pair supports and proper graph coloring.
An L-cycle needs L labels whose shifted time supports all fit into its plaintext
alphabet. Pair incompatibilities make a graph; those labels must form a clique.
A proper coloring with fewer than L colors proves such a cycle impossible.
"""
from pathlib import Path
import json,argparse,time,random
from progressive_reduction import deswap
ROOT=Path(__file__).resolve().parent

def proper_color_count(vertices,neighbors,order):
    colors=[]
    for v in order:
        for k,group in enumerate(colors):
            if not neighbors[v]&group:
                colors[k]|=1<<v;break
        else:colors.append(1<<v)
    return len(colors)

def cycle_cost(messages,n,top,L):
    labels=[i for i in range(n) if i!=top];lookup={c:i for i,c in enumerate(labels)}
    rows=[0]*(n-1);mask=(1<<L)-1
    for m in messages:
        for t,b in enumerate(deswap(m,top,n)):
            if b==top:
                assert t==0;continue
            rows[lookup[b]] |= 1<<(t%L)
    sizes=[x.bit_count() for x in rows]
    rotations=[[(r<<d|r>>(L-d))&mask for d in range(1,L)] for r in rows]
    pair={}
    for i in range(n-1):
        for j in range(i+1,n-1):
            overlap=max((rows[i]&r).bit_count() for r in rotations[j]) if L>1 else 0
            pair[i,j]=sizes[i]+sizes[j]-overlap
    certificates=[]
    for alphabet in range(1,L+1):
        vertices=[i for i in range(n-1) if sizes[i]<=alphabet]
        if len(vertices)<L:
            certificates.append(dict(alphabet=alphabet,eligible_labels=len(vertices),color_upper_bound=len(vertices)))
            continue
        neighbors=[0]*(n-1)
        for k,i in enumerate(vertices):
            for j in vertices[k+1:]:
                if pair[min(i,j),max(i,j)]<=alphabet:
                    neighbors[i]|=1<<j;neighbors[j]|=1<<i
        order=sorted(vertices,key=lambda i:neighbors[i].bit_count(),reverse=True)
        upper=proper_color_count(vertices,neighbors,order)
        # Each proper coloring gives a valid upper bound; keep the tightest.
        for seed in range(3):
            trial=vertices[:];random.Random(seed).shuffle(trial)
            upper=min(upper,proper_color_count(vertices,neighbors,trial))
        certificates.append(dict(alphabet=alphabet,eligible_labels=len(vertices),color_upper_bound=upper))
        if upper>=L:
            return dict(top=top,cycle_length=L,cycle_alphabet_lower_bound=alphabet,certificates=certificates)
    raise AssertionError('The full cycle alphabet must be feasible in the relaxation')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--length',type=int,default=41);args=ap.parse_args()
    m=list(json.loads((ROOT/'ciphertext.json').read_text()).values());start=time.time()
    results=[cycle_cost(m,83,top,args.length) for top in range(83)]
    (ROOT/('cycle_partition_bound_'+str(args.length)+'.json')).write_text(json.dumps(dict(seconds=time.time()-start,results=results),indent=2)+'\n',encoding='utf-8',newline='\r\n')
    bounds=[x['cycle_alphabet_lower_bound'] for x in results]
    print('Cycle',args.length,'alphabet lower bounds:',min(bounds),'to',max(bounds),'seconds',time.time()-start)
