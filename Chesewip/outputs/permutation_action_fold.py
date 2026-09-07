"""Necessary permutation-action consistency by folding inverse-prefix paths.

This is a standard partial permutation graph construction, not a new cipher.
Contradictions are exact; surviving graphs larger than the deck are unresolved.
"""
from pathlib import Path
from collections import deque
import json,random,time
ROOT=Path(__file__).resolve().parent

class Fold:
    def __init__(self):self.parent=[];self.adj=[];self.colour=[];self.queue=deque();self.failure=None
    def node(self):
        i=len(self.parent);self.parent.append(i);self.adj.append({});self.colour.append(None);return i
    def root(self,x):
        while self.parent[x]!=x:
            self.parent[x]=self.parent[self.parent[x]];x=self.parent[x]
        return x
    def edge(self,a,label,b):
        self.adj[a][label]=b;self.adj[b][-label]=a
    def merge(self,a,b):self.queue.append((a,b))
    def drain(self):
        while self.queue and self.failure is None:
            a,b=map(self.root,self.queue.popleft())
            if a==b:continue
            if len(self.adj[a])<len(self.adj[b]):a,b=b,a
            ca,cb=self.colour[a],self.colour[b]
            if ca is not None and cb is not None and ca!=cb:
                self.failure=[ca,cb];break
            self.parent[b]=a;self.colour[a]=ca if ca is not None else cb
            for label,target in self.adj[b].items():
                if label in self.adj[a]:self.merge(self.adj[a][label],target)
                else:self.adj[a][label]=target
            self.adj[b]={}

def solve(pts,cts,include_forced=False):
    alphabet={x:i+1 for i,x in enumerate(dict.fromkeys(x for p in pts for x in p))}
    f=Fold();top=f.node();endpoint={};observations=[]
    # Paths use inverse updates from the output point, in reverse time order.
    for mi,(pt,ct) in enumerate(zip(pts,cts)):
        assert len(pt)==len(ct)
        for t,c in enumerate(ct):
            node=top
            for token in reversed(pt[:t+1]):
                label=alphabet[token]
                if label not in f.adj[node]:
                    new=f.node();f.edge(node,label,new)
                node=f.adj[node][label]
            if f.colour[node] is not None and f.colour[node]!=c:
                return {'status':'contradiction','conflicting_cards':[f.colour[node],c]}
            f.colour[node]=c;observations.append((mi,t,c,node))
            if c in endpoint:f.merge(node,endpoint[c])
            else:endpoint[c]=node
    initial=len(f.parent);f.drain();roots=[i for i in range(initial) if f.root(i)==i]
    out={'status':'contradiction' if f.failure else 'relaxation_survives','initial_graph_nodes':initial,
         'folded_graph_nodes':len(roots),'plaintext_operation_classes':len(alphabet),'conflicting_cards':f.failure}
    if not f.failure:
        # Check every original observation and each surviving inverse edge.
        for mi,t,c,node in observations:assert f.colour[f.root(node)]==c
        for a in roots:
            for label,target in f.adj[a].items():
                b=f.root(target);assert f.root(f.adj[b][-label])==a
        out['folded_edges']=sum(len(f.adj[i]) for i in roots)//2
        if include_forced:
            by_source={};back={v:k for k,v in alphabet.items()};top=f.root(top)
            for label,target in f.adj[top].items():
                if label>0:by_source.setdefault(f.root(target),[]).append(back[label])
            out['forced_equal_operations']=[v for v in by_source.values() if len(v)>1]
            out['forced_fixed_output_operations']=by_source.get(top,[])
    return out

def make_plaintexts(messages,eq):
    parent={(i,t):(i,t) for i,m in enumerate(messages) for t in range(len(m))}
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for i,s,j,t,length in eq:
        for k in range(length):parent[root((i,s+k))]=root((j,t+k))
    return [[root((i,t)) for t in range(len(m))] for i,m in enumerate(messages)]

def controls():
    from plaintext_change_bounds import encrypt
    rng=random.Random(20261026);checked=0
    for n in [5,11,83]:
        for _ in range(50):
            perms=[]
            for k in range(4):
                q=list(range(n));rng.shuffle(q);perms.append(q)
            key=list(range(n));rng.shuffle(key)
            pts=[[rng.randrange(4) for _ in range(40)] for j in range(3)]
            cts=[encrypt(p,key,perms) for p in pts]
            assert solve(pts,cts)['status']=='relaxation_survives';checked+=1
    # One update repeated twice cannot both fix and move the output point.
    assert solve(['AAA'],[[1,1,2]])['status']=='contradiction'
    # Independently reproduce the published Waite fixed-point contradiction.
    quote='SUBLIME THAT WHICH IS THE LOWEST, AND MAKE THAT WHICH IS THE HIGHEST, THE LOWEST.'
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    waite=solve([quote],[raw[2][37:]])
    assert waite['status']=='contradiction'
    return {'valid_generated_fixtures':checked,'contradictory_repeated_letter_fixture':True,'waite_reproduction':waite}

if __name__=='__main__':
    from progressive_reduction import RUNS
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());prefixes=[]
    for i in range(len(raw)):
        for j in range(i):
            t=1
            while t<min(len(raw[i]),len(raw[j])) and raw[i][t]==raw[j][t]:t+=1
            if t>1:prefixes.append((i,1,j,1,t-1))
    out={'controls':controls(),'models':[]}
    for trim in [1,2,3]:
        for prefix in [False,True]:
            eq=[(i,s+trim,j,t+trim,n-trim) for i,s,j,t,n in RUNS]
            if prefix:eq+=prefixes
            started=time.time();r=solve(make_plaintexts(raw,eq),raw)
            r.update(trim=trim,assume_shared_prefixes=prefix,assumed_equalities=eq,seconds=time.time()-started)
            out['models'].append(r);print({k:v for k,v in r.items() if k!='assumed_equalities'},flush=True)
    out['warning']='Necessary arbitrary-degree action test. Survival does not establish an 83-card realization, small alphabet, reversibility, or meaningful text. Repeated-plaintext assumptions are conditional.'
    (ROOT/'permutation_action_fold.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
