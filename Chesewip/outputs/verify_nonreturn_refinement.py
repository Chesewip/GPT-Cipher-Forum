"""Check terminal non-return constraints against direct physical updates."""
from pathlib import Path
import json,random
from refine_return_paths import Engine
ROOT=Path(__file__).resolve().parent
rng=random.Random(20261110);counts={'sat':0,'unsat':0}
for n in [7,19,83]:
    b=3%(n-1)
    for trial in range(20):
        length=rng.randrange(2,7);pt=[1]+[rng.randrange(1,n) for _ in range(length)]
        deck=list(range(n));observed=[]
        for p in pt[1:]:
            neighbor=1+p%(n-1);old,chosen,tail=deck[0],deck[p],deck[neighbor]
            deck[0]=chosen;deck[p]=tail;deck[neighbor]=old;observed.append(deck[0])
            if b:deck=[deck[0]]+deck[-b:]+deck[1:-b]
        for equal in [False,True]:
            ct=[0]+[1]*(length-1)+[0 if equal else 1];cl=[[(0,t) for t in range(length+1)]]
            engine=Engine([ct],cl,set(cl[0][1:]),b,n,3000,pinned=[pt]);engine.add(0,0,length,equal);r,_=engine.check()
            expected=all(x!=0 for x in observed[:-1]) and ((observed[-1]==0)==equal)
            assert r['status']==('sat' if expected else 'unsat'),(n,pt,observed,equal,r);counts[r['status']]+=1
# Independent physical replay of the two repaired runs.
r=json.loads((ROOT/'refined_returns_20_8.json').read_text());assert r['status']=='local_model_fit'
from permutation_action_fold import make_plaintexts
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());classes=make_plaintexts(raw,r['assumed_equalities']);assignment={tuple(x):v+1 for x,v in r['selector_assignment']};outputs=0
for run in r['local_keys']:
    mi,start,end=run['message'],run['start'],run['end'];deck=run['deck_at_run_start'];assert sorted(deck)==list(range(83))
    if start>0:assert deck[0]==raw[mi][start-1]
    for t in range(start,end):
        p=assignment[classes[mi][t]];q=1+p%82;a,c,e=deck[0],deck[p],deck[q];deck[0]=c;deck[p]=e;deck[q]=a
        assert deck[0]==raw[mi][t];deck=[deck[0]]+deck[-9:]+deck[1:-9];outputs+=1
out={'pinned_terminal_checks':sum(counts.values()),'outcomes':counts,'repaired_local_runs':len(r['local_keys']),'real_outputs_independently_replayed':outputs,'scope':'Separate starting decks for the local runs; no common reset key.'}
(ROOT/'checked_nonreturn_refinement.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(out)
