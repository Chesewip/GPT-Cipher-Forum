"""Independent integer certificates, context eligibility, and reset controls.

Uses only the standard library and prior independent linear algebra helpers.
Does not import discovery implementations.
"""
from pathlib import Path
import hashlib,json
from verify_recurrence_transfer import kernel,normalized
ROOT=Path(__file__).resolve().parent

def load(name):return json.loads((ROOT/name).read_bytes())
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()

def row_for(messages,positions):
    row=[0]*83
    for (mi,t),sign in zip(positions,[1,-1]):
        row[messages[mi][t]]+=sign;row[messages[mi][t-1]]-=sign
    return row

def make_rows(messages,equalities,trim,filter_equal=True):
    out=[]
    for i,s,j,t,n in equalities:
        for d in range(trim,n):
            if min(s+d,t+d)<2:continue
            ps=[[i,s+d],[j,t+d]]
            if filter_equal and messages[i][s+d]==messages[j][t+d]:continue
            row=[v%83 for v in row_for(messages,ps)]
            if any(row):out.append((ps,row))
    return out

def check_certificate(messages,rows,proof,integer=False):
    allowed={tuple(tuple(p) for p in ps) for ps,row in rows};total=[0]*83
    a,b=proof['labels'];assert a!=b and 0<=a<83 and 0<=b<83
    assert proof['terms']
    for term in proof['terms']:
        ps=term['positions'];assert tuple(tuple(p) for p in ps) in allowed
        c=term['coefficient'];assert isinstance(c,int) and c!=0
        if not integer:assert 0<c<83
        total=[x+c*y for x,y in zip(total,row_for(messages,ps))]
    expected=[0]*83;expected[a]=1;expected[b]=-1
    assert total==expected if integer else [x%83 for x in total]==[x%83 for x in expected]
    return total

def check_result(messages,rows,result):
    assert result['equation_count']==len(rows)
    rank,vs=kernel([row for ps,row in rows])
    assert result['rank']==rank and result['nullity']==83-rank
    if result['status']=='forced_output_collision':
        check_certificate(messages,rows,result['certificate']);return
    assert result['status']=='no_forced_collision'
    signatures=[tuple(v[j] for v in vs) for j in range(83)]
    assert len(set(signatures))==83
    active={j for ps,row in rows for j,x in enumerate(row) if x}
    assert result['unconstrained_labels']==sorted(set(range(83))-active)
    assert result['active_nullity']==len(active)-rank
    if 'normalized_label_to_residue' in result:
        assert result['active_nullity']==2 and len(active)>=82
        key=result['normalized_label_to_residue'];assert sorted(key)==list(range(83))
        assert key==normalized(key,result['anchor_labels'])
        assert all(sum(a*b for a,b in zip(key,row))%83==0 for ps,row in rows)

