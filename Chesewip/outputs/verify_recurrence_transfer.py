"""Independent checks of loop obstructions and cyclic-map calibration.

No discovery modules imported. Reverse-column Gauss-Jordan elimination and
kernel coordinate signatures check rank and forced collisions independently.
"""
from pathlib import Path
from collections import defaultdict,Counter
import itertools,json,hashlib,math
ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()

def relation(messages,a,b):
    row=[0]*83
    for (mi,t),sign in [(a,1),(b,-1)]:
        row[messages[mi][t]]+=sign;row[messages[mi][t-1]]-=sign
    return [v%83 for v in row]
def constraints(messages,eqs):
    return [relation(messages,(i,s+d),(j,t+d)) for i,s,j,t,n in eqs for d in range(n) if min(s+d,t+d)>=2]
def kernel(rows):
    matrix=[r.copy() for r in rows if any(r)];pivots=[];r=0
    for col in reversed(range(83)):
        pivot=next((i for i in range(r,len(matrix)) if matrix[i][col]),None)
        if pivot is None:continue
        matrix[r],matrix[pivot]=matrix[pivot],matrix[r]
        inv=pow(matrix[r][col],-1,83);matrix[r]=[(x*inv)%83 for x in matrix[r]]
        for i in range(len(matrix)):
            if i==r:continue
            mult=matrix[i][col]
            if mult:matrix[i]=[(x-mult*y)%83 for x,y in zip(matrix[i],matrix[r])]
        pivots.append(col);r+=1
    free=[j for j in range(83) if j not in pivots];vectors=[]
    for j in free:
        v=[0]*83;v[j]=1
        for p,row in zip(pivots,matrix):v[p]=(-row[j])%83
        assert all(sum(a*b for a,b in zip(v,row))%83==0 for row in rows)
        vectors.append(v)
    return r,vectors
def normalized(key,anchors):
    a,b=anchors;scale=pow((key[b]-key[a])%83,-1,83)
    return [((v-key[a])*scale)%83 for v in key]

def check_control(c):
    key=c['true_label_to_residue'];assert sorted(key)==list(range(83))
    steps=c['input_steps'];assert len(steps)==len(set(steps))==27 and all(0<p<83 for p in steps)
    for initial,ct,pt in zip(c['initial_residues'],c['ciphertext'],c['plaintext']):
        assert len(ct)==len(pt);state=initial
        for output,token in zip(ct[1:],pt[1:]):
            state=(state+steps[token])%83;assert key[output]==state
    for i,s,j,t,n in c['equalities']:assert c['plaintext'][i][s:s+n]==c['plaintext'][j][t:t+n]
    rows=constraints(c['ciphertext'],c['equalities']);rank,vs=kernel(rows)
    assert all(sum(x*y for x,y in zip(key,row))%83==0 for row in rows)
    result=c['result'];assert result['rank']==rank and result['nullity']==len(vs)
    if result['status']=='output_map_recovered_up_to_affine_change':
        assert len(vs)==2 and result['normalized_label_to_residue']==normalized(key,[0,1])
    else:assert result['status']=='linear_information_insufficient_for_unique_map'
    return rows,rank

