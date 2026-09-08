"""Independent regular-reset certificate and phase-coverage verifier.

Standard library only. Reuses the earlier independent reverse-column kernel
checker, not the NumPy discovery elimination or phase grouping code.
"""
from pathlib import Path
import json,hashlib,itertools
from verify_recurrence_transfer import relation,kernel,normalized
ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()

def equation_data(messages,equalities):
    positions=[];rows=[]
    for i,s,j,t,n in equalities:
        for d in range(n):
            if min(s+d,t+d)<2:continue
            a,b=[i,s+d],[j,t+d];row=relation(messages,a,b)
            if any(row):positions.append([a,b]);rows.append(row)
    return positions,rows

def check_proofs(messages,equalities,saved):
    positions,rows=equation_data(messages,equalities)
    assert positions==saved['equation_positions'];masks=[]
    for proof in saved['proofs']:
        a,b=proof['labels'];assert 0<=a<83 and 0<=b<83 and a!=b
        result=[0]*83;mask=0
        for idx,coefficient in proof['terms']:
            assert 0<=idx<len(rows) and 0<coefficient<83 and not mask&(1<<idx)
            mask|=1<<idx;result=[(x+coefficient*y)%83 for x,y in zip(result,rows[idx])]
        target=[0]*83;target[a]=1;target[b]=82;assert result==target;masks.append(mask)
    return positions,rows,masks

def schedule_mask(positions,period,phases):
    mask=0
    for i,pair in enumerate(positions):
        reset=any((position-1)%period==phases[mi] for mi,position in pair)
        if not reset:mask|=1<<i
    return mask

def check_result(active,result,rows,proof_masks):
    assert result['active_equations']==active.bit_count()
    if result['status']=='forced_output_collision':
        required=proof_masks[result['proof_id']];assert active&required==required;return
    assert result['status']=='no_forced_collision'
    chosen=[row for i,row in enumerate(rows) if active&(1<<i)];rank,vs=kernel(chosen)
    assert rank==result['rank'] and len(vs)==result['nullity']
    signatures=[tuple(v[j] for v in vs) for j in range(83)];assert len(set(signatures))==83
    labels=[j for j in range(83) if any(row[j] for row in chosen)];missing=sorted(set(range(83))-set(labels))
    assert len(labels)-rank==result['active_nullity'] and missing==result['unconstrained_labels']
    if 'normalized_label_to_residue' in result:
        key=result['normalized_label_to_residue'];assert sorted(key)==list(range(83))
        assert result['active_nullity']==2 and len(missing)<=1
        a,b=result['anchor_labels'];assert [a,b]==labels[:2] and key[a]==0 and key[b]==1
        assert all(sum(x*y for x,y in zip(key,row))%83==0 for row in chosen)

