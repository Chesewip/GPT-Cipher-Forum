"""Independent modular row certificates and domain-deletion replay.

Standard library only. No imports from the new search implementation.
Finite search limits are reported outcomes, never verified exclusions.
"""
from pathlib import Path
from collections import Counter
import hashlib,json
from verify_frozen_candidates import rows_for,rank_of,f,decode,heldout,check_encryption
ROOT=Path(__file__).resolve().parent

def read(n):return json.loads((ROOT/n).read_bytes())
def sha(n):return hashlib.sha256((ROOT/n).read_bytes()).hexdigest()
def truth_for(c):
    key=c['true_key']
    if c['name']!='add':return key.copy()
    a=pow((key[1]-key[0])%83,81,83)
    return [(a*(x-key[0]))%83 for x in key]

def verify_equations(messages,eq,name,saved):
    original=rows_for(messages,eq)
    if name=='add':original=[[(r[j]+r[j+83])%83 for j in range(83)] for r in original]
    assert original==saved['original_rows']
    rows=saved['rows'];combinations=saved['combinations']
    assert len(rows)==len(combinations)==rank_of(original)==rank_of(rows)
    for row,combo in zip(rows,combinations):
        assert len(combo)==len(original)
        assert row==[sum(a*r[j] for a,r in zip(combo,original))%83 for j in range(len(row))]
    return rows

def replay(messages,name,rows,pins,saved,truth,alphabet):
    domains=[set(range(83)) for _ in range(83)]
    for j,value in pins:domains[j]={value}
    if name=='add':domains[0]={0};domains[1]={1}
    initial_fixed=sum(len(d)==1 for d in domains)
    edges={(m[t-1],m[t]) for m in messages[:6] for t in range(2,len(m))}
    terms=[]
    for row in rows:
        terms.append([(j,row[j],row[j+83] if len(row)>83 else 0) for j in range(83)
            if row[j] or (len(row)>83 and row[j+83])])
    cache={};counts=Counter()
    for event in saved['trace']:
        j,value,reason=event['label'],event['value'],event['reason']
        assert value in domains[j] and value!=truth[j]
        if reason=='permutation':
            assert any(i!=j and d=={value} for i,d in enumerate(domains))
        elif reason=='alphabet_cap':
            assert alphabet
            trial={i:next(iter(d)) for i,d in enumerate(domains) if len(d)==1};trial[j]=value
            codes={(trial[b]-f(name,trial[a]))%83 for a,b in edges if a in trial and b in trial}
            assert len(codes)>27
        elif reason=='passage_row':
            index=event['witness'];rowterms=terms[index]
            own=next((a,b) for i,a,b in rowterms if i==j)
            # Domain changes to the tested variable do not invalidate support
            # sums for the other variables. Cache those sums during replay.
            signature=(index,j,tuple((i,tuple(sorted(domains[i]))) for i,a,b in rowterms if i!=j))
            if signature not in cache:
                possible={0}
                for i,a,b in rowterms:
                    if i==j:continue
                    values={(a*x+b*f(name,x))%83 for x in domains[i]}
                    possible={(x+y)%83 for x in possible for y in values}
                    if len(possible)==83:break
                cache[signature]=possible
            target=-(own[0]*value+own[1]*f(name,value))%83
            assert target not in cache[signature]
        else:raise AssertionError(reason)
        domains[j].remove(value);assert domains[j];counts[reason]+=1
    assert dict(counts)==saved['reason_counts'] and [sorted(d) for d in domains]==saved['domains']
    assert saved['status']=='fixed_point' and saved['contradiction'] is None
    assert saved['singletons']==sum(len(d)==1 for d in domains)
    assert all(truth[j] in d for j,d in enumerate(domains))
    result=dict(initial_singletons=initial_fixed,final_singletons=saved['singletons'],deleted_values=sum(counts.values()),reasons=dict(counts))
    if result['final_singletons']==83:
        key=[next(iter(d)) for d in domains];assert key==truth and sorted(key)==list(range(83))
        decoded=decode(messages,name,key);codes=sorted({x for row in decoded[:6] for x in row[2:]})
        assert len(codes)==27;result['key']=key;result['codebook']=codes
    return result

