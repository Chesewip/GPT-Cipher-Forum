"""Independent standard-library checks of function-model refinements.

No discovery implementations imported. The earlier independent proof replayer
is reused only for recorded conditional-equality certificates.
"""
from pathlib import Path
from collections import Counter, defaultdict
import itertools, json, hashlib, math
from verify_nonlinear_dependencies import routing, check_result

ROOT = Path(__file__).resolve().parent
POINTS = list(itertools.product(range(5), repeat=3))
def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf-8'))
def sha(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
def number(point):
    return sum(a*b for a,b in zip((25,5,1),point))
def allowed(table, axis):
    other = [d for d in range(3) if d != axis]
    return {i for i,p in enumerate(POINTS) if p[axis] == table[p[other[0]]][p[other[1]]]}
def flatten(messages):
    return [x for m in messages for x in m]
def decode(messages, key, period):
    result = []
    for message in messages:
        for start in range(0,len(message),period):
            block=message[start:start+period]; n=len(block)
            stream=[d for label in block for d in POINTS[key[label]]]
            result.extend(number(stream[i::n]) for i in range(n))
    return result
def encode_pair(p,q):
    stream=[d for pair in zip(POINTS[p],POINTS[q]) for d in pair]
    return number(stream[:3]),number(stream[3:])
def decode_pair(pair):
    stream=list(POINTS[pair[0]])+list(POINTS[pair[1]])
    return [number(stream[::2]),number(stream[1::2])]
def check_control(c):
    assert sorted(c['true_label_to_code']) == list(range(125))
    actual=decode(c['ciphertext'],c['true_label_to_code'],c['period'])
    assert actual == flatten(c['plaintext'])
    assert set(actual) <= allowed(c['table'],c['axis'])
def degrees(messages,strip=False,reverse=False,first=2):
    edges=set(); labels=set()
    for raw in messages:
        seq=list(raw[int(strip):])
        if reverse: seq.reverse()
        labels.update(seq); start=0; width=first
        while start < len(seq):
            block=seq[start:start+width]
            if len(block)==2: edges.add(tuple(block))
            start+=width; width=2
    return [{str(v):sum(e[side]==v for e in edges) for v in sorted(labels)} for side in (0,1)]
def check_summary(deg,saved):
    assert deg==saved['degrees']
    tails=[sum(d>5*k for d in deg.values()) for k in range(5)]
    assert tails==saved['tail_counts']
    budget=sum(math.ceil(h/5) for h in tails)
    assert budget==saved['required_table_entries']
    return budget
def partitions(n,minimum=1):
    if not n:
        yield ()
    for x in range(minimum,n+1):
        for rest in partitions(n-x,x): yield (x,)+rest
def ident(c):
    return c['axis'],c['period'],c['strip_first'],c['reverse']

def main():
    source=read('one_coordinate_function_screen.json')
    eyes=list(read('ciphertext.json').values())
    controls={c['seed']:c for c in source['controls']}
    for c in controls.values(): check_control(c)
    out={'status':'Independent checks passed; Eye cipher unsolved.', 'ciphertext_sha256':sha('ciphertext.json')}
    cert=read('period_two_degree_certificate.json')
    assert cert['ciphertext_sha256']==sha('ciphertext.json')
    assert {(c['strip_first'],c['reverse'],c['first_block']) for c in cert['cases']}==set(itertools.product((False,True),(False,True),(1,2)))
    observed=[]
    for c in cert['cases']:
        ds=degrees(eyes,c['strip_first'],c['reverse'],c['first_block'])
        budgets=[check_summary(d,c[name]) for d,name in zip(ds,('outgoing','incoming'))]
        direction=c['middle_axis_certificate_direction']; side=int(direction=='incoming')
        assert budgets[side]==26
        assert ds[1][str(c['outer_axis0_in_degree_witness'])]>5
        assert ds[0][str(c['outer_axis2_out_degree_witness'])]>5
        observed.append(sorted(ds[side].values(),reverse=True))
    # Independent finite relaxation: all seven partitions of each table row's
    # five cells, for all five rows. No tail-budget shortcut used here.
    parts=list(partitions(5)); assert len(parts)==7
    profile_count=0
    for rows in itertools.product(parts,repeat=5):
        caps=sorted([5*m for row in rows for m in row for _ in range(5)],reverse=True)
        caps += [0]*(125-len(caps)); profile_count+=1
        for obs in observed: assert any(d>cap for d,cap in zip(obs,caps))
    for c in cert['controls']:
        check_control(c)
        ds=degrees(c['ciphertext'])
        assert all(check_summary(d,c[name])<=25 for d,name in zip(ds,('outgoing','incoming')))
        # Direct encoding of every input pair checks both degree identities
        # and the middle-axis counting formula on actual generated tables.
        for axis in range(3):
            codebook=allowed(c['table'],axis)
            pairs={encode_pair(p,q) for p,q in itertools.product(codebook,repeat=2)}
            assert len(pairs)==625
            outs=Counter(p for p,q in pairs); ins=Counter(q for p,q in pairs)
            if axis==0: assert all(ins[v]==5 for v in range(125))
            if axis==2: assert all(outs[v]==5 for v in range(125))
            if axis==1:
                for v,(a,b,d) in enumerate(POINTS):
                    assert outs[v]==5*c['table'][a].count(d)
                    assert ins[v]==5*sum(row[d]==a for row in c['table'])
    out['degree_certificate']={'excluded_settings':24,'views':8,'row_profiles_per_view':profile_count,'generated_controls':3}
    refinement=read('function_dependency_refinement_16.json')
    assert refinement['source_sha256']==sha('one_coordinate_function_screen.json')
    assert refinement['ciphertext_sha256']==sha('ciphertext.json')
    old={ident(c) for c in source['cases'] if c['status']=='closure_survives'}
    assert len(old)==278 and {ident(c) for c in refinement['cases']}==old
    excluded=set(); steps=branches=0
    for c in refinement['cases']:
        if c['status']=='no_six_clique_found': continue
        assert c['status']=='six_pairwise_distinct_coordinate_values'
        rr=routing(eyes,c['period'],c['first_block'],c['strip_first'],c['reverse'])
        labels={v//3 for row in rr for v in row}
        s,b=check_result(rr,labels,c,(c['axis'],)); steps+=s; branches+=b
        excluded.add(ident(c))
    assert len(excluded)==2 and branches==30
    for c in refinement['controls']:
        actual=controls[c['control_seed']]
        vals=[d for code in actual['true_label_to_code'] for d in POINTS[code]]
        assert c['status']=='no_six_clique_found'
        for a,b in c['inequality_edges']:
            assert vals[c['coordinate_variables'][a]]!=vals[c['coordinate_variables'][b]]
    period_two={c for c in old if c[1]==2}; assert len(period_two)==4
    remaining=sorted(old-excluded-period_two); assert len(remaining)==272
    out['graph_refinement']={'new_exclusions':[list(c) for c in sorted(excluded)],'checked_branches':branches,'checked_implications':steps}
    out['remaining_full_first_block_cases']=[dict(zip(('axis','period','strip_first','reverse'),c)) for c in remaining]
    pilot=read('function_table_boolean_pilot.json'); recovered=[]
    for r in pilot['runs']:
        if r['status']=='unknown': continue
        assert r['status']=='sat' and r['kind']=='control_known'
        c=controls[r['control_seed']]; assert r['table']==c['table']==r['known_table']
        assert sorted(r['key'])==list(range(125))
        actual=decode(c['ciphertext'],r['key'],c['period'])
        assert actual==r['decoded'] and set(actual)<=allowed(r['table'],r['axis'])
        labels=set(flatten(c['ciphertext']))
        recovered.append(dict(seed=c['seed'],observed_labels=len(labels),matching_key_entries=sum(r['key'][v]==c['true_label_to_code'][v] for v in labels),changed_plaintext_positions=sum(a!=b for a,b in zip(actual,flatten(c['plaintext'])))))
    assert [r['changed_plaintext_positions'] for r in recovered]==[236,0]
    assert [r['matching_key_entries'] for r in recovered]==[79,125]
    out['known_table_solver_witnesses']=recovered
    uf=read('function_table_solver_pilot.json')
    assert len(uf['real'])==4 and len(uf['controls'])==3
    assert all(r['status']=='unknown' for r in uf['real']+uf['controls'])
    out['inconclusive_solver_runs']=7+sum(r['status']=='unknown' for r in pilot['runs'])
    ambiguity=read('function_key_ambiguity.json'); c=controls[ambiguity['control_seed']]
    assert ambiguity['control_source_sha256']==sha('one_coordinate_function_screen.json')
    original=flatten(c['plaintext']); key=c['true_label_to_code']; freq=Counter(flatten(c['ciphertext']))
    codebook=allowed(c['table'],c['axis']); valid=[]; tested=0
    for a,b in itertools.combinations(range(125),2):
        if not freq[a] and not freq[b]:continue
        tested+=1; alternative=key.copy(); alternative[a],alternative[b]=alternative[b],alternative[a]
        dec=decode(c['ciphertext'],alternative,c['period'])
        if not set(dec)<=codebook:continue
        images=defaultdict(set)
        for old,new in zip(original,dec):images[old].add(new)
        if not any(len(v)>1 for v in images.values()):continue
        valid.append([a,b,sum(x!=y for x,y in zip(original,dec)),freq[a],freq[b]])
    assert tested==ambiguity['two_entry_swaps_tested']==7749
    assert valid==ambiguity['valid_swaps'] and len(valid)==ambiguity['valid_nonrenaming_swaps']==77
    a,b=ambiguity['selected_labels']; alternative=key.copy(); alternative[a],alternative[b]=alternative[b],alternative[a]
    dec=decode(c['ciphertext'],alternative,c['period'])
    assert alternative==ambiguity['alternative_key'] and dec==ambiguity['alternative_decoded']
    changed=[]; offset=0
    for mi,m in enumerate(c['plaintext']):
        changed.extend([mi,i,x,dec[offset+i]] for i,x in enumerate(m) if x!=dec[offset+i]); offset+=len(m)
    assert changed==ambiguity['changed_locations'] and len(changed)==43
    w=ambiguity['nonrenaming_witness']; assert w[0][1]==w[1][1] and w[0][2]!=w[1][2]
    for i,old,new in w:assert original[i]==old and dec[i]==new
    auto=read('function_graph_automorphisms.json')
    assert auto['control_source_sha256']==sha('one_coordinate_function_screen.json') and auto['table']==c['table']
    pairs={encode_pair(p,q) for p,q in itertools.product(codebook,repeat=2)}
    assert len(pairs)==auto['valid_two_symbol_blocks']==625
    tau=list(range(125)); a,b=auto['selected_coordinate_codes']; assert [a,b]==[key[v] for v in ambiguity['selected_labels']]
    tau[a],tau[b]=tau[b],tau[a]
    assert all((x in codebook)==(tau[x] in codebook) for x in range(125))
    assert all(((x,y) in pairs)==((tau[x],tau[y]) in pairs) for x,y in itertools.product(range(125),repeat=2))
    groups=defaultdict(list)
    for v in range(125):
        signature=(frozenset(y for x,y in pairs if x==v),frozenset(x for x,y in pairs if y==v),v in codebook)
        groups[signature].append(v)
    twins=[g for g in groups.values() if len(g)>1]
    live=[g for sig,g in groups.items() if len(g)>1 and any(sig)]
    assert twins==auto['all_twin_classes'] and live==auto['live_twin_classes']
    bound=math.prod(math.factorial(len(g)) for g in live)
    assert str(bound)==auto['live_twin_permutation_lower_bound']
    changes=[]
    for p,q in itertools.product(sorted(codebook),repeat=2):
        image=decode_pair(tuple(tau[x] for x in encode_pair(p,q)))
        if image!=[p,q]: changes.append([[p,q],image])
    assert changes==auto['changed_block_examples'] and len(changes)==auto['changed_plaintext_blocks']==42
    for w in auto['contextual_nonrenaming_witnesses']:
        pos=w['position']; first,second=w['blocks']
        assert first[0][pos]==second[0][pos]==w['input_symbol'] and first[1][pos]!=second[1][pos]
        for before,after in w['blocks']:
            assert after==decode_pair(tuple(tau[x] for x in encode_pair(*before)))
    out['generated_global_ambiguity']={'seed':c['seed'],'sample_swaps_checked':tested,'valid_nonrenaming_sample_swaps':len(valid),'selected_changed_sample_positions':43,'all_pair_memberships_checked':15625,'changed_valid_plaintext_blocks':42,'live_twin_classes':len(live),'live_key_permutation_lower_bound':str(bound)}
    files=['ciphertext.json','one_coordinate_function_screen.json','period_two_degree_certificate.json','function_dependency_refinement_16.json','function_table_solver_pilot.json','function_table_boolean_pilot.json','function_key_ambiguity.json','function_graph_automorphisms.json']
    out['source_hashes']={f:sha(f) for f in files}
    (ROOT/'checked_function_refinements.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('remaining_full_first_block_cases','source_hashes')},indent=2))

if __name__=='__main__':main()