def main():
    source=read('periodic_reset_screen.json');coverage=read('reset_phase_coverage.json');parent=read('state_memory_comparison.json');messages=list(read('ciphertext.json').values())
    for obj in [source,coverage]:
        assert obj['ciphertext_sha256']==sha('ciphertext.json') and obj['parent_sha256']==sha('state_memory_comparison.json')
    assert source['equalities']==parent['assumption_sets']['strong']
    assert coverage['equalities']==parent['assumption_sets']['early']
    out=dict(status='Independent checks passed; conditional exclusions only, no Eye key.',source_hashes={f:sha(f) for f in ['ciphertext.json','state_memory_comparison.json','periodic_reset_screen.json','reset_phase_coverage.json']})
    positions,rows,masks=check_proofs(messages,source['equalities'],source['real_certificates'])
    assert source['period_limit']==max(len(m)-1 for m in messages)==136
    settings=set();unresolved=[]
    for case in source['common_schedule_cases']:
        b,p=case['period'],case['phase'];assert (b,p) not in settings;settings.add((b,p))
        check_result(schedule_mask(positions,b,[p]*9),case,rows,masks)
        if case['status']=='no_forced_collision':unresolved.append([b,p])
    assert settings=={(b,p) for b in range(1,137) for p in range(b)}
    assert unresolved==[[1,0],[2,0],[2,1],[3,0],[3,1]]
    out['common_schedule']=dict(settings=len(settings),excluded=len(settings)-len(unresolved),unresolved=unresolved,certificate_library=len(masks))
    out['bounded_independent_phase_probes']=[]
    for probe in source['independent_phase_probes']:
        b=probe['period'];assert probe['phase_messages']==[1,2,6,7,8] and probe['limit']==1000
        expected=itertools.islice(itertools.product(range(b),repeat=5),1000)
        for i,(combo,case) in enumerate(zip(expected,probe['cases'])):
            phases=[0]*9
            for mi,p in zip(probe['phase_messages'],combo):phases[mi]=p
            assert phases==case['phases'];check_result(schedule_mask(positions,b,phases),case,rows,masks)
            if i+1<len(probe['cases']):assert case['status']=='forced_output_collision'
        assert len(probe['cases'])==1000 or probe['cases'][-1]['status']=='no_forced_collision'
        out['bounded_independent_phase_probes'].append(dict(period=b,tested=len(probe['cases']),last_status=probe['cases'][-1]['status']))
    out['controls']=[];control_proofs=0
    for c in source['controls']:
        key=c['true_label_to_residue'];assert sorted(key)==list(range(83));steps=c['input_steps'];assert len(set(steps))==len(steps)==27 and all(0<s<83 for s in steps)
        for initial,ct,pt,jumps in zip(c['initial_residues'],c['ciphertext'],c['plaintext'],c['resets']):
            assert len(ct)==len(pt);assert [t for t,state in jumps]==[t for t in range(1,len(ct)) if (t-1)%c['period']==c['phase']]
            reset=dict(jumps);state=initial
            for t in range(1,len(ct)):
                state=reset.get(t,state);state=(state+steps[pt[t]])%83;assert key[ct[t]]==state
        for i,s,j,t,n in c['equalities']:assert c['plaintext'][i][s:s+n]==c['plaintext'][j][t:t+n]
        ps,rs,proofs=check_proofs(c['ciphertext'],c['equalities'],c['certificates']);control_proofs+=len(proofs);seen=set();survivors=[]
        for case in c['cases']:
            b,p=case['period'],case['phase'];assert (b,p) not in seen;seen.add((b,p))
            check_result(schedule_mask(ps,b,[p]*9),case,rs,proofs)
            if case['status']=='no_forced_collision':survivors.append([b,p])
        assert seen=={(b,p) for b in range(1,33) for p in range(b)}
        assert survivors==[[1,0],[c['period'],c['phase']]]
        correct=next(r for r in c['cases'] if [r['period'],r['phase']]==survivors[1]);recovered=correct['normalized_label_to_residue'];assert recovered==normalized(key,correct['anchor_labels'])
        a,b=correct['anchor_labels'];scale=pow((key[b]-key[a])%83,-1,83);checked=0
        for ct,pt in zip(c['ciphertext'],c['plaintext']):
            for t in range(2,len(ct)):
                if (t-1)%c['period']==c['phase']:continue
                assert (recovered[ct[t]]-recovered[ct[t-1]])%83==steps[pt[t]]*scale%83;checked+=1
        out['controls'].append(dict(seed=c['seed'],settings=len(seen),unresolved=survivors,recovered_map_entries=83,nonreset_increment_checks=checked))
    ps,rs,proofs=check_proofs(messages,coverage['equalities'],coverage['certificates'])
    assert coverage['period_limit']==136 and [p['period'] for p in coverage['periods']]==list(range(1,137))
    all_mask=(1<<len(ps))-1;seen_masks=set()
    for item in coverage['patterns']:
        active=int(item['active_mask'],16);assert active not in seen_masks;seen_masks.add(active)
        check_result(active,item['result'],rs,proofs)
    counted=0;surviving=[]
    for item in coverage['periods']:
        b=item['period'];collections=[item['W1_groups'],item['E2_groups']]
        for mi,groups in zip([1,2],collections):
            phases=[];removed_seen=set()
            for group in groups:
                removed=int(group['removed_mask'],16);assert removed not in removed_seen;removed_seen.add(removed)
                for phase in group['phases']:
                    assert 0<=phase<b;phases.append(phase)
                    actual=sum(1<<i for i,pair in enumerate(ps) if any(m==mi and (t-1)%b==phase for m,t in pair))
                    assert actual==removed
            assert sorted(phases)==list(range(b))
        pairs=list(itertools.product(*collections));assert len(pairs)==len(item['pattern_indices'])
        for (left,right),idx in zip(pairs,item['pattern_indices']):
            active=all_mask^(int(left['removed_mask'],16)|int(right['removed_mask'],16));record=coverage['patterns'][idx];assert int(record['active_mask'],16)==active
            counted+=len(left['phases'])*len(right['phases'])
            if record['result']['status']=='no_forced_collision':surviving.extend([b,a,c] for a,c in itertools.product(left['phases'],right['phases']))
    assert counted==coverage['phase_pairs_covered']==sum(b*b for b in range(1,137))==847756
    assert sorted(surviving)==coverage['unresolved_phase_pairs'] and len(surviving)==39
    out['independent_early_phase_coverage']=dict(phase_pairs=counted,excluded=counted-len(surviving),unresolved=sorted(surviving),unique_equation_systems=len(coverage['patterns']),certificates=len(proofs))
    out['total_certificate_checks']=len(masks)+control_proofs+len(proofs)
    (ROOT/'checked_periodic_resets.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
