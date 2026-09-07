from pathlib import Path
import json,itertools
ROOT=Path(__file__).resolve().parent
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());a,b=[m[:50] for m in raw[:2]]
possible=[]
for first,second in itertools.combinations(range(1,50),2):
    cuts=[0,first,second,50];okay=True
    for lo,hi in zip(cuts,cuts[1:]):
        pairs=list(zip(a[lo:hi],b[lo:hi]));f=dict(pairs)
        if any(f[x]!=y for x,y in pairs) or len(set(f.values()))!=len(f):okay=False;break
        if hi<50 and f.get(a[hi])==b[hi]:okay=False;break
    if okay:possible.append([0,first,second])
source=json.loads((ROOT/'compact_template_witnesses.json').read_text());verified=[]
for r in source['witnesses']:
    assert r['status']=='Engineered counterexample; not a decryption'
    key=r['common_initial_deck'];perms=r['per_letter_permutations'];pts=r['plaintext_tokens'];N=83
    assert sorted(key)==list(range(N)) and all(sorted(p)==list(range(N)) for p in perms)
    assert len({p.index(0) for p in perms})==len(perms) and all(p[0]!=0 for p in perms)
    outputs=[];states=[]
    for pt in pts:
        deck=key.copy();ct=[];trace=[]
        for token in pt:
            p=perms[token];new=[None]*N
            for old,newpos in enumerate(p):new[newpos]=deck[old]
            deck=new;ct.append(deck[0]);trace.append(deck.copy())
        outputs.append(ct);states.append(trace)
    assert outputs==[a,b]
    changed=[i for i,(x,y) in enumerate(zip(*pts)) if x!=y];assert changed==r['plaintext_difference_positions'] and len(changed)==3
    assert all(x!=y for x,y in zip(*states))
    verified.append({'difference_positions':changed,'alphabet_size':len(perms),'exact_replay':True})
assert sorted(r['difference_positions'] for r in verified)==possible
assert len(possible)==18 and all(r['alphabet_size']<=23 for r in verified)
out={'all_possible_body_cut_pairs_enumerated':1176,'exact_minimum_change_templates':18,
     'possible_difference_positions_zero_based':possible,'witnesses_independently_verified':verified,
     'maximum_constructed_alphabet':23,'minimum_constructed_alphabet':22,
     'scope':'Exactly three aligned plaintext differences, common initial deck, reversible fixed-per-letter positional permutations, first 50 East1/West1 outputs.',
     'warning':'These synthetic plaintexts are not meaningful language.'}
(ROOT/'checked_compact_templates.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print({k:v for k,v in out.items() if k not in ['possible_difference_positions_zero_based','witnesses_independently_verified']})
