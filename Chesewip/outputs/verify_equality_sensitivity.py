"""Independent row certificates, combinatorial bounds and generated recovery.

No discovery imports. Standard-library hitting-set search checks lower bounds;
prior independent reverse-column linear algebra checks surviving systems.
"""
from pathlib import Path
from collections import Counter
import hashlib,itertools,json
from verify_recurrence_transfer import kernel,normalized
ROOT=Path(__file__).resolve().parent

def read(name):return json.loads((ROOT/name).read_bytes())
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()

def prepare(messages,equalities,metric):
    graph={}
    for i,s,j,t,n in equalities:
        for d in range(n):
            a,b=(i,s+d),(j,t+d);graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    remaining=set(graph);groups=[]
    while remaining:
        todo=[min(remaining)];seen=set(todo)
        while todo:
            for v in graph[todo.pop()]:
                if v not in seen:seen.add(v);todo.append(v)
        remaining-=seen;groups.append([list(p) for p in sorted(seen)])
    groups.sort();positions=sorted(graph);index={p:i for i,p in enumerate(positions)}
    units=groups if metric=='columns' else [list(p) for p in positions];rows=[];row_units=[];row_positions=[]
    for gi,g in enumerate(groups):
        for a,b in itertools.combinations(g,2):
            row=[0]*83
            for (mi,t),sgn in zip([a,b],[1,-1]):
                assert t>=2;row[messages[mi][t]]+=sgn;row[messages[mi][t-1]]-=sgn
            rows.append([v%83 for v in row]);row_positions.append([a,b])
            row_units.append([gi] if metric=='columns' else [index[tuple(a)],index[tuple(b)]])
    return groups,units,rows,row_units,row_positions

def bits(mask):
    while mask:
        bit=mask&-mask;yield bit.bit_length()-1;mask-=bit

def has_small_hitting_set(clauses,budget):
    ordered=sorted(set(clauses),key=lambda m:(m.bit_count(),m));masks=[]
    for m in ordered:
        if not any(m&n==n for n in masks):masks.append(m)
    incidence={}
    for i,m in enumerate(masks):
        for u in bits(m):incidence[u]=incidence.get(u,0)|(1<<i)
    failed={};nodes=0
    def visit(left,k):
        nonlocal nodes
        nodes+=1
        if not left:return []
        if k<=0:return None
        if failed.get(left,-1)>=k:return None
        used=0;packing=0;first=None
        for i in bits(left):
            m=masks[i]
            if first is None:first=i
            if not m&used:
                used|=m;packing+=1
                if packing>k:failed[left]=k;return None
        coverage=[]
        for u in bits(masks[first]):
            cover=incidence[u]&left
            if any(cover&v==cover for _,v in coverage):continue
            coverage=[(w,v) for w,v in coverage if v&cover!=v];coverage.append((u,cover))
        for u,cover in sorted(coverage,key=lambda pair:-pair[1].bit_count()):
            answer=visit(left&~cover,k-1)
            if answer is not None:return [u]+answer
        failed[left]=k;return None
    answer=visit((1<<len(masks))-1,budget)
    return answer,dict(minimal_clauses=len(masks),search_nodes=nodes)

def active_rows(groups,units,rows,row_units,row_positions,metric,dropped):
    dropped=set(dropped);selected=[]
    for g in groups:
        if metric=='columns':good=[] if units.index(g) in dropped else g
        else:good=[p for p in g if units.index(p) not in dropped]
        if good:selected.extend([[good[0],b] for b in good[1:]])
    indices=[row_positions.index(ps) for ps in selected]
    assert all(not dropped.intersection(row_units[i]) for i in indices)
    return [rows[i] for i in indices]

