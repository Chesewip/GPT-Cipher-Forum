"""Independent numeric candidate checks and local deletion-certificate replay.

Standard library only; imports no new discovery or propagation implementation.
Solver timeouts are logged outcomes, never independently proved exclusions.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,random
from verify_frozen_candidates import f,decode,heldout,check_encryption
ROOT=Path(__file__).resolve().parent

def read(n):return json.loads((ROOT/n).read_bytes())
def sha(n):return hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
def normalize(name,key):
    if name!='add':return key.copy()
    a=pow((key[1]-key[0])%83,81,83)
    return [(a*(v-key[0]))%83 for v in key]

def replay(messages,name,pins,result,truth):
    edges=sorted({(m[t-1],m[t]) for m in messages[:6] for t in range(2,len(m))})
    incident=[[e for e in edges if j in e] for j in range(83)]
    domains=[set(range(83)) for _ in range(83)]
    for j,v in pins:domains[j]={v}
    if name=='add':domains[0]={0};domains[1]={1}
    assert result['initial_domains']==[sorted(d) for d in domains]
    initial_singletons=sum(len(d)==1 for d in domains)
    def snapshot():
        fixed={j:next(iter(d)) for j,d in enumerate(domains) if len(d)==1}
        codes={(fixed[b]-f(name,fixed[a]))%83 for a,b in edges if a in fixed and b in fixed}
        return fixed,codes
    fixed,codes=snapshot();assert result['initial_codes']==sorted(codes)
    def local_codes(j,value):
        trial=dict(fixed);trial[j]=value
        return codes|{(trial[b]-f(name,trial[a]))%83 for a,b in incident[j] if a in trial and b in trial}
    def supported(j,value,edge):
        a,b=edge
        if a==b:return (value-f(name,value))%83 in codes
        left=[value] if a==j else domains[a];right=[value] if b==j else domains[b]
        return any((y-f(name,x))%83 in codes for x in left for y in right)
    reasons=Counter()
    for event in result['trace']:
        j=event['label'];value=event['value'];reason=event['reason'];witness=event['witness']
        assert value in domains[j] and len(domains[j])>1 and value!=truth[j]
        if reason=='used_value':assert witness!=j and fixed[witness]==value
        elif reason=='alphabet_cap':assert len(local_codes(j,value))>27
        elif reason=='edge_support':
            assert len(codes)==27 and tuple(witness) in incident[j] and not supported(j,value,witness)
        else:raise AssertionError(reason)
        domains[j].remove(value);reasons[reason]+=1
        if len(domains[j])==1:fixed,codes=snapshot()
        assert len(codes)<=27
    assert result['domains']==[sorted(d) for d in domains]
    assert result['singletons']==len(fixed) and result['final_codes']==sorted(codes)
    assert sum(r['removed'] for r in result['rounds'])==len(result['trace']) and result['rounds'][-1]['removed']==0
    assert all(truth[j] in d for j,d in enumerate(domains))
    # Verify it is a fixed point for the three implemented local filters.
    for j,domain in enumerate(domains):
        if len(domain)==1:continue
        for value in domain:
            assert value not in fixed.values() and len(local_codes(j,value))<=27
            if len(codes)==27:assert all(supported(j,value,e) for e in incident[j])
    if len(fixed)==83:
        assert result['key']==[fixed[j] for j in range(83)]==truth
        assert sorted(result['key'])==list(range(83))
    else:assert 'key' not in result
    return dict(initial_singletons=initial_singletons,final_singletons=len(fixed),initial_code_values=len(result['initial_codes']),
        final_code_values=len(codes),deleted_values=len(result['trace']),deletion_reasons=dict(reasons),fully_recovered=len(fixed)==83)

def main():
    source=read('frozen_candidate_search.json');joint=read('joint_feedback_constraints.json');prop=read('propagate_feedback_domains.json');guards=read('joint_feedback_guards.json')
    for data in [joint,prop,guards]:assert data['source_sha256']==sha('frozen_candidate_search.json')
    assert prop['joint_parent_sha256']==sha('joint_feedback_constraints.json')
    assert joint['training_messages']==list(range(6)) and joint['heldout_messages']==[6,7,8]
    assert not joint['global_no_doubles_constraint'] and not prop['global_no_doubles_constraint'] and not prop['uses_early_equalities']
    out=dict(status='Independent candidates, cap guards and propagation certificates passed; no Eye key.',
        source_hashes={n:sha(n) for n in ['frozen_candidate_search.json','joint_feedback_constraints.json','joint_feedback_guards.json','propagate_feedback_domains.json']},
        controls=[],reencrypted_symbols=0,bitvector_residue_pairs_checked=0)
    # Exhaustively validate the seven-bit corrected subtraction arithmetic.
    for a in range(83):
        for b in range(83):
            encoded=(a-b)%128 if a>=b else ((a-b)%128+83)%128
            assert encoded==(a-b)%83;out['bitvector_residue_pairs_checked']+=1
    for c,joint_c,prop_c,guard in zip(source['controls'],joint['controls'],prop['controls'],guards['guards']):
        assert c['seed']==joint_c['seed']==prop_c['seed']==guard['seed']
        truth=normalize(c['name'],c['true_key']);early=source['early_equalities'];late=source['late_equalities']
        out['reencrypted_symbols']+=check_encryption(c,early,late)
        assert joint_c['hide_order']==random.Random(joint_c['mask_seed']).sample(range(83),83)
        d=decode(c['ciphertext'],c['name'],truth);true_codes={x for row in d[:6] for x in row[2:]}
        assert len(true_codes)==27 and guard['cap']==26 and guard['status']=='unsat' and guard['all_key_entries_pinned']
        row=dict(name=c['name'],seed=c['seed'],joint_runs=[],propagation=[])
        for r in joint_c['runs']:
            missing=set(joint_c['hide_order'][:r['hidden_labels']]);pins=[[j,v] for j,v in enumerate(truth) if j not in missing]
            assert r['pins']==pins and r['rule_supplied'] and r['timeout_ms']==12000
            assert r['training_transitions']==sum(len(m)-2 for m in c['ciphertext'][:6])
            assert r['distinct_training_edges']==len({(m[t-1],m[t]) for m in c['ciphertext'][:6] for t in range(2,len(m))})
            if r['status']=='sat':
                key=r['key'];assert sorted(key)==list(range(83)) and all(key[j]==v for j,v in pins)
                if c['name']=='add':assert key[0]==0 and key[1]==1
                decoded=decode(c['ciphertext'],c['name'],key);codes=sorted({v for m in decoded[:6] for v in m[2:]})
                assert codes==r['codebook'] and len(codes)<=27
                assert all(decoded[i][s+k]==decoded[j][t+k] for i,s,j,t,n in early for k in range(n))
                assert r['heldout']==heldout(c['ciphertext'],late,c['name'],key,codes)
                assert r['canonical_truth_matches']==sum(a==b for a,b in zip(key,truth))==83
                assert r['heldout']['outside_frozen_codebook']==r['heldout']['late_pair_mismatches']==0
            else:assert r['status']=='unknown' and r['reason_unknown'] and 'key' not in r
            row['joint_runs'].append(dict(hidden_labels=r['hidden_labels'],status=r['status'],truth_matches=r.get('canonical_truth_matches')))
        for r in prop_c['runs']:
            missing=set(joint_c['hide_order'][:r['hidden_labels']]);pins=[[j,v] for j,v in enumerate(truth) if j not in missing]
            assert r['pins']==pins
            result=replay(c['ciphertext'],c['name'],pins,r['result'],truth);result['hidden_labels']=r['hidden_labels']
            if result['fully_recovered']:
                h=heldout(c['ciphertext'],late,c['name'],r['result']['key'],r['result']['final_codes'])
                assert r['heldout']==h and h['outside_frozen_codebook']==h['late_pair_mismatches']==0
                result['heldout']={k:v for k,v in h.items() if k!='decoded_residues'}
            row['propagation'].append(result)
        out['controls'].append(row)
        print(c['name'],'verified',[(r['hidden_labels'],r['final_singletons']) for r in row['propagation']],flush=True)
    (ROOT/'checked_joint_feedback.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(out['status'],flush=True)

if __name__=='__main__':main()
