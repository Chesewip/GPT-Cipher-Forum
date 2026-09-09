"""Independent affine-space, relationship, and candidate checks.

Standard library only. Does not import the relational search or Z3.
Timeouts remain recorded outcomes, not exclusion certificates.
"""
from pathlib import Path
import hashlib,json
from verify_frozen_candidates import rows_for,rank_of,f,decode,heldout,check_encryption
ROOT=Path(__file__).resolve().parent

def read(n):return json.loads((ROOT/n).read_bytes())
def sha(n):return hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
def dot(a,b):return sum(x*y for x,y in zip(a,b))%83

def verify(c,early,late,r):
    name=c['name'];info=r['parameterization'];width=83 if name=='add' else 166
    original=rows_for(c['ciphertext'],early)
    if name=='add':original=[[(row[j]+row[j+83])%83 for j in range(83)] for row in original]
    equations=[row+[0] for row in original]
    if name=='add':equations+=[[int(j==i) for j in range(width)]+[i] for i in [0,1]]
    assert info['original_rows']==original and info['augmented_rows']==equations and info['width']==width
    rank=rank_of([row[:-1] for row in equations]);base=info['particular'];directions=info['directions'];free=info['free_columns']
    assert info['rank']==rank and len(directions)==len(free)==width-rank
    assert all(dot(row[:-1],base)==row[-1] for row in equations)
    assert all(all(dot(row[:-1],v)==0 for row in equations) for v in directions)
    assert rank_of(directions)==len(directions)
    for i,j in enumerate(free):
        assert base[j]==0 and [v[j] for v in directions]==[int(i==k) for k in range(len(directions))]
    inactive=[j for j in range(width) if all(row[j]==0 for row in original)]
    omitted=[j for j in inactive if j>=83];columns=sorted(set(free)-set(omitted))
    assert info['inactive_columns']==inactive and r['omitted_inactive_feedback_columns']==omitted and r['solver_parameter_columns']==columns
    for j in omitted:
        assert j in free and directions[free.index(j)]==[int(i==j) for i in range(width)]
    largest=max([base[i]+sum(82*v[i] for v in directions) for i in range(width) if i not in set(columns)|set(omitted)],default=0)
    assert r['largest_linear_sum_bound']==largest<2**32
    truth=c['true_key'].copy()
    if name=='add':
        a=pow((truth[1]-truth[0])%83,81,83);truth=[(a*(x-truth[0]))%83 for x in truth]
    vector=truth if name=='add' else truth+[f(name,x) for x in truth]
    reconstructed=[(x+sum(vector[j]*v[i] for j,v in zip(free,directions)))%83 for i,x in enumerate(base)]
    assert reconstructed==vector
    d=decode(c['ciphertext'],name,truth);assert len({v for row in d[:6] for v in row[2:]})==27
    assert r['timeout_ms']==30000 and r['solver_seed']==83
    assert r['training_transitions']==sum(len(m)-2 for m in c['ciphertext'][:6])
    assert r['distinct_training_edges']==len({(m[t-1],m[t]) for m in c['ciphertext'][:6] for t in range(2,len(m))})
    if r['status']=='sat':
        key=r['key'];assert sorted(key)==list(range(83))
        if name=='add':assert key[0]==0 and key[1]==1
        values={int(j):v for j,v in r['parameter_values'].items()};assert sorted(values)==columns
        for i in range(83):assert key[i]==(base[i]+sum(values[j]*v[i] for j,v in zip(free,directions) if j in values))%83
        decoded=decode(c['ciphertext'],name,key);codes=sorted({v for row in decoded[:6] for v in row[2:]})
        assert codes==r['codebook'] and len(codes)<=27
        assert all(decoded[i][s+k]==decoded[j][t+k] for i,s,j,t,n in early for k in range(n))
        if r.get('negative_pair_cut'):
            a,b=r['negative_pair_cut'];assert key[a]+key[b]==83
    else:assert r['status']=='unknown' and r['reason_unknown'] and 'key' not in r
    return dict(name=name,status=r['status'],linear_rank=rank,affine_dimension=len(free),solver_parameters=len(columns),
        omitted_feedback_parameters=len(omitted),full_linear_space_verified=True,planted_key_inside_parameterization=True,
        largest_linear_sum_bound=largest,solve_seconds=r['solve_seconds'])

def main():
    source=read('frozen_candidate_search.json');data=read('relational_key_search.json');cut=read('relational_pair_cut.json')
    assert data['source_sha256']==cut['source_sha256']==sha('frozen_candidate_search.json')
    assert cut['proof_source_sha256']==sha('passage_domain_search.json')
    assert data['key_pins']==[] and data['function_supplied'] and not data['global_no_doubles_constraint']
    assert data['training_messages']==list(range(6)) and data['heldout_messages']==[6,7,8]
    out=dict(status='Independent relational-space and pair checks passed; no blind key recovered.',
        source_hashes={n:sha(n) for n in ['frozen_candidate_search.json','passage_domain_search.json','relational_key_search.json','relational_pair_cut.json']},
        controls=[],reencrypted_symbols=0)
    for c,entry in zip(source['controls'],data['controls']):
        assert c['seed']==entry['seed'];out['reencrypted_symbols']+=check_encryption(c,source['early_equalities'],source['late_equalities'])
        result=verify(c,source['early_equalities'],source['late_equalities'],entry['result']);out['controls'].append(result)
        if 'key' in entry['result']:
            r=entry['result'];assert entry['heldout']==heldout(c['ciphertext'],source['late_equalities'],c['name'],r['key'],r['codebook'])
        print(c['name'],result,flush=True)
    c=next(c for c in source['controls'] if c['seed']==cut['seed']);assert c['name']=='square'
    original=rows_for(c['ciphertext'],source['early_equalities']);combo=cut['combination'];row=cut['row'];a,b=cut['pair']
    assert len(combo)==len(original)
    assert row==[sum(w*r[j] for w,r in zip(combo,original))%83 for j in range(166)]
    assert {j for j,v in enumerate(row) if v}=={83+a,83+b} and (row[83+a]+row[83+b])%83==0
    pairs=[[x,y] for x in range(83) for y in range(83) if x!=y and x*x%83==y*y%83]
    assert pairs==cut['allowed_pairs']==[[x,83-x] for x in range(1,83)]
    assert c['true_key'][a]+c['true_key'][b]==83
    assert cut['result']['negative_pair_cut']==[a,b]
    out['pair_cut']=verify(c,source['early_equalities'],source['late_equalities'],cut['result'])
    out['pair_relation']=dict(labels=[a,b],distinct_pairs_before=83*82,pairs_after=len(pairs),
        possible_values_per_label=82,supplied_key_entries=0,ordered_pairs_checked=83**2)
    if 'key' in cut['result']:
        r=cut['result'];assert cut['heldout']==heldout(c['ciphertext'],source['late_equalities'],'square',r['key'],r['codebook'])
    (ROOT/'checked_relational_keys.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(out['status'],out['pair_relation'],flush=True)

if __name__=='__main__':main()
