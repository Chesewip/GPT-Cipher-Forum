"""Training-only domain pruning from partial output keys and an alphabet cap.

Every removed value has a replayable local reason. Truth is supplied only as
explicit pins in assisted tests; the blind test starts from no key hints.
"""
from pathlib import Path
import hashlib,json,time
from verify_frozen_candidates import f,decode,heldout
ROOT=Path(__file__).resolve().parent

def canonical(name,key):
    if name!='add':return key.copy()
    scale=pow((key[1]-key[0])%83,81,83)
    return [(x-key[0])*scale%83 for x in key]

def propagate(messages,name,pins):
    edges=sorted({(m[t-1],m[t]) for m in messages[:6] for t in range(2,len(m))})
    domains=[set(range(83)) for _ in range(83)]
    for j,v in pins:domains[j]={v}
    if name=='add':domains[0]={0};domains[1]={1}
    start_domains=[sorted(d) for d in domains]
    incident={j:[e for e in edges if j in e] for j in range(83)}
    fn=[f(name,x) for x in range(83)];trace=[];rounds=[]
    def fixed_codes():
        return {(next(iter(domains[b]))-fn[next(iter(domains[a]))])%83 for a,b in edges if len(domains[a])==len(domains[b])==1}
    initial_codes=sorted(fixed_codes());started=time.monotonic()
    while True:
        before=len(trace)
        for j in range(83):
            if len(domains[j])==1:continue
            fixed={next(iter(d)):i for i,d in enumerate(domains) if len(d)==1}
            codes=fixed_codes()
            assert len(codes)<=27
            for value in sorted(domains[j]):
                reason=None;witness=None
                if value in fixed:reason='used_value';witness=fixed[value]
                else:
                    local=set(codes)
                    for a,b in incident[j]:
                        if a==b:local.add((value-fn[value])%83)
                        elif a==j and len(domains[b])==1:local.add((next(iter(domains[b]))-fn[value])%83)
                        elif b==j and len(domains[a])==1:local.add((value-fn[next(iter(domains[a]))])%83)
                    if len(local)>27:reason='alphabet_cap'
                    elif len(codes)==27:
                        for a,b in incident[j]:
                            if a==b:supported=(value-fn[value])%83 in codes
                            elif a==j:supported=any((y-fn[value])%83 in codes for y in domains[b])
                            else:supported=any((value-fn[x])%83 in codes for x in domains[a])
                            if not supported:reason='edge_support';witness=[a,b];break
                if reason:
                    domains[j].remove(value);trace.append(dict(label=j,value=value,reason=reason,witness=witness))
            assert domains[j]
        rounds.append(dict(removed=len(trace)-before,singletons=sum(len(d)==1 for d in domains),known_codes=len(fixed_codes())))
        if len(trace)==before:break
    result=dict(initial_domains=start_domains,initial_codes=initial_codes,trace=trace,rounds=rounds,
        domains=[sorted(d) for d in domains],singletons=sum(len(d)==1 for d in domains),
        final_codes=sorted(fixed_codes()),seconds=time.monotonic()-started)
    if result['singletons']==83:result['key']=[next(iter(d)) for d in domains]
    return result

def main():
    raw=(ROOT/'frozen_candidate_search.json').read_bytes();source=json.loads(raw)
    joint_raw=(ROOT/'joint_feedback_constraints.json').read_bytes();joint=json.loads(joint_raw)
    out=dict(executed_date='2026-09-08',source_sha256=hashlib.sha256(raw).hexdigest(),
        joint_parent_sha256=hashlib.sha256(joint_raw).hexdigest(),status='Partial-key propagation calibration; no Eye key.',
        uses_early_equalities=False,global_no_doubles_constraint=False,controls=[])
    for c,old in zip(source['controls'],joint['controls']):
        truth=canonical(c['name'],c['true_key']);record=dict(seed=c['seed'],name=c['name'],runs=[]);out['controls'].append(record)
        for hidden in [8,24,40,56,83]:
            missing=set(old['hide_order'][:hidden]);pins=[[j,v] for j,v in enumerate(truth) if j not in missing]
            result=propagate(c['ciphertext'],c['name'],pins)
            entry=dict(hidden_labels=hidden,pins=pins,mode='blind_key' if hidden==83 else 'truth_assisted_partial_key',result=result)
            assert all(truth[j] in d for j,d in enumerate(result['domains']))
            if 'key' in result:
                assert result['key']==truth
                entry['heldout']=heldout(c['ciphertext'],source['late_equalities'],c['name'],result['key'],result['final_codes'])
            record['runs'].append(entry)
            print(c['name'],'hidden',hidden,'known codes',len(result['initial_codes']),'->',len(result['final_codes']),
                'key entries',83-hidden,'->',result['singletons'],'removed',len(result['trace']),flush=True)
    (ROOT/'propagate_feedback_domains.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
