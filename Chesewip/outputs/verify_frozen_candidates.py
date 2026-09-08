"""Independent frozen-codebook and lifted-map checks, standard library only."""
from pathlib import Path
from collections import Counter
import hashlib,json
ROOT=Path(__file__).resolve().parent

def read(n):return json.loads((ROOT/n).read_bytes())
def sha(n):return hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
def f(name,x):return x if name=='add' else x*x%83 if name=='square' else pow(x,81,83)
def decode(messages,name,key):return [[None,None]+[(key[m[t]]-f(name,key[m[t-1]]))%83 for t in range(2,len(m))] for m in messages]

def training(messages,eq,name,key,weight):
    d=decode(messages,name,key);values=[v for row in d[:6] for v in row[2:]];counts=Counter(values)
    allowed=sorted(set(range(83))-{(x-f(name,x))%83 for x in range(83)})
    code=sorted(sorted(allowed,key=lambda x:(-counts[x],x))[:27])
    outside=sum(v not in code for v in values);bad=sum(d[i][s+k]!=d[j][t+k] for i,s,j,t,n in eq for k in range(n))
    return dict(energy=outside+weight*bad,outside_codebook=outside,early_pair_mismatches=bad,
                distinct_residuals=len(counts),codebook=code,scored_transitions=len(values))

def heldout(messages,eq,name,key,code):
    d=decode(messages,name,key);values=[v for row in d[6:] for v in row[2:]]
    return dict(outside_frozen_codebook=sum(v not in code for v in values),transitions=len(values),
        late_pair_mismatches=sum(d[i][s+k]!=d[j][t+k] for i,s,j,t,n in eq for k in range(n)),
        late_comparisons=sum(e[-1] for e in eq),distinct_residuals=len(set(values)),decoded_residues=d)

def check_encryption(c,early,late):
    key=c['true_key'];assert sorted(key)==list(range(83));codes=c['input_codebook'];assert len(set(codes))==len(codes)==27
    allowed=set(range(83))-{(x-f(c['name'],x))%83 for x in range(83)};assert set(codes)<=allowed
    count=0
    for ct,pt,state in zip(c['ciphertext'],c['plaintext'],c['initial_states']):
        assert len(ct)==len(pt)
        for t in range(1,len(ct)):state=(f(c['name'],state)+codes[pt[t]])%83;assert key[ct[t]]==state;count+=1
        assert all(a!=b for a,b in zip(ct[1:],ct[2:]))
    for i,s,j,t,n in early+late:assert c['plaintext'][i][s:s+n]==c['plaintext'][j][t:t+n]
    assert set(p for row in c['plaintext'][:6] for p in row[2:])==set(range(27))
    return count

def check_search(messages,early,late,r):
    assert len(r['runs'])==r['restarts']
    for run in r['runs']:
        assert sorted(run['key'])==sorted(run['initial_key'])==list(range(83))
        assert run['training']==training(messages,early,r['name'],run['key'],r['equality_weight'])
    chosen=min(range(len(r['runs'])),key=lambda i:r['runs'][i]['training']['energy']);assert chosen==r['selected_restart']
    assert r['key']==r['runs'][chosen]['key'] and r['training']==r['runs'][chosen]['training'] and r['codebook']==r['training']['codebook']
    assert r['heldout']==heldout(messages,late,r['name'],r['key'],r['codebook'])
    assert r['allowed_code_values']==sorted(set(range(83))-{(x-f(r['name'],x))%83 for x in range(83)})
    return dict(name=r['name'],mode=r['initial_mode'],equality_weight=r['equality_weight'],
                training=r['training'],heldout_outside=r['heldout']['outside_frozen_codebook'],
                heldout_late_mismatches=r['heldout']['late_pair_mismatches'])

def rows_for(messages,eq):
    rows=[]
    for i,s,j,t,n in eq:
        for k in range(n):
            row=[0]*166
            row[messages[i][s+k]]+=1;row[messages[j][t+k]]-=1
            row[83+messages[i][s+k-1]]-=1;row[83+messages[j][t+k-1]]+=1
            if any(row):rows.append([v%83 for v in row])
    return rows

def rank_of(rows):
    basis={}
    for original in rows:
        row=original.copy()
        for pivot in sorted(basis,reverse=True):
            c=row[pivot]
            if c:row=[(a-c*b)%83 for a,b in zip(row,basis[pivot])]
        pivot=next((i for i in reversed(range(len(row))) if row[i]),None)
        if pivot is not None:
            inv=pow(row[pivot],81,83);basis[pivot]=[v*inv%83 for v in row]
    return len(basis)

