"""Independent exhaustive audit and constraint ablation, standard library only.

Does not import the sparse discovery implementation. Enumerates complete
missing-label permutations rather than using its partial-codebook DFS.
"""
from pathlib import Path
import hashlib,itertools,json,math
from verify_frozen_candidates import rows_for,rank_of,f,decode,heldout,check_encryption
ROOT=Path(__file__).resolve().parent

def read(name):return json.loads((ROOT/name).read_bytes())
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
def dot(a,b):return sum(x*y for x,y in zip(a,b))%83

def audit(messages,eq,r):
    rows=rows_for(messages,eq);info=r['fiber'];assert info['status']=='normalized_affine_fiber'
    inactive=[j for j in range(166) if all(row[j]==0 for row in rows)]
    common=[j for j in range(83) if j not in inactive and j+83 not in inactive]
    a,b=common[:2];fixed=[(a,0),(b,1),(a+83,0)]+[(j,0) for j in inactive]
    assert info['anchors']==[a,b] and info['inactive_columns']==inactive
    anchors=[[int(i==j) for i in range(166)] for j,_ in fixed]
    dimension=166-rank_of(rows+anchors)
    base=info['particular'];directions=info['directions']
    assert info['nonzero_rows']==len(rows) and info['normalized_dimension']==dimension==len(directions)
    assert rank_of(directions)==dimension
    assert all(dot(row,base)==0 for row in rows) and all(base[j]==value for j,value in fixed)
    assert all(all(dot(row,v)==0 for row in rows) and all(v[j]==0 for j,_ in fixed) for v in directions)
    out=dict(linear_rank=rank_of(rows),inactive_output_labels=sum(j<83 for j in inactive),
             inactive_feedback_labels=sum(j>=83 for j in inactive),normalized_active_dimension=dimension,status=r['status'])
    if dimension>r['dimension_budget']:
        assert r['status']=='outside_enumeration_budget' and 'candidates' not in r
        return out
    assert r['status']=='enumerated_candidates' and r['fibers_tested']==83**dimension
    active=[j for j in range(83) if j not in inactive];missing=[j for j in range(83) if j in inactive]
    assert len(missing)<=r['missing_label_budget']
    fibers=[];link_counts={n:0 for n in ['add','square','inverse']};candidates=[];ablation=[]
    edges=sorted({(m[t-1],m[t]) for m in messages[:6] for t in range(2,len(m))})
    for coeff in itertools.product(range(83),repeat=dimension):
        vector=[(x+sum(c*v[j] for c,v in zip(coeff,directions)))%83 for j,x in enumerate(base)]
        u,v=vector[:83],vector[83:]
        if len({u[j] for j in active})!=len(active):continue
        fibers.append(list(coeff))
        for name in link_counts:
            parameters=[(1,0)] if name=='add' else itertools.product(range(1,83),range(83))
            for scale,shift in parameters:
                if any((f(name,(scale*u[j]+shift)%83)-scale*v[j])%83!=f(name,shift) for j in common):continue
                link_counts[name]+=1;key=[None]*83
                for j in active:key[j]=(scale*u[j]+shift)%83
                unused=sorted(set(range(83))-{key[j] for j in active})
                allowed=set(range(83))-{(x-f(name,x))%83 for x in range(83)}
                counts=dict(permutations=math.factorial(len(missing)),after_feedback=0,after_cap_without_global_no_doubles=0,after_global_no_doubles=0,after_codebook_cap=0)
                hist={};all_hist={}
                for perm in itertools.permutations(unused):
                    for j,value in zip(missing,perm):key[j]=value
                    if any(j+83 not in inactive and (f(name,key[j])-scale*v[j])%83!=f(name,shift) for j in missing):continue
                    counts['after_feedback']+=1
                    code={(key[y]-f(name,key[x]))%83 for x,y in edges}
                    all_hist[len(code)]=all_hist.get(len(code),0)+1
                    if len(code)<=27:counts['after_cap_without_global_no_doubles']+=1
                    if not code<=allowed:continue
                    counts['after_global_no_doubles']+=1;hist[len(code)]=hist.get(len(code),0)+1
                    if len(code)>27:continue
                    counts['after_codebook_cap']+=1
                    candidates.append(dict(name=name,key=key.copy(),codebook=sorted(code),coefficients=list(coeff),scale=scale,shift=shift))
                ablation.append(dict(name=name,coefficients=list(coeff),scale=scale,shift=shift,counts=counts,
                    codebook_size_histogram_before_global_no_doubles=all_hist,
                    codebook_size_histogram_after_global_no_doubles=hist))
    candidates.sort(key=lambda c:(c['name'],c['key']))
    assert fibers==r['injective_output_fibers'] and link_counts==r['link_counts']
    assert candidates==r['candidates'] and r['selected_candidate']==(0 if candidates else None)
    for c in candidates:
        assert sorted(c['key'])==list(range(83))
        d=decode(messages,c['name'],c['key'])
        assert all(d[i][s+k]==d[j][t+k] for i,s,j,t,n in eq for k in range(n))
    out.update(fibers_tested=83**dimension,injective_fibers=len(fibers),link_counts=link_counts,
               candidates=len(candidates),ablation=ablation)
    return out

