"""Adaptive weighted equality search; fixed rotation is an explicit assumption."""
from pathlib import Path
import json,time,argparse
import numpy as np
from rotation_vote_search import direct_errors
from two_swap_prefix_repair import profiles
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent

def fixture(seed=20261106):
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cl=make_plaintexts(raw,assumptions(raw))
    rng=np.random.default_rng(seed);key=rng.permutation(83);values={x:int(rng.integers(1,83)) for row in cl for x in row};pt=[[values[x] for x in row] for row in cl]
    for i,row in enumerate(pt):row[0]=i+1
    return [encrypt_physical(row,key,1,9) for row in pt],cl,key,pt

def search(ct,cl,b,steps=250,seed=20261110,start_key=None,blocks=320):
    rng=np.random.default_rng(seed);key=rng.permutation(83) if start_key is None else np.array(start_key);aa,bb=np.triu_indices(83,1);ids=np.arange(len(aa));start=time.time();weights=None;best=100000;winner=None;history=[];stagnation=0
    for step in range(steps):
        keys=np.tile(key,(len(aa)+1,1));keys[ids,aa]=key[bb];keys[ids,bb]=key[aa];extra=[]
        for _ in range(blocks):
            a,c,e=sorted(rng.choice(np.arange(1,84),3,replace=False).tolist());extra.append(np.concatenate([key[:a],key[c:e],key[a:c],key[e:]]))
        keys=np.concatenate([keys,np.array(extra)]) if extra else keys
        match,invalid=profiles(ct,keys,cl,b);bad=(~match).astype(np.int16);errors=bad.sum(axis=1)+10000*invalid
        if weights is None:weights=np.ones(bad.shape[1])
        k=int(np.argmin(errors));improved=int(errors[k])<best
        if improved:best=int(errors[k]);winner=keys[k].copy();stagnation=0;history.append([step,best])
        else:stagnation+=1
        if best==0:break
        cost=bad@weights+100000*invalid;current=len(aa);lowest=float(cost.min());candidates=np.flatnonzero(cost<=lowest+1e-8)
        pick=int(rng.choice(candidates));key=keys[pick].copy()
        if lowest>=float(cost[current])-1e-8:
            weights+=bad[pick];weights=1+(weights-1)*0.995
        if stagnation and stagnation%35==0:
            # Bounded escape preserving most of the current candidate.
            ps=rng.choice(np.arange(1,83),5,replace=False);key[ps]=key[np.roll(ps,1)]
        if step%20==0:print('step',step,'best errors',best,'current',int(errors[pick]),'max weight',round(float(weights.max()),2),flush=True)
    err,pt=direct_errors(ct,winner.tolist(),b,cl);assert err==best
    assert all(encrypt_physical(p,winner,1,b)==c for p,c in zip(pt,ct))
    return dict(status='structural_model_fit' if best==0 else 'search_inconclusive',initial_deck=winner.tolist(),rotation=b,shared_selection_disagreements=best,comparisons=bad.shape[1],plaintext_positions=pt,seconds=time.time()-start,steps_requested=steps,seed=seed,blocks_per_step=blocks,history=history,exact_ciphertext_replay=True,warning='Fixed rotation. Exact replay alone does not authenticate plaintext. Heuristic failure does not exclude a model.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');ap.add_argument('--steps',type=int,default=250);ap.add_argument('--source');ap.add_argument('--length',type=int);ap.add_argument('--rotation',type=int,default=9);ap.add_argument('--seed',type=int,default=20261110);ap.add_argument('--output',required=True);a=ap.parse_args()
    if a.control:ct,cl,truekey,truept=fixture()
    else:ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());cl=make_plaintexts(ct,assumptions(ct))
    if a.length:ct=[m[:a.length] for m in ct];cl=[m[:a.length] for m in cl]
    key=json.loads((ROOT/a.source).read_text())['initial_deck'] if a.source else None
    r=search(ct,cl,a.rotation,a.steps,a.seed,key);r.update(source=a.source,prefix_length=a.length,control=a.control)
    if a.control:r['exact_planted_plaintext_recovered']=r['plaintext_positions']==[m[:a.length] if a.length else m for m in truept]
    (ROOT/a.output).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions','history']},flush=True)
