import json,sys,collections
sys.path.insert(0,'outputs')
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from return_displacement import graph
ct=list(json.load(open('outputs/ciphertext.json')).values());pts=make_plaintexts(ct,assumptions(ct));edges=graph(ct,pts)
for limit in [4,6,8,12,10000]:
    parent={x:x for pt in pts for x in pt}
    def root(x):
        if parent[x]!=x:parent[x]=root(parent[x])
        return parent[x]
    selected=[e for e in edges if e[2]<=limit];used=set()
    for _,_,_,mi,r,t in selected:
        vs=pts[mi][r+1:t+1];used.update(vs)
        for v in vs:parent[root(v)]=root(vs[0])
    c=collections.Counter(root(x) for x in used)
    print(limit,sorted(c.values(),reverse=True)[:12])