def main():
    sparse=read('sparse_map_completion.json');rich=read('lifted_feedback_recovery.json');short=read('frozen_candidate_search.json')
    assert sparse['rich_parent_sha256']==sha('lifted_feedback_recovery.json')
    assert sparse['short_parent_sha256']==sha('frozen_candidate_search.json')
    sets=read('state_memory_comparison.json')['assumption_sets'];eye=list(read('ciphertext.json').values())
    assert short['early_equalities']==rich['eye_training_equalities']==sets['early']
    for source in [short,rich]:
        assert source['ciphertext_sha256']==sha('ciphertext.json') and source['parent_sha256']==sha('state_memory_comparison.json')
    out=dict(status='Independent sparse completion and ablation checks passed; no Eye key.',
        source_hashes={n:sha(n) for n in ['sparse_map_completion.json','lifted_feedback_recovery.json','frozen_candidate_search.json','ciphertext.json','state_memory_comparison.json']},
        rich_controls=[],short_controls=[],reencrypted_symbols=0)
    by_seed={c['seed']:c for c in rich['controls']}
    for c in rich['controls']:out['reencrypted_symbols']+=check_encryption(c,c['training_equalities'],c['late_equalities'])
    for entry in sparse['controls']:
        c=by_seed[entry['seed']];eq=c['training_equalities'][:entry['blocks']*5]
        assert entry['training_equalities']==eq and entry['true_name']==c['name']
        assert all(i<6 and j<6 for i,s,j,t,n in eq)
        result=audit(c['ciphertext'],eq,entry['result']);result.update(name=c['name'],seed=c['seed'],blocks=entry['blocks'])
        if entry['result'].get('selected_candidate') is not None:
            chosen=entry['result']['candidates'][0];key=chosen['key'];truth=c['true_key']
            assert chosen['name']==c['name']
            if c['name']=='add':
                scale=(key[1]-key[0])*pow((truth[1]-truth[0])%83,81,83)%83;shift=(key[0]-scale*truth[0])%83
                assert scale and key==[(scale*x+shift)%83 for x in truth]
            elif c['name']=='square':assert key==truth
            else:assert key==truth or key==[(-x)%83 for x in truth]
            h=heldout(c['ciphertext'],c['late_equalities'],c['name'],key,chosen['codebook'])
            assert entry['heldout']==h and h['outside_frozen_codebook']==h['late_pair_mismatches']==0
            assert len(chosen['codebook'])==27
            result.update(true_rule_and_equivalent_key_recovered=True,heldout={k:v for k,v in h.items() if k!='decoded_residues'})
        out['rich_controls'].append(result)
        print(c['name'],entry['blocks'],json.dumps(result),flush=True)
    for entry,c in zip(sparse['short_controls'],short['controls']):
        assert entry['seed']==c['seed'];out['reencrypted_symbols']+=check_encryption(c,sets['early'],sets['late'])
        result=audit(c['ciphertext'],sets['early'],entry['result']);result.update(seed=c['seed'],name=c['name']);out['short_controls'].append(result)
    out['eye']=audit(eye,sets['early'],sparse['eye'])
    (ROOT/'checked_sparse_completion.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(out['status'],out['eye'],flush=True)

if __name__=='__main__':main()
