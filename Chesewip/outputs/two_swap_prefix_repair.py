"""Bounded two-swap repair of a nearly fitting common-key prefix candidate."""
from pathlib import Path
import json,time,argparse
import numpy as np
from rotation_vote_search import prepare,direct_errors
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent

def profiles(messages,keys,classes,b):
    labels,G,C,_=prepare(classes,82);B,n=keys.shape;ids=np.arange(B);matches=np.zeros((B,C),dtype=bool);seen={};times={};index=0;invalid=np.zeros(B,dtype=np.int16)
    for mi,ct in enumerate(messages):
        deck=keys.copy();pos=np.argsort(keys,axis=1)
        for t,c in enumerate(ct):
            p=pos[:,c].copy();invalid+=p==0;g=labels[mi][t]
            if g>=0:
                if g not in seen:seen[g]=p.copy();times[g]=t
                else:matches[:,index]=(p-seen[g]+(t-times[g])*b)%82==0;index+=1
            neighbor=np.where(p==0,0,1+p%82);old=deck[:,0].copy();tail=deck[ids,neighbor].copy()
            deck[:,0]=c;deck[ids,p]=tail;deck[ids,neighbor]=old;pos[:,c]=0;pos[ids,tail]=p;pos[ids,old]=neighbor
    return matches,invalid

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='common_key_prefix_32_refined.json');ap.add_argument('--output',default='two_swap_prefix_repair.json');args=ap.parse_args()
    source=json.loads((ROOT/args.source).read_text());key=np.array(source['initial_deck']);b=source['rotation'];raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(raw);full=make_plaintexts(raw,eq);ct=[m[:32] for m in raw];cl=[m[:32] for m in full];aa,bb=np.triu_indices(83,1);I=np.arange(len(aa));start=time.time()
    baseline,_=profiles(ct,np.array([key]),cl,b);bad=~baseline[0];keys=np.tile(key,(len(aa),1));keys[I,aa]=key[bb];keys[I,bb]=key[aa]
    matched,invalid=profiles(ct,keys,cl,b);errors=np.count_nonzero(~matched,axis=1);fixed=np.count_nonzero(matched[:,bad],axis=1)
    candidates=np.flatnonzero((fixed>0)&(invalid==0)&(errors<=int(bad.sum())+4));candidates=sorted(candidates,key=lambda i:(errors[i],-fixed[i]))[:100]
    print('baseline errors',int(bad.sum()),'first moves selected',len(candidates),flush=True);best=int(bad.sum());winner=None;tested=0
    for offset in range(0,len(candidates),5):
        selected=candidates[offset:offset+5];trials=[]
        for i in selected:
            base=keys[i];neighbors=np.tile(base,(len(aa),1));neighbors[I,aa]=base[bb];neighbors[I,bb]=base[aa];trials.append(neighbors)
        trials=np.concatenate(trials);m,bad_top=profiles(ct,trials,cl,b);scores=np.count_nonzero(~m,axis=1)+1000*bad_top;k=int(np.argmin(scores));tested+=len(trials)
        if int(scores[k])<best:best=int(scores[k]);winner=trials[k].copy()
        print('tested',tested,'best errors',best,flush=True)
        if best==0:break
    out={'status':'structural_prefix_fit' if best==0 else 'bounded_search_inconclusive','prefix_length':32,'rotation':b,'first_moves_selected':len(candidates),'second_move_candidates_tested':tested,'best_disagreements':best,'seconds':time.time()-start,
         'maximum_first_move_disagreements':int(bad.sum())+4,'source':args.source,'scope':'Two swaps; first move must repair at least one originally failed comparison, obey the recorded error threshold, and rank among at most 100 retained moves. Not an exhaustive two-swap search.'}
    if winner is not None:
        error,pt=direct_errors(ct,winner.tolist(),b,cl);assert error==best
        assert all(encrypt_physical(p,winner,1,b)==c for p,c in zip(pt,ct))
        out.update(initial_deck=winner.tolist(),plaintext_positions=pt,full_corpus_disagreements=direct_errors(raw,winner.tolist(),b,full)[0])
    (ROOT/args.output).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in out.items() if k not in ['initial_deck','plaintext_positions']},flush=True)
