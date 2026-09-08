"""Global language symmetry of a generated period-2 function-codebook cipher.

States are coordinate triples. Equal incoming/outgoing neighborhoods and equal
singleton membership make a state transposition preserve every valid message.
This is a generated-model identifiability result, not an Eye solution.
"""
from pathlib import Path
from collections import defaultdict
import itertools,json,hashlib,math
ROOT=Path(__file__).resolve().parent
POINTS=list(itertools.product(range(5),repeat=3))

def main():
    source_bytes=(ROOT/'one_coordinate_function_screen.json').read_bytes();source=json.loads(source_bytes)
    c=next(c for c in source['controls'] if c['seed']==908210);table=c['table']
    assert c['axis']==0 and c['period']==2
    allowed={25*x+5*y+z for x,y,z in POINTS if x==table[y][z]}
    out_neighbors=[0]*125;in_neighbors=[0]*125
    for a,b in itertools.product(range(125),repeat=2):
        u,v=POINTS[a],POINTS[b]
        if u[0]==table[u[2]][v[1]] and u[1]==table[v[0]][v[2]]:
            out_neighbors[a]|=1<<b;in_neighbors[b]|=1<<a
    groups=defaultdict(list)
    for state in range(125):groups[(out_neighbors[state],in_neighbors[state],state in allowed)].append(state)
    twins=[g for g in groups.values() if len(g)>1]
    prior=json.loads((ROOT/'function_key_ambiguity.json').read_text(encoding='utf-8'))
    a,b=[c['true_label_to_code'][label] for label in prior['selected_labels']]
    assert any(a in g and b in g for g in twins)
    tau=list(range(125));tau[a],tau[b]=tau[b],tau[a]
    assert all((state in allowed)==(tau[state] in allowed) for state in range(125))
    assert all(bool(out_neighbors[x]&(1<<y))==bool(out_neighbors[tau[x]]&(1<<tau[y])) for x,y in itertools.product(range(125),repeat=2))
    changes=[];images=[defaultdict(list),defaultdict(list)]
    for p,q in itertools.product(sorted(allowed),repeat=2):
        x,y=POINTS[p],POINTS[q]
        enc=[25*x[0]+5*y[0]+x[1],25*y[1]+5*x[2]+y[2]]
        u,v=[POINTS[tau[s]] for s in enc]
        decoded=[25*u[0]+5*u[2]+v[1],25*u[1]+5*v[0]+v[2]]
        assert all(s in allowed for s in decoded)
        if decoded!=[p,q]:changes.append([[p,q],decoded])
        for pos,old in enumerate([p,q]):images[pos][old].append([[p,q],decoded])
    witnesses=[]
    for pos in range(2):
        for old,examples in images[pos].items():
            values={example[1][pos] for example in examples}
            if len(values)>1:
                first=examples[0];second=next(e for e in examples if e[1][pos]!=first[1][pos])
                witnesses.append(dict(position=pos,input_symbol=old,blocks=[first,second]));break
    assert len(witnesses)==2
    live_twins=[g for g in twins if out_neighbors[g[0]] or in_neighbors[g[0]] or g[0] in allowed]
    out=dict(status='Global symmetry of a generated cipher model; not a fit to the Eye ciphertext.',
        control_source_sha256=hashlib.sha256(source_bytes).hexdigest(),control_seed=908210,
        table=table,allowed_input_codes=sorted(allowed),valid_two_symbol_blocks=sum(mask.bit_count() for mask in out_neighbors),
        selected_coordinate_codes=[a,b],all_twin_classes=twins,live_twin_classes=live_twins,
        twin_permutation_lower_bound=str(math.prod(math.factorial(len(g)) for g in twins)),
        live_twin_permutation_lower_bound=str(math.prod(math.factorial(len(g)) for g in live_twins)),
        singleton_membership_checks=125,ordered_pair_membership_checks=15625,
        changed_plaintext_blocks=len(changes),changed_block_examples=changes,
        contextual_nonrenaming_witnesses=witnesses,
        conclusion='Swapping the selected two output-map entries preserves the complete valid ciphertext language for period 2, including singleton boundary blocks, but changes plaintext in a context-dependent way.')
    (ROOT/'function_graph_automorphisms.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Live twin classes',live_twins,'live key permutations',out['live_twin_permutation_lower_bound'],'changed input blocks',len(changes),flush=True)

if __name__=='__main__':main()