def check_refinement(c,result):
    rows,rank=check_control(c)
    active=[j for j in range(83) if any(row[j] for row in rows)];inactive=sorted(set(range(83))-set(active))
    assert active==result['active_labels'] and inactive==result['unconstrained_labels']
    assert rank==result['rank'] and len(active)-rank==result['active_nullity']
    if result['status']=='additional_linear_freedom':assert result['active_nullity']>2;return None
    assert result['active_nullity']==2
    anchors=result['anchor_labels'];assert anchors==active[:2]
    truth=normalized(c['true_label_to_residue'],anchors)
    assert {int(j):v for j,v in result['normalized_active_map'].items()}=={j:truth[j] for j in active}
    remaining=sorted(set(range(83))-{truth[j] for j in active})
    assert remaining==result['unused_residues']
    assert result['permutation_completions_with_anchors_fixed']==str(math.factorial(len(inactive)))
    if result['status']=='unique_bijective_map_up_to_affine_change':
        key=result['normalized_label_to_residue'];assert len(inactive)<=1 and key==truth and sorted(key)==list(range(83))
        a,b=anchors;scale=pow((c['true_label_to_residue'][b]-c['true_label_to_residue'][a])%83,-1,83);checks=0
        for ct,pt in zip(c['ciphertext'],c['plaintext']):
            for t in range(2,len(ct)):
                assert (key[ct[t]]-key[ct[t-1]])%83==c['input_steps'][pt[t]]*scale%83;checks+=1
        return dict(seed=c['seed'],map_entries=83,decoded_increment_checks=checks,anchors=anchors)
    assert result['status']=='active_map_recovered_unconstrained_label_permutations_remain' and len(inactive)>1
    return None

def check_loops(messages,records,words,edges):
    expected=[];total=bad=0
    for mi,start,n,word in words:
        cipher=messages[mi][start:start+n]
        for a,b in itertools.combinations(range(n),2):
            if cipher[a]!=cipher[b]:continue
            expected.append(([mi,start,n],[a,b],word[a+1:b+1]))
    assert len(records)==len(expected)==7
    for record,(source,offsets,word) in zip(records,expected):
        assert record['source']==source and record['equal_output_offsets']==offsets and record['word']==word
        complete=0;violations=[]
        for initial in range(83):
            state=initial;path=[]
            for token in word:
                edge=edges.get((token,state))
                if edge is None:break
                finish,location=edge;path.append(dict(token=token,before=state,after=finish,location=location));state=finish
            else:
                complete+=1
                if state!=initial:violations.append(dict(initial=initial,finish=state,path=path))
        assert complete==record['fully_observed_paths'] and violations==record['violations']
        total+=complete;bad+=len(violations)
    return dict(return_words=len(records),fully_observed_paths=total,violations=bad)