def main():
    source=load('input_reset_context_audit.json');messages=list(load('ciphertext.json').values())
    parent=load('state_memory_comparison.json')['assumption_sets']
    assert source['ciphertext_sha256']==sha('ciphertext.json') and source['parent_sha256']==sha('state_memory_comparison.json')
    assert source['assumption_sets']=={name:parent[name] for name in ['early','late','strong']}
    out=dict(status='Independent checks passed. Conditional mechanism exclusions, no Eye plaintext.',
             source_hashes={name:sha(name) for name in ['ciphertext.json','state_memory_comparison.json','input_reset_context_audit.json']},screens={},integer_certificates={},controls=[])
    for name,equalities in source['assumption_sets'].items():
        cases=source['screens'][name];assert [r['trim'] for r in cases]==list(range(28))
        comparisons=sum(n for i,s,j,t,n in equalities)
        assert all(messages[i][s+d]!=messages[j][t+d] for i,s,j,t,n in equalities for d in range(n))
        excluded=[]
        for r in cases:
            rows=make_rows(messages,equalities,r['trim']);check_result(messages,rows,r)
            if r['status']=='forced_output_collision':excluded.append(r['trim'])
        limit=10 if name=='early' else 16;assert excluded==list(range(limit+1))
        out['screens'][name]=dict(cases=len(cases),unequal_aligned_comparisons=comparisons,
            excluded_prefix_trims=excluded,first_no_forced_collision_trim=limit+1,
            before_output_context_length_excluded_through=limit+1,after_output_context_length_excluded_through=limit)
    for name,entry in source['integer_proofs'].items():
        rows=make_rows(messages,parent[name],entry['trim'])
        total=check_certificate(messages,rows,entry['certificate'],True);assert total==entry['integer_sum']
        out['integer_certificates'][name]=dict(trim=entry['trim'],terms=len(entry['certificate']['terms']),labels=entry['certificate']['labels'],exact_integer_cancellation=True)
    for c in source['controls']:
        length=c['context_length'];timing=c['timing'];assert timing in ['before','after']
        trim=length-1 if timing=='before' else length;assert c['trim']==trim
        key=c['true_label_to_residue'];assert sorted(key)==list(range(83))
        table={tuple(r['context']):r for r in c['context_table']};assert len(table)==len(c['context_table'])
        ciphertext=c['ciphertext'];plaintext=c['plaintext'];body_checks=0
        assert len(ciphertext)==len(plaintext)==len(c['initial_states'])==len(c['reset_positions'])==9
        for ct,pt,initial,rs in zip(ciphertext,plaintext,c['initial_states'],c['reset_positions']):
            assert len(ct)==len(pt);state=initial;actual=[]
            for t in range(1,len(pt)):
                h=tuple(pt[max(1,t-length+1):t+1]);entry=table[h]
                assert 0<entry['step']<83 and 0<=entry['replacement']<83 and isinstance(entry['trigger'],bool)
                if timing=='before':
                    if entry['trigger']:state=entry['replacement']
                    else:state=(state+entry['step'])%83
                    output=state
                else:
                    output=(state+entry['step'])%83
                    state=entry['replacement'] if entry['trigger'] else output
                assert key[ct[t]]==output;body_checks+=1
                if entry['trigger']:actual.append(t)
            assert rs==actual
        for i,s,j,t,n in c['equalities']:assert plaintext[i][s:s+n]==plaintext[j][t:t+n]
        rows=make_rows(ciphertext,c['equalities'],trim);check_result(ciphertext,rows,c['result'])
        assert c['result']['status']=='no_forced_collision'
        assert all(sum(x*y for x,y in zip(key,row))%83==0 for ps,row in rows)
        raw=make_rows(ciphertext,c['equalities'],trim,False);check_result(ciphertext,raw,c['naive_result'])
        assert c['naive_result']['status']=='forced_output_collision'
        bad=[ps for ps,row in raw if sum(x*y for x,y in zip(key,row))%83]
        assert bad==c['incorrectly_retained_rows'] and bad
        assert len(c['synchronized_suffixes'])==len(c['equalities'])==8
        for r,(i,s,j,t,n) in zip(c['synchronized_suffixes'],c['equalities']):
            first=next(d for d in range(trim,n) if s+d in c['reset_positions'][i])
            assert t+first in c['reset_positions'][j]
            start=first+int(timing=='after')
            assert r==dict(messages=[i,j],shared_reset_offset=first,equal_output_suffix_offset=start,length=n-start)
            assert ciphertext[i][s+start:s+n]==ciphertext[j][t+start:t+n]
        out['controls'].append(dict(seed=c['seed'],timing=timing,context_length=length,
                body_symbols_reencrypted=body_checks,eligible_equations=len(rows),
                false_rows_if_resets_ignored=len(bad),synchronized_suffixes=8))
    assert [(c['seed'],c['context_length'],c['timing']) for c in source['controls']]==[(909600+i,l,t) for i,(l,t) in enumerate((l,t) for l in [1,2,5] for t in ['before','after'])]
    out['body_symbols_reencrypted']=sum(c['body_symbols_reencrypted'] for c in out['controls'])
    (ROOT/'checked_input_reset_context.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
