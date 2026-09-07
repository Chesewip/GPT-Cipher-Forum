"""Broader exact key neighborhoods, scoring every rotation in one replay."""
from pathlib import Path
import itertools,json,time,argparse,math
import numpy as np
from rotation_vote_search import scores,prepare,direct_errors
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--source',default='two_swap_prefix_repair.json');ap.add_argument('--length',type=int,default=32);ap.add_argument('--mode',choices=['three_cycle','disjoint_blocks'],default='three_cycle');ap.add_argument('--output',required=True);a=ap.parse_args()
source=json.loads((ROOT/a.source).read_text());key=np.array(source['initial_deck']);raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());full=make_plaintexts(raw,assumptions(raw));ct=[m[:a.length] for m in raw];cl=[m[:a.length] for m in full];prepared=prepare(cl,82);v,C,invalid=scores(ct,np.array([key]),prepared);best=int(C-v.max());b=int(v.argmax());winner=key.copy();tested=0;start=time.time();history=[]
def candidates():
    if a.mode=='three_cycle':
        for i,j,k in itertools.combinations(range(83),3):
            for direction in [1,-1]:
                trial=key.copy();trial[[i,j,k]]=key[np.roll([i,j,k],direction)];yield trial
    else:
        for i,j,k,l in itertools.combinations(range(1,84),4):
            yield np.concatenate([key[:i],key[k:l],key[j:k],key[i:j],key[l:]])
gen=candidates()
while True:
    batch=list(itertools.islice(gen,4096))
    if not batch:break
    keys=np.array(batch);votes,C,invalid=scores(ct,keys,prepared);index=np.unravel_index(np.argmax(votes),votes.shape);error=C-int(votes[index]);tested+=len(keys)
    if error<best:
        best=error;winner=keys[index[0]].copy();b=int(index[1]);history.append([tested,best,b]);print('tested',tested,'best',best,'rotation',b,flush=True)
    if tested%131072==0:print('tested',tested,'best',best,flush=True)
    if best==0:break
expected=2*math.comb(83,3) if a.mode=='three_cycle' else math.comb(83,4)
error,pt=direct_errors(ct,winner.tolist(),b,cl);assert error==best;assert all(encrypt_physical(p,winner,1,b)==c for p,c in zip(pt,ct))
r=dict(status='structural_prefix_fit' if best==0 else 'search_inconclusive',initial_deck=winner.tolist(),rotation=b,shared_selection_disagreements=best,comparisons=C,plaintext_positions=pt,prefix_length=a.length,source=a.source,mode=a.mode,key_candidates_tested=tested,complete_neighborhood=tested==expected,possible_key_candidates=expected,rotations_per_candidate=82,seconds=time.time()-start,history=history,full_corpus_disagreements=direct_errors(raw,winner.tolist(),b,full)[0],scope='Only the recorded key neighborhood. Zero prefix errors is not a full-corpus fit or meaningful plaintext.')
(ROOT/a.output).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions','history']},flush=True)