def search_record(r,messages,early,name):
    assert 0<r['nodes']<=r['node_limit'] and 0<=r['contradiction_nodes']<=r['nodes']
    if r['status']=='candidate':
        key=r['key'];assert sorted(key)==list(range(83))
        if name=='add':assert key[0]==0 and key[1]==1
        d=decode(messages,name,key);code=sorted({x for row in d[:6] for x in row[2:]})
        assert code==r['codebook'] and len(code)<=27
        assert all(d[i][s+k]==d[j][t+k] for i,s,j,t,n in early for k in range(n))
        assert all(key[j]==value for j,value in r['branch_choices'])
    else:
        assert r['status']=='budget_exhausted' and 'key' not in r
        assert r['nodes']==r['node_limit'] or r['elapsed_seconds']>=r['seconds_budget']
    return {k:v for k,v in r.items() if k not in ['key','codebook','branch_choices']}

def main():
    source=read('frozen_candidate_search.json');masks=read('joint_feedback_constraints.json')
    data=read('passage_domain_search.json');extended=read('passage_domain_extended.json');old=read('propagate_feedback_domains.json')
    assert data['source_sha256']==extended['source_sha256']==sha('frozen_candidate_search.json')
    assert data['mask_parent_sha256']==sha('joint_feedback_constraints.json') and extended['parent_sha256']==sha('passage_domain_search.json')
    assert old['source_sha256']==sha('frozen_candidate_search.json') and old['joint_parent_sha256']==sha('joint_feedback_constraints.json')
    out=dict(status='Independent passage-row and deletion checks passed; no blind control key recovered.',
        source_hashes={n:sha(n) for n in ['frozen_candidate_search.json','joint_feedback_constraints.json','propagate_feedback_domains.json','passage_domain_search.json','passage_domain_extended.json']},
        controls=[],reencrypted_symbols=0)
    for c,mask,saved,extra,prior in zip(source['controls'],masks['controls'],data['controls'],extended['controls'],old['controls']):
        assert c['seed']==mask['seed']==saved['seed']==extra['seed']==prior['seed']
        name=c['name'];truth=truth_for(c);messages=c['ciphertext'];early=source['early_equalities'];late=source['late_equalities']
        out['reencrypted_symbols']+=check_encryption(c,early,late)
        rows=verify_equations(messages,early,name,saved['equations'])
        row=dict(name=name,seed=c['seed'],verified_rank=len(rows),blind_root=replay(messages,name,rows,[],saved['blind_root'],truth,True),
            initial_search=search_record(saved['blind_search'],messages,early,name),extended_search=search_record(extra['result'],messages,early,name))
        assisted=saved['assisted_27_pins'];missing=set(mask['hide_order'][:56]);pins=[[j,v] for j,v in enumerate(truth) if j not in missing]
        assert assisted['pins']==pins and len(pins)==27
        old_case=next(r for r in prior['runs'] if r['hidden_labels']==56);assert old_case['pins']==pins
        row['alphabet_only_fixed']=old_case['result']['singletons'];row['assisted']={}
        for mode in ['passages_only','passages_and_alphabet']:
            result=replay(messages,name,rows,pins,assisted[mode],truth,mode=='passages_and_alphabet')
            if 'key' in result:
                key=result.pop('key');code=result.pop('codebook');h=heldout(messages,late,name,key,code)
                assert h==assisted[mode]['heldout'] and h['outside_frozen_codebook']==h['late_pair_mismatches']==0
                result['true_key_recovered']=True;result['heldout']={k:v for k,v in h.items() if k!='decoded_residues'}
            row['assisted'][mode]=result
        out['controls'].append(row)
        print(name,'independent checks passed;',row['extended_search']['status'],
            {m:r['final_singletons'] for m,r in row['assisted'].items()},flush=True)
    (ROOT/'checked_passage_domains.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(out['status'],flush=True)

if __name__=='__main__':main()
