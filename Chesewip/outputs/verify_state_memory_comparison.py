"""Independent replay of observed-state constraints and engineered models.

Standard library only; no discovery modules imported. Fit witnesses are
checked by direct table consistency, contradictions by equality paths.
"""
from pathlib import Path
from collections import Counter,defaultdict
import itertools,json,hashlib
ROOT=Path(__file__).resolve().parent

def inventory(messages,model):
    observations={}
    for i,message in enumerate(messages):
        for t,c in enumerate(message):
            if t==0:continue
            kind=model['kind'];k=model['memory']
            if kind=='fixed':ctx=()
            elif kind=='position':ctx=(t,)
            else:
                if t-k<int(model['header']=='metadata'):continue
                ctx=tuple(message[j] for j in (range(t-k,t) if kind=='window' else [t-k]))
            observations[i,t]=(ctx,c)
    nodes=sorted(set(observations.values()));ids={node:i for i,node in enumerate(nodes)}
    return nodes,{pos:ids[node] for pos,node in observations.items()}

def expanded(equalities):
    return [(tuple((i,s+k)),tuple((j,t+k))) for i,s,j,t,n in equalities for k in range(n)]

def check_case(messages,equalities,case):
    nodes,positions=inventory(messages,case['model']);pairs=expanded(equalities)
    usable=[(a,b) for a,b in pairs if a in positions and b in positions]
    assert len(nodes)==case['observed_nodes'] and len(positions)==case['compared_positions']
    assert len(usable)==case['used_equalities'] and len(pairs)-len(usable)==case['skipped_equalities']
    by_context=defaultdict(list)
    for n,(ctx,c) in enumerate(nodes):by_context[ctx].append(n)
    assert max(map(len,by_context.values()))==case['row_degree_lower_bound']
    if case['status']=='constructed_token_fit':
        colors=case['node_tokens'];assert len(colors)==len(nodes)
        assert set(colors)==set(range(case['tokens'])) and case['tokens']<=83
        for vs in by_context.values():assert len(set(colors[v] for v in vs))==len(vs)
        for a,b in usable:assert colors[positions[a]]==colors[positions[b]]
        # Construct partial encryption tables and replay every observation.
        enc={(ctx,colors[v]):c for v,(ctx,c) in enumerate(nodes)}
        assert len(enc)==len(nodes)
        for pos,v in positions.items():assert enc[nodes[v][0],colors[v]]==messages[pos[0]][pos[1]]
        return 'fit',0
    assert case['status']=='contradiction'
    a,b=case['collision_nodes'];assert a!=b and nodes[a][0]==nodes[b][0] and nodes[a][1]!=nodes[b][1]
    allowed={frozenset((p,q)) for p,q in usable};current=a
    for step in case['path']:
        assert step['from_node']==current
        p,q=map(tuple,step['positions']);assert frozenset((p,q)) in allowed
        assert {positions[p],positions[q]}=={step['from_node'],step['to_node']}
        current=step['to_node']
    assert current==b
    return 'contradiction',len(case['path'])

def equal_pattern(seq):
    # Pairwise equality matrix, independent of discovery's first-occurrence
    # canonical numbering.
    return tuple(seq[i]==seq[j] for i in range(len(seq)) for j in range(i))

def replay_transfer(key,record):
    actual=[]
    for initial in range(83):
        sequence=[];state=initial
        for token in record['word']:
            state=key[token][state];sequence.append(state)
        actual.append(sequence)
    assert actual==record['output_from_every_state']
    counts=Counter(map(equal_pattern,actual))
    saved={equal_pattern(r['pattern']):r['count'] for r in record['pattern_counts']}
    assert len(saved)==len(record['pattern_counts']) and counts==saved
    return counts