def main():
    messages=list(read('ciphertext.json').values());parent=read('state_memory_comparison.json');source=read('recurrence_transfer_audit.json');refinement=read('cyclic_permutation_refinement.json')
    assert source['ciphertext_sha256']==sha('ciphertext.json') and source['parent_sha256']==sha('state_memory_comparison.json')
    assert refinement['source_sha256']==sha('recurrence_transfer_audit.json')
    out=dict(status='Independent checks passed; no Eye plaintext or key recovered.',source_hashes={f:sha(f) for f in ['ciphertext.json','state_memory_comparison.json','recurrence_transfer_audit.json','cyclic_permutation_refinement.json']},engineered_loops=[],cyclic_cases={},recovered_controls=[])
    for record in source['engineered_loop_tests']:
        w=parent['engineered_fits'][record['parent_witness']];edges={}
        assert all(sorted(row)==list(range(83)) for row in w['key'])
        for mi,(ct,pt,state) in enumerate(zip(messages,w['body_tokens'],w['initial_states'])):
            for t,(c,p) in enumerate(zip(ct[1:],pt),1):
                assert w['key'][p][state]==c;edges[p,state]=(c,[mi,t]);state=c
        words=[(mi,start,n,w['body_tokens'][mi][start-1:start-1+n]) for mi,start,n in [(1,37,15),(6,71,27)]]
        out['engineered_loops'].append(check_loops(messages,record['loops'],words,edges))
    # Independent connected components for the unmerged token classes.
    pairs=sorted({(m[t-1],m[t]) for m in messages for t in range(2,len(m))});index={p:i for i,p in enumerate(pairs)}
    pos={(mi,t):index[m[t-1],m[t]] for mi,m in enumerate(messages) for t in range(2,len(m))};adj=[set() for _ in pairs]
    for i,s,j,t,n in parent['assumption_sets']['full_prefix']:
        for d in range(n):
            if min(s+d,t+d)<2:continue
            a,b=pos[i,s+d],pos[j,t+d];adj[a].add(b);adj[b].add(a)
    tokens=[None]*len(pairs)
    for root in range(len(pairs)):
        if tokens[root] is not None:continue
        stack=[root];tokens[root]=root
        while stack:
            v=stack.pop()
            for w in adj[v]:
                if tokens[w] is None:tokens[w]=root;stack.append(w)
    record=source['unmerged_loop_test'];assert tokens==record['node_tokens'] and len(set(tokens))==record['token_classes']==738
    edges={}
    for (mi,t),v in pos.items():a,b=pairs[v];edges[tokens[v],a]=(b,[mi,t])
    words=[(mi,start,n,[tokens[pos[mi,t]] for t in range(start,start+n)]) for mi,start,n in [(1,37,15),(6,71,27)]]
    out['unmerged_loops']=check_loops(messages,record['loops'],words,edges)
    expected=parent['assumption_sets'].copy();expected['within_W1']=[expected['early'][0]];expected['within_E2']=[expected['early'][1]]
    assert set(source['cyclic_cases'])==set(expected)
    for name,c in source['cyclic_cases'].items():
        assert c['equalities']==expected[name];rows=constraints(messages,c['equalities']);rank,vs=kernel(rows)
        assert c['rank']==rank and c['nullity']==len(vs) and c['equation_count']==sum(any(r) for r in rows)
        signatures=[tuple(v[j] for v in vs) for j in range(83)]
        collisions=[[a,b] for a in range(83) for b in range(a) if signatures[a]==signatures[b]]
        assert collisions==c['forced_label_collisions']
        if collisions:
            assert c['status']=='injective_output_map_impossible';certificate=c['certificate'];a,b=certificate['labels'];acc=[0]*83
            allowed={frozenset(((i,s+d),(j,t+d))) for i,s,j,t,n in c['equalities'] for d in range(n) if min(s+d,t+d)>=2}
            for term in certificate['terms']:
                x,y=map(tuple,term['positions']);assert frozenset((x,y)) in allowed and 0<term['coefficient']<83
                row=relation(messages,x,y);acc=[(a+term['coefficient']*b)%83 for a,b in zip(acc,row)]
            target=[0]*83;target[a]=1;target[b]=82;assert acc==target
        else:assert c['status']=='linear_constraints_survive'
        out['cyclic_cases'][name]=dict(rank=rank,nullity=len(vs),forced_collisions=len(collisions),certificate_terms=len(c.get('certificate',{}).get('terms',[])))
    # The early certificate also cancels over the integers, not merely mod
    # 83. Therefore the same identity holds in every abelian group.
    early=source['cyclic_cases']['early']['certificate'];integer_sum=[0]*83;signed=[]
    for term in early['terms']:
        coeff=term['coefficient'];coeff=coeff if coeff<=41 else coeff-83
        signed.append(dict(positions=term['positions'],coefficient=coeff))
        for (mi,t),sign in zip(term['positions'],(1,-1)):
            integer_sum[messages[mi][t]]+=coeff*sign
            integer_sum[messages[mi][t-1]]-=coeff*sign
    expected_sum=[0]*83;expected_sum[44]=1;expected_sum[33]=-1
    assert early['labels']==[44,33] and integer_sum==expected_sum
    out['abelian_group_certificate']=dict(status='Conditional collision for every abelian group with shared injective output labeling.',labels=[44,33],signed_terms=signed,integer_identity_verified=True)
    controls={c['seed']:c for c in source['controls']}
    for c in controls.values():check_control(c)
    for r in refinement['prior_controls']:
        checked=check_refinement(controls[r['seed']],r['result'])
        if checked:out['recovered_controls'].append(checked)
    checked=check_refinement(refinement['fresh_control'],refinement['fresh_result'])
    if checked:out['recovered_controls'].append(checked)
    assert len(out['recovered_controls'])==4
    out['generated_controls_checked']=7
    (ROOT/'checked_recurrence_transfer.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