def check_survivor(rows,r):
    rank,vs=kernel(rows);assert r['rank']==rank and r['nullity']==83-rank
    assert len({tuple(v[j] for v in vs) for j in range(83)})==83
    active=sorted({j for row in rows for j,v in enumerate(row) if v})
    assert r['status']=='no_forced_collision' and r['unconstrained_labels']==sorted(set(range(83))-set(active))
    assert r['active_nullity']==len(active)-rank
    if 'normalized_label_to_residue' in r:
        key=r['normalized_label_to_residue'];assert sorted(key)==list(range(83)) and len(active)-rank==2 and len(active)>=82
        assert key==normalized(key,r['anchor_labels']) and all(sum(x*y for x,y in zip(key,row))%83==0 for row in rows)
    return rank,vs

def check_case(messages,equalities,r,column_bound=0):
    metric=r['metric'];g,units,rows,us,ps=prepare(messages,equalities,metric)
    assert g==r['groups'] and units==r['units'];clauses=[]
    for proof in r['proofs']:
        total=[0]*83;needed=set();a,b=proof['labels'];assert a!=b
        for i,c in proof['terms']:
            assert 0<c<83;total=[(x+c*y)%83 for x,y in zip(total,rows[i])];needed.update(us[i])
        target=[0]*83;target[a]=1;target[b]=82;assert total==target and sorted(needed)==proof['units']
        clauses.append(sum(1<<u for u in needed))
    bound=r.get('minimum',r.get('lower_bound'))
    external=r.get('column_lower_bound',0);assert external<=column_bound
    if bound>column_bound:
        hit,stats=has_small_hitting_set(clauses,bound-1);assert hit is None
    else:stats=dict(bound_inherited_from_verified_column_minimum=column_bound)
    if r['status']=='exact_minimum_for_no_forced_collision':
        assert len(set(r['dropped']))==len(r['dropped'])==bound
        chosen=sum(1<<u for u in r['dropped']);assert all(chosen&m for m in clauses)
        rs=active_rows(g,units,rows,us,ps,metric,r['dropped']);check_survivor(rs,r['result'])
    else:assert r['status']=='bounded_search_incomplete'
    return dict(status=r['status'],minimum_or_lower_bound=bound,proofs=len(clauses),lower_bound_check=stats)

