"""Use the output map's bijection after the linear repeated-passage solve.

An unconstrained last label is determined by the one unused residue. More
unconstrained labels remain ambiguous without extra model information.
"""
from pathlib import Path
import json,hashlib,math
from recurrence_transfer_audit import equations,basis,control
ROOT=Path(__file__).resolve().parent

def refine(c):
    rows=[e['row'] for e in equations(c['ciphertext'],c['equalities'])]
    active=[j for j in range(83) if any(row[j] for row in rows)];inactive=sorted(set(range(83))-set(active))
    bs=basis(rows);free=[j for j in active if j not in bs]
    out=dict(active_labels=active,unconstrained_labels=inactive,rank=len(bs),active_nullity=len(free),status='additional_linear_freedom')
    if len(free)!=2:return out
    vectors=[]
    for j in free:
        v=[0]*83;v[j]=1
        for p,(row,_) in sorted(bs.items(),reverse=True):v[p]=-sum(row[k]*v[k] for k in range(p+1,83))%83
        vectors.append(v)
    a,b=active[:2];v=next(v for v in vectors if v[a]!=v[b]);scale=pow((v[b]-v[a])%83,-1,83)
    partial={j:((v[j]-v[a])*scale)%83 for j in active}
    assert len(set(partial.values()))==len(active)
    remaining=sorted(set(range(83))-set(partial.values()))
    out.update(anchor_labels=[a,b],normalized_active_map=partial,unused_residues=remaining,
               permutation_completions_with_anchors_fixed=str(math.factorial(len(inactive))))
    if len(inactive)<=1:
        key=[partial[j] if j in partial else remaining[0] for j in range(83)]
        out.update(status='unique_bijective_map_up_to_affine_change',normalized_label_to_residue=key)
    else:out['status']='active_map_recovered_unconstrained_label_permutations_remain'
    return out

def main():
    raw=(ROOT/'recurrence_transfer_audit.json').read_bytes();source=json.loads(raw)
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    prior=json.loads((ROOT/'state_memory_comparison.json').read_text())
    fresh=control(messages,prior['assumption_sets']['full_prefix'],909430,True)
    out=dict(status='Generated-key calibration, not an Eye decipherment.',source_sha256=hashlib.sha256(raw).hexdigest(),prior_controls=[],fresh_control=fresh)
    for c in source['controls']:
        result=refine(c);out['prior_controls'].append(dict(seed=c['seed'],result=result))
        print(c['seed'],result['status'],'active nullity',result['active_nullity'],'unused labels',result['unconstrained_labels'])
    out['fresh_result']=refine(fresh);print('Fresh',fresh['seed'],out['fresh_result']['status'])
    (ROOT/'cyclic_permutation_refinement.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
