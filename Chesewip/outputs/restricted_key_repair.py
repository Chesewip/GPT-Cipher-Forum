"""Exact restricted-neighborhood repair using lazy shared-key propagation.
Each call searches permutations of selected initial slots, fixing all others.
Exclusions apply only to the explicitly fixed neighborhood, not the family.
"""
from pathlib import Path
import json,time,argparse
import numpy as np
from shared_plaintext_search import solve
from adaptive_equality_search import fixture
from rotation_vote_search import direct_errors
from two_swap_prefix_repair import profiles
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent

def eq_from_classes(cl):
    first={};eq=[]
    for i,row in enumerate(cl):
        for t,x in enumerate(row):
            if x in first:j,s=first[x];eq.append((j,s,i,t,1))
            else:first[x]=(i,t)
    return eq

def repair(ct,cl,key,b,attempts=80,free_count=12,seconds=1,seed=20261111):
    rng=np.random.default_rng(seed);key=np.array(key);eq=eq_from_classes(cl);start=time.time();initial=direct_errors(ct,key.tolist(),b,cl)[0];best=initial;log=[];aa,bb=np.triu_indices(83,1);ids=np.arange(len(aa));last_best=-1
    for attempt in range(attempts):
        if best==0:break
        if best!=last_best:
            baseline,_=profiles(ct,np.array([key]),cl,b);bad=~baseline[0];keys=np.tile(key,(len(aa),1));keys[ids,aa]=key[bb];keys[ids,bb]=key[aa]
            matched,invalid=profiles(ct,keys,cl,b);errors=(~matched).sum(axis=1)+10000*invalid;fixes=matched[:,bad].sum(axis=1)
            selected=np.flatnonzero(fixes>0);selected=sorted(selected,key=lambda i:(errors[i],-fixes[i]));last_best=best
        if selected:
            head=selected[:min(len(selected),max(8,attempt//4))];chosen=rng.choice(head,min(len(head),max(1,free_count//4)),replace=False)
            slots=set(int(p) for idx in chosen for p in (aa[idx],bb[idx]))
        else:slots=set()
        if len(slots)<free_count:slots.update(int(x) for x in rng.choice([x for x in range(83) if x not in slots],free_count-len(slots),replace=False))
        if len(slots)>free_count:slots=set(rng.choice(sorted(slots),free_count,replace=False).tolist())
        fixed={int(c):i for i,c in enumerate(key) if i not in slots}
        r=solve(ct,83,list(range(1,83)),b,False,200000,seconds,fixed,eq)
        log.append(dict(attempt=attempt,free_slots=sorted(slots),status=r['status'],nodes=r['nodes'],seconds=r['seconds'],furthest_outputs=r['furthest_outputs_reached']))
        if r['status']=='model_fit':key=np.array(r['initial_deck']);best=direct_errors(ct,key.tolist(),b,cl)[0];assert best==0
        if attempt%10==0 or best==0:print('attempt',attempt,'status',r['status'],'nodes',r['nodes'],'errors',best,flush=True)
    return dict(status='structural_model_fit' if best==0 else 'restricted_search_inconclusive',initial_deck=key.tolist(),rotation=b,initial_disagreements=initial,shared_selection_disagreements=best,comparisons=len(eq),plaintext_positions=direct_errors(ct,key.tolist(),b,cl)[1],attempts=log,seconds=time.time()-start,seed=seed,free_count=free_count,scope='Only permutations of recorded free initial slots; all other key entries fixed. Each exhausted neighborhood may be excluded, but the family is not excluded.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');ap.add_argument('--source',required=True);ap.add_argument('--length',type=int);ap.add_argument('--attempts',type=int,default=80);ap.add_argument('--free',type=int,default=12);ap.add_argument('--seconds',type=float,default=1);ap.add_argument('--output',required=True);a=ap.parse_args()
    if a.control:ct,cl,truekey,truept=fixture()
    else:ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cl=make_plaintexts(ct,assumptions(ct))
    if a.length:ct=[m[:a.length] for m in ct];cl=[m[:a.length] for m in cl]
    source=json.loads((ROOT/a.source).read_text());r=repair(ct,cl,source['initial_deck'],source['rotation'],a.attempts,a.free,a.seconds);r.update(source=a.source,prefix_length=a.length,control=a.control)
    if a.control:r['exact_planted_plaintext_recovered']=r['plaintext_positions']==[m[:a.length] if a.length else m for m in truept]
    (ROOT/a.output).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions','attempts']},flush=True)