def check_lift(messages,eq,late,r):
    rows=rows_for(messages,eq);rank=rank_of(rows)
    assert (r['rank'],r['nullity'],r['nonzero_rows'])==(rank,166-rank,len(rows))
    if r['status']=='underdetermined_label_maps':return dict(rank=rank,nullity=166-rank,status=r['status'])
    assert r['status']=='normalized_label_maps_recovered';u,v=r['output_map'],r['feedback_map'];assert sorted(u)==list(range(83))
    inactive=[j for j in range(166) if not any(row[j] for row in rows)]
    assert 166-len(inactive)-rank==3 and not set(inactive)&{0,1,83}
    if inactive:
        assert r['linear_inactive_columns']==inactive and r['completed_output_labels']==[j for j in inactive if j<83]
        assert len(r['completed_output_labels'])<=1
    assert u[0]==v[0]==0 and u[1]==1
    assert [j+83 for j,x in enumerate(v) if x is None]==[j for j in inactive if j>=83]
    vector=u+[0 if x is None else x for x in v]
    assert all(sum(a*b for a,b in zip(vector,row))%83==0 for row in rows)
    anchors=[[int(i==j) for i in range(166)] for j in [0,1,83]+inactive]
    assert rank_of(rows+anchors)==166
    counts={};tests={}
    for name,record in r['families'].items():
        expected=[]
        for a in range(1,83):
            for b in range(83):
                if all(value is None or (f(name,(a*x+b)%83)-a*value)%83==f(name,b) for x,value in zip(u,v)):expected.append([a,b])
        assert expected==record['affine_parameters'];counts[name]=len(expected)
        if expected:
            a,b=expected[0];key=[(a*x+b)%83 for x in u];assert key==record['selected_key']
            d=decode(messages,name,key);code=sorted({x for row in d[:6] for x in row[2:]});assert code==record['frozen_codebook']
            assert record['heldout']==heldout(messages,late,name,key,code)
            tests[name]=dict(codebook_size=len(code),heldout_outside=record['heldout']['outside_frozen_codebook'],late_mismatches=record['heldout']['late_pair_mismatches'])
    return dict(rank=rank,nullity=166-rank,status=r['status'],inactive_columns=inactive,parameter_counts=counts,heldout=tests)

def main():
    s=read('frozen_candidate_search.json');lift=read('lifted_feedback_recovery.json');completion=read('lifted_feedback_completion.json')
    messages=list(read('ciphertext.json').values());sets=read('state_memory_comparison.json')['assumption_sets']
    assert s['training_messages']==list(range(6)) and s['heldout_messages']==[6,7,8]
    assert s['early_equalities']==lift['eye_training_equalities']==sets['early'] and s['late_equalities']==sets['late']
    for source in [s,lift]:
        assert source['ciphertext_sha256']==sha('ciphertext.json') and source['parent_sha256']==sha('state_memory_comparison.json')
        assert source['control_text_sha256']==hashlib.sha256((ROOT.parent/'work'/'pg1661.txt').read_bytes()).hexdigest()
    assert completion['parent_sha256']==sha('lifted_feedback_recovery.json')
    out=dict(status='Independent frozen-candidate checks passed; no Eye candidate qualifies.',
        source_hashes={name:sha(name) for name in ['ciphertext.json','state_memory_comparison.json','frozen_candidate_search.json','lifted_feedback_recovery.json','lifted_feedback_completion.json']},
        search_controls=[],eye=[],lifted_controls=[],reencrypted_symbols=0)
    for c in s['controls']:
        out['reencrypted_symbols']+=check_encryption(c,sets['early'],sets['late'])
        damaged=c['true_key'].copy()
        for a,b in c['repair_swaps']:damaged[a],damaged[b]=damaged[b],damaged[a]
        assert damaged==c['repair_start']
        for r in c['searches']:
            result=check_search(c['ciphertext'],sets['early'],sets['late'],r)
            if r['initial_mode']=='two_swap_repair':assert all(run['initial_key']==damaged for run in r['runs'])
            assert r['literal_key_matches']==sum(a==b for a,b in zip(r['key'],c['true_key']))
            assert r['true_key_training']==training(c['ciphertext'],sets['early'],c['name'],c['true_key'],3) and r['true_key_training']['energy']==0
            result.update(seed=c['seed'],literal_key_matches=r['literal_key_matches']);out['search_controls'].append(result)
    for r in s['eye']:out['eye'].append(check_search(messages,sets['early'],sets['late'],r))
    out['eye_lift']=check_lift(messages,sets['early'],sets['late'],lift['eye'])
    for c,extension in zip(lift['controls'],completion['controls']):
        print('Checking lifted control',c['name'],flush=True)
        assert extension['seed']==c['seed'];out['reencrypted_symbols']+=check_encryption(c,c['training_equalities'],c['late_equalities'])
        original=check_lift(c['ciphertext'],c['training_equalities'],c['late_equalities'],c['result'])
        completed=check_lift(c['ciphertext'],c['training_equalities'],c['late_equalities'],extension['result'])
        assert [name for name,n in completed['parameter_counts'].items() if n]==[c['name']]
        candidate=extension['result']['families'][c['name']];key=candidate['selected_key'];truth=c['true_key']
        if c['name']=='add':
            a=(key[1]-key[0])*pow((truth[1]-truth[0])%83,81,83)%83;b=(key[0]-a*truth[0])%83
            assert a and key==[(a*x+b)%83 for x in truth]
        elif c['name']=='square':assert key==truth
        else:assert key==truth or key==[(-x)%83 for x in truth]
        assert completed['heldout'][c['name']]==dict(codebook_size=27,heldout_outside=0,late_mismatches=0)
        out['lifted_controls'].append(dict(name=c['name'],seed=c['seed'],original=original,completed=completed,true_rule_and_equivalent_key_recovered=True))
    (ROOT/'checked_frozen_candidates.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(dict(status=out['status'],reencrypted_symbols=out['reencrypted_symbols'],eye_lift=out['eye_lift'],lifted_controls=out['lifted_controls']),indent=2))

if __name__=='__main__':main()
