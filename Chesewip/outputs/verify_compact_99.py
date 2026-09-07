from pathlib import Path
import json,itertools
ROOT=Path(__file__).resolve().parent
r=json.loads((ROOT/'compact_99_witness.json').read_text())
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
key=r['common_initial_deck'];perms=r['per_letter_permutations'];pts=r['plaintext_tokens'];N=83
assert sorted(key)==list(range(N)) and all(sorted(p)==list(range(N)) for p in perms)
assert len({p.index(0) for p in perms})==len(perms) and all(p[0]!=0 for p in perms)
outputs=[];states=[]
for pt in pts:
    deck=key.copy();ct=[];trace=[]
    for token in pt:
        new=[None]*N
        for old,newpos in enumerate(perms[token]):new[newpos]=deck[old]
        deck=new;ct.append(deck[0]);trace.append(deck.copy())
    outputs.append(ct);states.append(trace)
assert outputs==[raw[0],raw[1][:99]]
changed=[i for i,(x,y) in enumerate(zip(*pts)) if x!=y]
assert changed==[0,25,33,50,59,68,73,78,89]==r['plaintext_difference_positions']
support=[sum(x!=y for x,y in zip(sa,sb)) for sa,sb in zip(*states)]
assert support==r['relative_state_support_by_position'] and min(support)>0
run=max(len(list(g)) for pt in pts for _,g in itertools.groupby(pt))
assert run==r['actual_maximum_token_run_length']
out={'exact_replay':True,'positions_per_message':99,'alphabet_size':len(perms),'plaintext_difference_count':len(changed),'difference_positions_zero_based':changed,'actual_maximum_identical_token_run':run,'distinct_states_at_every_position':True,'minimum_state_support':min(support),'status':'Engineered counterexample, not a decryption. East1 complete; West1 first 99 of 103 symbols.'}
(ROOT/'checked_compact_99.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(out)
