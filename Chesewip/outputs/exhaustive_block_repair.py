"""Exhaustive adjacent-block exchange neighborhood at a fixed key and rotation."""
from pathlib import Path
import itertools,json,time,argparse,math
import numpy as np
from two_swap_prefix_repair import profiles
from rotation_vote_search import direct_errors
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--source',default='two_swap_prefix_repair.json');ap.add_argument('--length',type=int,default=32);ap.add_argument('--rounds',type=int,default=4);ap.add_argument('--output',default='exhaustive_block_prefix32.json');a=ap.parse_args()
source=json.loads((ROOT/a.source).read_text());key=np.array(source['initial_deck']);b=source['rotation'];raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());full=make_plaintexts(raw,assumptions(raw));ct=[m[:a.length] for m in raw];cl=[m[:a.length] for m in full];best=direct_errors(ct,key.tolist(),b,cl)[0];log=[];start=time.time()
for iteration in range(a.rounds):
    winner=None;tested=0;initial=best;moves=itertools.combinations(range(1,84),3)
    while True:
        batch=list(itertools.islice(moves,4096))
        if not batch:break
        keys=np.array([np.concatenate([key[:i],key[j:k],key[i:j],key[k:]]) for i,j,k in batch]);matched,invalid=profiles(ct,keys,cl,b);errors=(~matched).sum(axis=1)+10000*invalid;idx=int(np.argmin(errors));tested+=len(batch)
        if int(errors[idx])<best:best=int(errors[idx]);winner=keys[idx].copy();move=batch[idx]
    assert tested==math.comb(83,3)
    log.append(dict(round=iteration,candidates=tested,initial_errors=initial,best_errors=best));print(log[-1],flush=True)
    if winner is None:break
    key=winner
    if best==0:break
error,pt=direct_errors(ct,key.tolist(),b,cl);assert error==best;assert all(encrypt_physical(p,key,1,b)==c for p,c in zip(pt,ct))
r=dict(status='structural_prefix_fit' if best==0 else 'search_inconclusive',initial_deck=key.tolist(),rotation=b,shared_selection_disagreements=best,plaintext_positions=pt,prefix_length=a.length,rounds=log,seconds=time.time()-start,full_corpus_disagreements=direct_errors(raw,key.tolist(),b,full)[0],scope='Exhaustive adjacent-block exchanges for each listed base key at this rotation. Not an exhaustive key search; no plaintext authentication.')
(ROOT/a.output).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions','rounds']},flush=True)
