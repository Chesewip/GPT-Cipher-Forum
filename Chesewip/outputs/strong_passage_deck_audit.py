"""Audit stronger published passage equalities separately from the older set."""
from pathlib import Path
import json,time,collections
from shared_update_support import assumptions,scan
from permutation_action_fold import make_plaintexts,solve as fold
from return_displacement import graph,solve
ROOT=Path(__file__).resolve().parent
raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
strong=[(1,34,1,64,18),(1,34,2,39,18),(1,34,2,74,18),(0,40,0,68,9),(6,68,7,71,30),(6,68,8,69,30)]
results=[]
for variant in ['strong_only','older_plus_strong']:
 eq=[(i,s+3,j,t+3,n-3) for i,s,j,t,n in strong]
 if variant=='older_plus_strong':eq=assumptions(raw,3)+eq
 cl=make_plaintexts(raw,eq);start=time.time();f=fold(cl,raw);bounds=scan(raw,cl);edges=graph(raw,cl);returns=[]
 print(variant,'classes',len({x for row in cl for x in row}),'fold',f['status'],'support bound',max(r.get('ratio',999) for r in bounds),flush=True)
 for b in range(82):
  r=solve(edges,82,b,1000);returns.append(r)
  if b%20==0 or r['status']!='sat':print(variant,'b',b,r['status'],flush=True)
 results.append(dict(variant=variant,trim=3,assumed_equalities=eq,plaintext_classes=len({x for row in cl for x in row}),fold=f,support_bounds=bounds,return_displacement=returns,seconds=time.time()-start))
(ROOT/'strong_passage_deck_audit.json').write_text(json.dumps(dict(strong_ciphertext_alignments=strong,results=results,scope='Explicitly separated conditional equality sets. Passing these necessary tests is not a complete key or a plaintext.'),indent=2)+'\n',encoding='utf-8',newline='\r\n')
