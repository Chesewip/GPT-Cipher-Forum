"""Compare table selection by position or observed ciphertext history.

Fits are deliberately engineered token encodings, never plaintext recovery.
Repeated-plaintext hypotheses are kept separate from ciphertext-only cases.
"""
from pathlib import Path
from collections import defaultdict, Counter, deque
import itertools, json, random, hashlib

ROOT=Path(__file__).resolve().parent
EARLY=[(1,37,1,67,15),(2,42,2,77,15),(1,37,2,42,15),(1,37,2,77,15)]
WEAK=[(0,43,0,71,6)]
LATE=[(6,71,7,74,27),(6,71,8,72,27)]

class Union:
    def __init__(self,n):self.parent=list(range(n));self.adj=[[] for _ in range(n)]
    def root(self,x):
        while self.parent[x]!=x:
            self.parent[x]=self.parent[self.parent[x]];x=self.parent[x]
        return x
    def join(self,a,b,why):
        self.adj[a].append((b,why));self.adj[b].append((a,why))
        a,b=self.root(a),self.root(b)
        if a!=b:self.parent[max(a,b)]=min(a,b)
    def path(self,a,b):
        seen={a:None};queue=deque([a])
        while b not in seen:
            v=queue.popleft()
            for w,why in self.adj[v]:
                if w not in seen:seen[w]=(v,why);queue.append(w)
        path=[];v=b
        while seen[v] is not None:
            previous,why=seen[v];path.append(dict(from_node=previous,to_node=v,positions=why));v=previous
        return path[::-1]

def prefix_assumptions(messages):
    result=[]
    for i,j in itertools.combinations(range(len(messages)),2):
        n=0
        while n+1<min(len(messages[i]),len(messages[j])) and messages[i][n+1]==messages[j][n+1]:n+=1
        if n:result.append((i,1,j,1,n))
    return result

def start_at(model):
    return 1 if model['kind'] in ('fixed','position') else model['memory']+int(model['header']=='metadata')

def context(message,t,model):
    kind=model['kind'];k=model['memory']
    if kind=='fixed':return ()
    if kind=='position':return (t,)
    if kind=='window':return tuple(message[t-k:t])
    if kind=='lag':return (message[t-k],)
    raise ValueError(kind)

def observations(messages,model):
    start=start_at(model)
    raw={(i,t):(context(m,t,model),m[t]) for i,m in enumerate(messages) for t in range(start,len(m))}
    nodes=sorted(set(raw.values()));index={v:i for i,v in enumerate(nodes)}
    return nodes,{pos:index[node] for pos,node in raw.items()}

def fit(messages,model,equalities,state_permutations=False):
    nodes,positions=observations(messages,model);u=Union(len(nodes));used=skipped=0
    for ei,(i,s,j,t,n) in enumerate(equalities):
        for k in range(n):
            a,b=(i,s+k),(j,t+k)
            if a not in positions or b not in positions:skipped+=1;continue
            u.join(positions[a],positions[b],[list(a),list(b)]);used+=1
    groups=defaultdict(list)
    for v,(ctx,c) in enumerate(nodes):
        groups[('table',ctx)].append(v)
        if state_permutations:groups[('target',c)].append(v)
    graph={u.root(v):set() for v in range(len(nodes))}
    out=dict(model=model,observed_nodes=len(nodes),compared_positions=len(positions),used_equalities=used,skipped_equalities=skipped,
             row_degree_lower_bound=max(sum(node[0]==ctx for node in nodes) for ctx in {n[0] for n in nodes}),state_permutations=state_permutations)
    for group,vs in sorted(groups.items()):
        seen={}
        for v in vs:
            r=u.root(v)
            if r in seen:
                out.update(status='contradiction',collision_nodes=[seen[r],v],collision_group=[group[0],group[1]],path=u.path(seen[r],v));return out
            seen[r]=v
        roots=set(seen)
        for r in roots:graph[r].update(roots-{r})
    # DSATUR constructs an upper bound, not a proof that this many colors
    # are necessary. A matching row-degree bound does prove optimality.
    colors={};saturation={v:set() for v in graph}
    while len(colors)<len(graph):
        v=max((v for v in graph if v not in colors),key=lambda v:(len(saturation[v]),len(graph[v]),v))
        c=0
        while c in saturation[v]:c+=1
        colors[v]=c
        for w in graph[v]:saturation[w].add(c)
    out.update(status='constructed_token_fit',tokens=max(colors.values())+1,node_tokens=[colors[u.root(v)] for v in range(len(nodes))])
    return out

def complete_permutations(messages,equalities,header):
    model=dict(kind='window',memory=1,header=header)
    fitted=fit(messages,model,equalities,True);assert fitted['status']=='constructed_token_fit'
    nodes,positions=observations(messages,model);k=fitted['tokens'];maps=[{} for _ in range(k)]
    used={(ctx[0],c) for ctx,c in nodes}
    for ((a,),b),token in zip(nodes,fitted['node_tokens']):maps[token][a]=b
    for color,mp in enumerate(maps):
        rows=[a for a in range(83) if a not in mp];cols=set(range(83))-set(mp.values());matching={}
        def augment(a,seen):
            for b in sorted(cols):
                if a==b or (a,b) in used or b in seen:continue
                seen.add(b)
                if b not in matching or augment(matching[b],seen):matching[b]=a;return True
            return False
        assert all(augment(a,set()) for a in rows)
        for b,a in matching.items():mp[a]=b;used.add((a,b))
    key=[[mp[a] for a in range(83)] for mp in maps]
    assert all(sorted(mp)==list(range(83)) and all(a!=b for a,b in enumerate(mp)) for mp in key)
    assert all(len({mp[a] for mp in key})==k for a in range(83))
    initial=[m[0] for m in messages] if header=='primer' else [key[0].index(messages[0][1])]*len(messages)
    tokens=[]
    for state,m in zip(initial,messages):
        plain=[]
        for c in m[1:]:
            choices=[p for p in range(k) if key[p][state]==c];assert len(choices)==1
            plain.append(choices[0]);state=c
        tokens.append(plain)
    for i,s,j,t,n in equalities:assert tokens[i][s-1:s-1+n]==tokens[j][t-1:t-1+n]
    return dict(status='Engineered nonlinguistic full-body fit, not a Noita key.',model=model,alphabet_size=k,key=key,initial_states=initial,body_tokens=tokens,
                equalities=equalities,lower_bound=fitted['row_degree_lower_bound'],observed_edges=len(nodes))

