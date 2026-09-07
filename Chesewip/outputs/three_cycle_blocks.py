"""Refine circular keys with moves that preserve within-block adjacency."""
from pathlib import Path
import numpy as np
import json,time,argparse
from variable_three_cycle import encrypt,decrypt,batch_hist,signature
from key_swap_attack import objective
ROOT=Path(__file__).resolve().parent

def refine(messages,key,offset,A,steps=150,samples=1600,seed=20260926):
    rng=np.random.default_rng(seed);n=len(key);key=np.array(key);start=time.time();best=None
    for step in range(steps):
        keys=[]
        for k in range(samples):
            a,b,c=sorted(rng.choice(np.arange(1,n+1),3,replace=False).tolist())
            keys.append(np.concatenate([key[:a],key[b:c],key[a:b],key[c:]]))
        for p in range(1,n):
            trial=key.copy();trial[0],trial[p]=trial[p],trial[0];keys.append(trial)
        keys.append(key);keys=np.array(keys)
        hist=batch_hist(messages,keys,offset);scores=objective(hist,A);k=int(np.argmax(scores))
        if best is None or scores[k]>best['score']:
            best={'score':int(scores[k]),'initial_deck':keys[k].tolist(),
                  'outside_alphabet':int(np.partition(hist[k],n-A)[:n-A].sum()),
                  'support':int(np.count_nonzero(hist[k])),'step':step}
        if best['outside_alphabet']==0:break
        if scores[k]>scores[-1]:key=keys[k]
        if step%20==0:print('block step',step,'outside',best['outside_alphabet'],flush=True)
    best.update(plaintext=decrypt(messages,best['initial_deck'],offset),offset=offset,
                alphabet_bound=A,seconds=time.time()-start,steps_requested=steps,samples_per_step=samples)
    assert all(encrypt(p,best['initial_deck'],offset)==c for p,c in zip(best['plaintext'],messages))
    return best

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='three_cycle_control_1_27.json')
    ap.add_argument('--control',action='store_true');ap.add_argument('--steps',type=int,default=150)
    args=ap.parse_args();base=json.loads((ROOT/args.input).read_text());A=base['alphabet_bound'];offset=base['offset']
    if args.control:
        rng=np.random.default_rng(20260925);key=rng.permutation(83);alphabet=rng.choice(np.arange(1,83),A,replace=False)
        pt=[rng.choice(alphabet,120).tolist() for _ in range(9)];messages=[encrypt(p,key,offset) for p in pt]
    else:messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    out=refine(messages,base['initial_deck'],offset,A,args.steps)
    if args.control:out['planted_plaintext_pattern_recovered']=signature(sum(out['plaintext'],[]))==signature(sum(pt,[]))
    name=Path(args.input).stem+'_blocks.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in out.items() if k not in ['plaintext','initial_deck']})
