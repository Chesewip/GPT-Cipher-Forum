"""Combine exact certificates to cover every affine shuffle modulo 83.

Model: arbitrary common initial deck; swap selected position with Q^-1(0),
apply Q, output top; Q(x)=a*x+b (mod 83). Fixed selection alphabet <=40.
Does not cover extra swaps, changing shuffles, or variable letter encodings.
"""
from pathlib import Path
from collections import Counter
import json
ROOT=Path(__file__).resolve().parent

def cycles(q):
    unseen=set(range(len(q)));out=[]
    while unseen:
        start=min(unseen);cycle=[];v=start
        while v in unseen:
            unseen.remove(v);cycle.append(v);v=q[v]
        out.append(cycle)
    return out

def main():
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    assert set(c for m in messages for c in m)==set(range(83))
    gaps=set()
    for m in messages:
        last={}
        for t,c in enumerate(m):
            if c in last:gaps.add(t-last[c])
            last[c]=t
    single=json.loads((ROOT/'checked_cycle_subset_10_44.json').read_text())
    assert single['passed'] and single['all_83_rechecked']
    assert len(single['results'])==83 and {r['top'] for r in single['results']}==set(range(83))
    assert all(r['status']=='unsat' and r['target_alphabet']==44 for r in single['results'])
    split=json.loads((ROOT/'checked_multicycle_bound_1_41_41_40.json').read_text())
    assert split['passed']
    groups={}
    for a in range(1,83):
        for b in range(83):
            cc=cycles([(a*x+b)%83 for x in range(83)])
            top=next(c for c in cc if 0 in c)
            parts=(len(top),)+tuple(sorted((len(c) for c in cc if c is not top),reverse=True))
            reachability=len(cc)-1
            short_returns=sum(g<=len(top) for g in gaps)
            lower=reachability+short_returns
            if lower>40:reason='return_gaps_plus_every_residual_cycle_must_be_selected'
            elif parts==(1,82):reason='exact_82_cycle_support_bound';lower=45
            elif parts==(1,41,41):reason='exact_two_41_cycle_support_bound';lower=41
            else:raise AssertionError((a,b,parts,lower))
            key=str(parts)
            if key not in groups:groups[key]={'cycle_partition':parts,'configurations':0,'minimum_alphabet':lower,'reason':reason}
            groups[key]['configurations']+=1
    out={'model':__doc__,'all_6806_affine_shuffles_excluded_at_alphabet_40':True,
         'arbitrary_common_initial_deck':True,'plaintext_isomorph_assumptions_used':False,
         'cycle_types':list(groups.values()),'configurations':sum(g['configurations'] for g in groups.values())}
    assert out['configurations']==6806
    (ROOT/'affine_family_certificate.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    for g in groups.values():print(g)

if __name__=='__main__':main()
