"""Exact restricted improvements, accepting fewer equality errors, not full fits."""
from pathlib import Path
import json,argparse,time
import numpy as np
from inverse_position_solver import solve
from adaptive_equality_search import fixture
from rotation_vote_search import direct_errors
from two_swap_prefix_repair import profiles
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output',required=True);ap.add_argument('--control',action='store_true');ap.add_argument('--length',type=int);ap.add_argument('--attempts',type=int,default=6);ap.add_argument('--free',type=int,default=10);ap.add_argument('--timeout',type=int,default=5000);a=ap.parse_args()
if a.control:ct,cl,truekey,truept=fixture()
else:ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cl=make_plaintexts(ct,assumptions(ct))
if a.length:ct=[m[:a.length] for m in ct];cl=[m[:a.length] for m in cl]
source=json.loads((ROOT/a.source).read_text());key=source['initial_deck'];b=source['rotation'];best=direct_errors(ct,key,b,cl)[0];rng=np.random.default_rng(20261113);log=[];start=time.time()
for attempt in range(a.attempts):
    if best==0:break
    aa,bb=np.triu_indices(83,1);ids=np.arange(len(aa));keys=np.tile(key,(len(aa),1));keys[ids,aa]=np.array(key)[bb];keys[ids,bb]=np.array(key)[aa]
    baseline,_=profiles(ct,np.array([key]),cl,b);matched,invalid=profiles(ct,keys,cl,b);errors=(~matched).sum(axis=1)+invalid*10000;fixes=matched[:,~baseline[0]].sum(axis=1)
    candidates=sorted(np.flatnonzero(fixes>0),key=lambda i:errors[i]);head=candidates[:40];slots=set()
    if head:
        for i in rng.choice(head,min(len(head),a.free//3),replace=False):slots.update([int(aa[i]),int(bb[i])])
    slots.update(rng.choice([p for p in range(83) if p not in slots],a.free-len(slots),replace=False).tolist())
    fixed={c:p for p,c in enumerate(key) if p not in slots}
    r=solve(ct,cl,b,timeout=a.timeout,fixed=fixed,preferred=key,max_errors=best-1);r['free_slots']=sorted(slots);log.append(r)
    if r['status']=='sat':key=r['initial_deck'];best=r['shared_selection_disagreements']
    print('attempt',attempt,r['status'],'best errors',best,'seconds',round(r['seconds'],2),flush=True)
out=dict(status='structural_model_fit' if best==0 else 'search_inconclusive',initial_deck=key,rotation=b,shared_selection_disagreements=best,plaintext_positions=direct_errors(ct,key,b,cl)[1],source=a.source,prefix_length=a.length,control=a.control,attempts=log,seconds=time.time()-start,scope='Restricted SMT neighborhoods with a decreasing error bound. SAT with nonzero disagreements is only a heuristic candidate.')
if a.control:out['exact_planted_plaintext_recovered']=out['plaintext_positions']==[m[:a.length] if a.length else m for m in truept]
(ROOT/a.output).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