def main():
    s=read('equality_sensitivity.json');messages=list(read('ciphertext.json').values());parent=read('state_memory_comparison.json')['assumption_sets']
    assert s['ciphertext_sha256']==sha('ciphertext.json') and s['parent_sha256']==sha('state_memory_comparison.json')
    assert s['assumption_sets']=={name:parent[name] for name in ['early','late','strong']}
    out=dict(status='Independent sensitivity checks passed; no authentic Eye key.',source_hashes={name:sha(name) for name in ['ciphertext.json','state_memory_comparison.json','equality_sensitivity.json']},real={},controls=[])
    for name,rs in s['real'].items():
        out['real'][name]={}
        for metric,r in rs.items():
            print('Checking',name,metric,flush=True)
            cb=rs['columns']['minimum'] if metric=='occurrences' else 0
            out['real'][name][metric]=check_case(messages,parent[name],r,cb)
            print(out['real'][name][metric],flush=True)
    out['refinements']={}
    for name in ['equality_sensitivity_refinement.json','equality_sensitivity_sat.json']:
        record=read(name);assert record['parent_sha256']==sha('equality_sensitivity.json');out['source_hashes'][name]=sha(name)
        print('Checking',name,flush=True)
        out['refinements'][name]=check_case(messages,parent['strong'],record['result'],s['real']['strong']['columns']['minimum'])
    for c in s['controls']:
        key=c['true_label_to_residue'];steps=c['input_steps'];assert sorted(key)==list(range(83)) and len(set(steps))==len(steps)==27 and all(0<v<83 for v in steps)
        for defect in c['corrupted']:
            mi,t=defect['position'];assert c['plaintext'][mi][t]==defect['replacement'] and defect['replacement']!=defect['original']
        count=0
        for pt,ct,state in zip(c['plaintext'],c['ciphertext'],c['initial_states']):
            assert len(pt)==len(ct)
            for t in range(1,len(pt)):state=(state+steps[pt[t]])%83;assert key[ct[t]]==state;count+=1
        item=dict(seed=c['seed'],body_symbols_reencrypted=count,results={})
        for metric,r in c['results'].items():
            item['results'][metric]=check_case(c['ciphertext'],c['equalities'],r,c['results']['columns']['minimum'] if metric=='occurrences' else 0)
            recovered=r['result']['normalized_label_to_residue'];assert recovered==normalized(key,r['result']['anchor_labels'])
            groups=prepare(c['ciphertext'],c['equalities'],metric)[0];outliers=[];bad_columns=[]
            for gi,g in enumerate(groups):
                values=[(recovered[c['ciphertext'][mi][t]]-recovered[c['ciphertext'][mi][t-1]])%83 for mi,t in g]
                common,n=Counter(values).most_common(1)[0]
                if n<len(g):bad_columns.append(gi)
                outliers.extend(p for p,value in zip(g,values) if value!=common)
            assert sorted(outliers)==sorted(d['position'] for d in c['corrupted'])
            expected=bad_columns if metric=='columns' else [r['units'].index(p) for p in outliers]
            assert sorted(r['dropped'])==sorted(expected) and r['minimum']==len(c['corrupted'])
            item['results'][metric].update(map_entries_recovered=83,identified_fault_positions=sorted(outliers))
        out['controls'].append(item)
    audit=read('sensitivity_witness_audit.json');assert audit['parent_sha256']==sha('equality_sensitivity.json');out['source_hashes']['sensitivity_witness_audit.json']=sha('sensitivity_witness_audit.json')
    r=s['real']['strong']['columns'];g,units,rows,us,ps=prepare(messages,parent['strong'],'columns');rs=active_rows(g,units,rows,us,ps,'columns',r['dropped'])
    rank,vs=check_survivor(rs,r['result']);a=audit['joint_column_map'];active=sorted({j for row in rs for j,x in enumerate(row) if x})
    assert a['active_labels']==active and a['inactive_labels']==sorted(set(range(83))-set(active));x,y=a['anchors'];assert [x,y]==active[:2]
    base=a['particular'];directions=a['directions'];assert len(directions)==len(active)-rank-2==1
    assert base[x]==0 and base[y]==1 and all(sum(v*w for v,w in zip(base,row))%83==0 for row in rs)
    for v in directions:
        assert v[x]==v[y]==0 and any(v) and all(sum(k*w for k,w in zip(v,row))%83==0 for row in rs)
    assert all(v[j]==0 for v in [base]+directions for j in a['inactive_labels'])
    combos=list(itertools.product(range(83),repeat=len(directions)));assert len(combos)==a['candidates']==len(a['collision_pairs'])==83
    for co,pair in zip(combos,a['collision_pairs']):
        v=[(base[j]+sum(c*w[j] for c,w in zip(co,directions)))%83 for j in range(83)]
        assert pair and pair[0]!=pair[1] and set(pair)<=set(active) and v[pair[0]]==v[pair[1]]
    assert a['injective_candidates']==[]
    out['saved_column_witness_bijection_audit']=dict(active_labels=len(active),normalized_candidates=83,injective_candidates=0,all_completions_excluded_for_this_drop_set=True)
    gg,uu,rr,ru,rp=prepare(messages,parent['strong'],'occurrences')
    for pilot in audit['occurrence_pilots']:
        check_survivor(active_rows(gg,uu,rr,ru,rp,'occurrences',pilot['dropped']),pilot['result'])
    upper=min(len(p['dropped']) for p in audit['occurrence_pilots']);assert upper==audit['best_occurrence_upper_bound']
    out['joint_occurrence_linear_upper_bound']=upper
    (ROOT/'checked_equality_sensitivity.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