def pattern(seq):
    seen={};out=[]
    for v in seq:
        if v not in seen:seen[v]=len(seen)
        out.append(seen[v])
    return tuple(out)

def transfer(key,word):
    all_outputs=[]
    for initial in range(83):
        state=initial;seq=[]
        for p in word:state=key[p][state];seq.append(state)
        all_outputs.append(seq)
    return dict(word=word,output_from_every_state=all_outputs,pattern_counts=[dict(pattern=list(p),count=n) for p,n in sorted(Counter(map(pattern,all_outputs)).items())])

def generated_control(messages,model,seed,equalities):
    rng=random.Random(seed);positions=[(i,t) for i,m in enumerate(messages) for t in range(1,len(m))];idx={v:i for i,v in enumerate(positions)};u=Union(len(idx))
    for i,s,j,t,n in equalities:
        for d in range(n):u.join(idx[i,s+d],idx[j,t+d],None)
    labels={u.root(v):rng.randrange(27) for v in range(len(idx))};truth=[[None]+[labels[u.root(idx[i,t])] for t in range(1,len(m))] for i,m in enumerate(messages)]
    ciphertext=[];tables={};start=start_at(model)
    for i,m in enumerate(messages):
        c=[rng.randrange(83) for _ in range(start)]
        for t in range(start,len(m)):
            ctx=context(c,t,model)
            if ctx not in tables:tables[ctx]=rng.sample(range(83),27)
            c.append(tables[ctx][truth[i][t]])
        ciphertext.append(c)
    result=fit(ciphertext,model,equalities)
    assert result['status']=='constructed_token_fit'
    return dict(seed=seed,model=model,plaintext=truth,ciphertext=ciphertext,tables=[dict(context=list(ctx),outputs=values) for ctx,values in sorted(tables.items())],equalities=equalities,result=result)

def main():
    data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values());prefix=prefix_assumptions(messages)
    sets=dict(none=[],early=EARLY,late=LATE,strong=EARLY+LATE,full=EARLY+WEAK+LATE,prefix=prefix,late_prefix=LATE+prefix,full_prefix=EARLY+WEAK+LATE+prefix)
    models=[dict(kind=kind,memory=0,header='metadata') for kind in ('fixed','position')]
    models += [dict(kind=kind,memory=k,header=h) for kind,ks in [('window',range(1,5)),('lag',range(2,13))] for k in ks for h in ('primer','metadata')]
    out=dict(status='Observed-state model comparison; no decipherment.',ciphertext_sha256=hashlib.sha256(data).hexdigest(),message_names=list(json.loads(data)),assumption_sets=sets,cases=[],controls=[])
    for model in models:
        for name,eq in sets.items():
            r=fit(messages,model,eq);r['assumption_set']=name;out['cases'].append(r)
        print('Compared',model,flush=True)
    for i,model in enumerate([models[0],models[1],dict(kind='window',memory=1,header='primer'),dict(kind='window',memory=2,header='metadata'),dict(kind='lag',memory=4,header='metadata')]):
        out['controls'].append(generated_control(messages,model,909300+i,sets['full_prefix']))
    engineered=[]
    for header,name in [('primer','full'),('metadata','full_prefix')]:
        witness=complete_permutations(messages,sets[name],header);witness['assumption_set']=name;witness['transfers']=[]
        for mi,start,n in [(1,37,15),(6,71,27)]:
            word=witness['body_tokens'][mi][start-1:start-1+n]
            check=transfer(witness['key'],word);check['source']=[mi,start,n];check['observed_pattern']=list(pattern(messages[mi][start:start+n]))
            witness['transfers'].append(check)
        engineered.append(witness)
    rng=random.Random(909310);steps=rng.sample(range(1,83),19);cyclic=[[(state+step)%83 for state in range(83)] for step in steps]
    cyclic_checks=[transfer(cyclic,w['word']) for w in engineered[1]['transfers']]
    assert all(len(c['pattern_counts'])==1 for c in cyclic_checks)
    out['engineered_fits']=engineered;out['cyclic_transfer_control']=dict(seed=909310,steps=steps,key=cyclic,checks=cyclic_checks)
    # A two-step window can distinguish the very pair contexts responsible
    # for the one-step primer contradiction; save the raw locations directly.
    out['header_sensitive_locations']=[dict(message=i,position=t,three_labels=messages[i][max(0,t-2):t+1]) for i,t in [(1,1),(5,1),(6,77),(7,80),(8,78)]]
    path=ROOT/'state_memory_comparison.json';path.write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    print('Saved',len(out['cases']),'cases; engineered alphabets',[w['alphabet_size'] for w in engineered])
    for w in engineered:print(w['model'],'transfer pattern counts',[len(c['pattern_counts']) for c in w['transfers']])

if __name__=='__main__':main()
