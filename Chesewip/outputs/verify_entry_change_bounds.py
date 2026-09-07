"""Independent checks of entry-change bounds and their cipher-model scope."""
from pathlib import Path
import json,itertools,random,math
import numpy as np
from entry_change_bounds import row_costs,bound
ROOT=Path(__file__).resolve().parent

def dynamic_rows(a,b,n,common):
    total=0;values=[]
    for x in range(n):
        costs=[0 if not common or y==x else 10**6 for y in range(n)]
        for ca,cb in zip(a,b):
            m=min(costs)+1
            costs=[min(costs[y],m) if ((y==cb)==(x==ca)) else 10**6 for y in range(n)]
        values.append(min(costs));total+=min(costs)
    return total,values

def encrypt_pair(pts,keys,perms):
    states=[];cts=[]
    for pt,key in zip(pts,keys):
        deck=key.copy();ct=[];trace=[]
        for token in pt:
            new=[None]*len(deck)
            for old,dest in enumerate(perms[token]):new[dest]=deck[old]
            deck=new;ct.append(deck[0]);trace.append(deck.copy())
        cts.append(ct);states.append(trace)
    return cts,states

rng=random.Random(20261030);dp_checks=0
for n in [3,5,11,83]:
    for common in [False,True]:
        for _ in range(50):
            a=[rng.randrange(n) for t in range(40)];b=[rng.randrange(n) for t in range(40)]
            fast=row_costs(a,b,n,common);slow,rows=dynamic_rows(a,b,n,common)
            assert slow==fast['minimum_total_entry_changes'] and rows==[r['minimum_entry_changes'] for r in fast['rows']];dp_checks+=1

# Exhaustive global permutation-state optimization; row relaxation must be a bound.
global_checks=0
for n in [3,4,5]:
    perms=np.array(list(itertools.permutations(range(n))));distance=np.count_nonzero(perms[:,None,:]!=perms[None,:,:],axis=2)
    for _ in range(20):
        a=[rng.randrange(n) for t in range(8)];b=[rng.randrange(n) for t in range(8)];cost=np.count_nonzero(perms!=np.arange(n),axis=1)
        cost=np.where(perms[:,a[0]]==b[0],cost,10**6)
        for ca,cb in zip(a[1:],b[1:]):cost=np.where(perms[:,ca]==cb,np.min(cost[:,None]+distance,axis=0),10**6)
        r=bound(a,b,n);assert max(r['forward_entry_change_bound'],r['inverse_entry_change_bound'])<=int(min(cost));global_checks+=1

# Generated shared-base shuffle ciphers, both swaps and arbitrary anchored 3-cycles.
fixtures=0;shape_counts={}
for n in [7,19,83]:
    for support in [3,5]:
        for common in [True,False]:
            for _ in range(25):
                q=[0]+rng.sample(list(range(1,n)),n-1);perms=[]
                for p in range(1,min(n,28)):
                    s=list(range(n))
                    if support==3:s[0],s[p]=p,0
                    else:
                        tail=rng.choice([x for x in range(1,n) if x!=p]);s[0]=tail;s[p]=0;s[tail]=p
                    perms.append([q[s[x]] for x in range(n)])
                key=rng.sample(list(range(n)),n);other=key.copy() if common else rng.sample(list(range(n)),n)
                a=[rng.randrange(len(perms)) for t in range(100)];b=a.copy()
                for t in rng.sample(range(100),rng.randrange(1,40)):b[t]=rng.randrange(len(perms))
                cts,states=encrypt_pair([a,b],[key,other],perms)
                r=bound(*cts,n,common);actual=sum(x!=y for x,y in zip(a,b));computed=r['minimum_plaintext_differences_by_relative_support'][str(support)]
                assert computed<=actual
                previous=[None]*n
                for x,y in zip(key,other):previous[x]=y
                total=0
                for t,(da,db) in enumerate(zip(*states)):
                    rel=[None]*n
                    for x,y in zip(da,db):rel[x]=y
                    changed=sum(x!=y for x,y in zip(previous,rel));assert changed<=support and (a[t]!=b[t] or changed==0)
                    total+=changed;previous=rel
                assert max(r['forward_entry_change_bound'],r['inverse_entry_change_bound'])<=total;fixtures+=1

# Independently classify every distinct pair of unit-neighbor selections.
n=83;updates=[]
for p in range(1,n):
    tail=1+p%(n-1);s=list(range(n));s[0]=tail;s[p]=0;s[tail]=p;updates.append(s)
for i,a in enumerate(updates):
    for j,b in enumerate(updates):
        if i==j:continue
        inv=[b.index(x) for x in range(n)];relative=[inv[a[x]] for x in range(n)];seen=set();sizes=[]
        for x in range(n):
            if x in seen:continue
            size=0;y=x
            while y not in seen:seen.add(y);size+=1;y=relative[y]
            if size>1:sizes.append(size)
        shape=','.join(map(str,sorted(sizes)));assert shape in ['2,2','5'];shape_counts[shape]=shape_counts.get(shape,0)+1
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());verified=[]
for r in json.loads((ROOT/'entry_change_bounds.json').read_text())['focus']:
    N=r['length'];f,rows=dynamic_rows(raw[0][:N],raw[1][:N],83,True);v,_=dynamic_rows(raw[1][:N],raw[0][:N],83,True)
    assert f==r['forward_entry_change_bound'] and v==r['inverse_entry_change_bound'];verified.append({'length':N,'forward':f,'inverse':v})
out={'independent_row_dynamic_programs':dp_checks,'exhaustive_global_permutation_optimizations':global_checks,'generated_small_update_cipher_fixtures':fixtures,'unit_neighbor_distinct_selection_pair_types':shape_counts,'real_prefix_bounds_independently_verified':verified,'status':'All checks passed. Bounds are necessary, not plaintext recovery.'}
(ROOT/'checked_entry_change_bounds.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(out)
