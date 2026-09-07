"""Key-free mismatch lower bounds for small relative plaintext shuffles.

Let weight(R)=(n-number_of_odd_cycles(R))/2. Multiplication by a permutation
of support <=2b+1 changes this weight by at most b. After k plaintext
mismatches, weight of the relative state permutation is <=b*k. A partial
bijection with nontrivial path/cycle component sizes v requires weight at
least sum(floor(v/2)). These bounds require no guessed repeated plaintext.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent

def partial_weight(f):
    adj={}
    for x,y in f.items():
        if x!=y:
            adj.setdefault(x,set()).add(y);adj.setdefault(y,set()).add(x)
    seen=set();answer=0
    for x in adj:
        if x in seen:continue
        stack=[x];seen.add(x);size=0
        while stack:
            v=stack.pop();size+=1
            for w in adj[v]:
                if w not in seen:seen.add(w);stack.append(w)
        answer+=size//2
    return answer

def segment_table(a,b):
    n=min(len(a),len(b));segments={}
    for left in range(n):
        f={};g={}
        for right in range(left,n):
            x,y=a[right],b[right]
            if (x in f and f[x]!=y) or (y in g and g[y]!=x):break
            f[x]=y;g[y]=x;segments[left,right+1]=partial_weight(f)
    return segments

def bound(a,b,budget):
    assert a[0]!=b[0]  # All real message pairs satisfy this.
    n=min(len(a),len(b));segments=segment_table(a,b)
    reachable=[{} for _ in range(n+1)];reachable[0][0]=None
    for left in range(n):
        for right in range(left+1,n+1):
            if (left,right) not in segments:break
            needed=segments[left,right]
            for old in reachable[left]:
                count=old+1
                if needed<=budget*count and count not in reachable[right]:reachable[right][count]=(left,old)
    count=min(reachable[n]);parts=[];end=n;k=count
    while end:
        left,old=reachable[end][k];parts.append([left,end,segments[left,end],k]);end=left;k=old
    return {'minimum_plaintext_differences':count,'one_relaxed_partition':list(reversed(parts)),
            'relative_shuffle_weight_budget':budget}

if __name__=='__main__':
    ms=list(json.loads((ROOT/'ciphertext.json').read_text()).values());results=[]
    for length in [29,37,50,99]:
        r={'prefix_length':length,'bounds':[bound(ms[0][:length],ms[1][:length],budget) for budget in [1,2,41]]}
        results.append(r);print(length,[(x['relative_shuffle_weight_budget'],x['minimum_plaintext_differences']) for x in r['bounds']])
    (ROOT/'shuffle_weight_bounds.json').write_text(json.dumps({'east1_west1':results},indent=2)+'\n',encoding='utf-8',newline='\r\n')