def main():
    data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values())
    raw=(ROOT/'state_memory_comparison.json').read_bytes();source=json.loads(raw)
    assert source['ciphertext_sha256']==hashlib.sha256(data).hexdigest()
    sets=source['assumption_sets'];prefix=[]
    for i,j in itertools.combinations(range(9),2):
        stop=1
        while stop<min(len(messages[i]),len(messages[j])) and messages[i][stop]==messages[j][stop]:stop+=1
        if stop>1:prefix.append([i,1,j,1,stop-1])
    assert prefix==sets['prefix']
    early=[[1,37,1,67,15],[2,42,2,77,15],[1,37,2,42,15],[1,37,2,77,15]]
    late=[[6,71,7,74,27],[6,71,8,72,27]];weak=[[0,43,0,71,6]]
    assert sets==dict(none=[],early=early,late=late,strong=early+late,full=early+weak+late,prefix=prefix,late_prefix=late+prefix,full_prefix=early+weak+late+prefix)
    expected={('fixed',0,'metadata'),('position',0,'metadata')}
    expected.update((kind,k,h) for kind,ks in [('window',range(1,5)),('lag',range(2,13))] for k in ks for h in ('primer','metadata'))
    observed=set();counts=Counter();steps=0;summary=[]
    for case in source['cases']:
        m=case['model'];identity=(m['kind'],m['memory'],m['header'],case['assumption_set']);assert identity not in observed;observed.add(identity)
        status,n=check_case(messages,sets[case['assumption_set']],case);counts[status]+=1;steps+=n
        if status=='fit':assert case['tokens']==case['row_degree_lower_bound']
        if case['assumption_set'] in ('none','full','late_prefix','full_prefix'):
            summary.append(dict(model=m,assumptions=case['assumption_set'],status=status,tokens=case.get('tokens'),lower_bound=case['row_degree_lower_bound'],skipped_equalities=case['skipped_equalities']))
    assert observed=={(*model,name) for model in expected for name in sets}
    for c in source['controls']:
        assert c['equalities']==sets['full_prefix']
        status,_=check_case(c['ciphertext'],c['equalities'],c['result']);assert status=='fit'
        tables={tuple(r['context']):r['outputs'] for r in c['tables']};assert all(len(t)==len(set(t))==27 and all(0<=v<83 for v in t) for t in tables.values())
        nodes,positions=inventory(c['ciphertext'],c['model'])
        for (mi,t),n in positions.items():
            ctx,output=nodes[n];assert tables[ctx][c['plaintext'][mi][t]]==output
        for a,b in expanded(c['equalities']):assert c['plaintext'][a[0]][a[1]]==c['plaintext'][b[0]][b[1]]
    fits=[]
    for witness in source['engineered_fits']:
        k=witness['alphabet_size'];key=witness['key'];assert k==len(key)==19
        assert all(sorted(row)==list(range(83)) and all(a!=b for a,b in enumerate(row)) for row in key)
        assert all(len({key[p][state] for p in range(k)})==k for state in range(83))
        assert witness['equalities']==sets[witness['assumption_set']]
        if witness['model']['header']=='metadata':assert len(set(witness['initial_states']))==1
        else:assert witness['initial_states']==[m[0] for m in messages]
        for mi,message in enumerate(messages):
            state=witness['initial_states'][mi];decoded=[]
            assert len(witness['body_tokens'][mi])==len(message)-1
            for c,p in zip(message[1:],witness['body_tokens'][mi]):
                assert key[p][state]==c
                choices=[q for q in range(k) if key[q][state]==c];assert choices==[p]
                decoded.append(p);state=c
        for a,b in expanded(witness['equalities']):assert witness['body_tokens'][a[0]][a[1]-1]==witness['body_tokens'][b[0]][b[1]-1]
        nodes,_=inventory(messages,witness['model']);degrees=Counter(ctx for ctx,c in nodes)
        assert len(nodes)==witness['observed_edges'] and max(degrees.values())==witness['lower_bound']==19
        transfers=[]
        for r in witness['transfers']:
            mi,start,n=r['source'];assert r['word']==witness['body_tokens'][mi][start-1:start-1+n]
            counts2=replay_transfer(key,r);target=equal_pattern(messages[mi][start:start+n])
            assert target==equal_pattern(r['observed_pattern'])
            transfers.append(dict(source=r['source'],distinct_patterns=len(counts2),states_matching_observed_pattern=counts2[target]))
        fits.append(dict(header=witness['model']['header'],tokens=k,body_symbols=sum(len(m)-1 for m in messages),state_transitions_checked=83*k,transfers=transfers))
    control=source['cyclic_transfer_control'];assert len(set(control['steps']))==19 and all(0<s<83 for s in control['steps'])
    assert control['key']==[[(state+step)%83 for state in range(83)] for step in control['steps']]
    for r in control['checks']:assert len(replay_transfer(control['key'],r))==1
    # Compact primer-sensitive contradiction, independently stated without
    # using the general search certificate or its transitive closure.
    assert messages[1][0:2]==[80,66] and messages[5][0:2]==[34,66]
    assert messages[6][76:78]==[43,60] and messages[7][79:81]==[34,66] and messages[8][77:79]==[80,25]
    assert [6,71,7,74,27] in late and [6,71,8,72,27] in late
    assert any(i==1 and j==5 and s==t==1 and n>=1 for i,s,j,t,n in prefix)
    out=dict(status='Independent checks passed; no authentic plaintext or key recovered.',ciphertext_sha256=hashlib.sha256(data).hexdigest(),source_sha256=hashlib.sha256(raw).hexdigest(),cases=len(source['cases']),results=dict(counts),conditional_path_steps=steps,generated_controls=len(source['controls']),engineered_fits=fits,compact_header_sensitive_certificate=True,selected_case_summary=summary)
    (ROOT/'checked_state_memory_comparison.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps({k:v for k,v in out.items() if k!='selected_case_summary'},indent=2))

if __name__=='__main__':main()
