"""Replay saved component assignments in a physical deck, without SMT."""
from pathlib import Path
import json
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());checked=[]
for limit in [18,20]:
    source=json.loads((ROOT/f'component_returns_{limit}_9_free.json').read_text());assert source['combined_status']=='sat'
    classes=make_plaintexts(raw,source['assumed_equalities']);assignment={}
    for component in source['components']:
        assert component['status']=='sat'
        for label,value in component['selector_assignment']:
            label=tuple(label)
            assert label not in assignment or assignment[label]==value
            assert 0<=value<82;assignment[label]=value
    intervals=0;steps=0
    for mi,ct in enumerate(raw):
        seen={}
        for end,c in enumerate(ct):
            if c in seen and end-seen[c]<=limit:
                start=seen[c];deck=list(range(83));tracked=0
                for t in range(start+1,end+1):
                    p=assignment[classes[mi][t]]+1;neighbor=1+p%82
                    old,chosen,tail=deck[0],deck[p],deck[neighbor]
                    deck[0]=chosen;deck[p]=tail;deck[neighbor]=old
                    assert (deck[0]==tracked)==(t==end)
                    deck=[deck[0]]+deck[-9:]+deck[1:-9];steps+=1
                intervals+=1
            seen[c]=end
    assert intervals==sum(r['return_intervals'] for r in source['components'])
    checked.append({'maximum_return_gap':limit,'return_intervals_verified':intervals,'physical_updates_verified':steps,'assigned_plaintext_classes':len(assignment),'all_shared_class_values_consistent':True})
out={'checked':checked,'warning':'Tracked-card return constraints only; no common initial key or meaningful text verified.'}
(ROOT/'checked_component_assignments.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(out)
