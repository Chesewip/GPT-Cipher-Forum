"""Held-out English control for unknown-key clocked three-cycle search.

English is a hypothesis, not established Noita plaintext. Train4-grams on
Pride and Prejudice; test on disjoint Sherlock Holmes passages. An exact
control match is required to claim recovery. Attractive fragments alone
are not evidence. Cipher parameters are unit neighbor and fixed rotation.
"""
from pathlib import Path
import json,re,hashlib,time,argparse
import numpy as np
from clocked_three_cycle_scan import encrypt_physical
from clocked_key_attack import decode
ROOT=Path(__file__).resolve().parent;WORK=ROOT.parent/'work'

def clean(path):
    raw=path.read_text(encoding='utf-8-sig')
    start=re.search(r'\*\*\* START OF .*?\*\*\*',raw)
    end=re.search(r'\*\*\* END OF .*?\*\*\*',raw)
    raw=raw[start.end() if start else 0:end.start() if end else len(raw)]
    return re.sub(r'[^a-z]+',' ',raw.lower()).strip()

def encode(text):return [1 if c==' ' else ord(c)-95 for c in text]
def readable(seq):return ''.join(' ' if p==1 else chr(p+95) if 2<=p<=27 else '?' for p in seq)

def model():
    chars=np.array(encode(clean(WORK/'pg1342.txt')),dtype=np.int32)
    ids=((chars[:-3]*28+chars[1:-2])*28+chars[2:-1])*28+chars[3:]
    counts=np.bincount(ids,minlength=28**4)
    table=np.log((counts+0.01)/(len(ids)+0.01*28**4))
    return table

def language_scores(messages,keys,b,table):
    B,n=keys.shape;ids=np.arange(B);scores=np.zeros(B);bad=np.zeros(B,dtype=np.int32)
    for m in messages:
        deck=keys.copy();pos=np.argsort(keys,axis=1);rolling=np.zeros(B,dtype=np.int32)
        for t,c in enumerate(m):
            p=pos[:,c].copy();r=np.where(p==0,0,1+p%(n-1))
            physical=np.where(p==0,0,1+(p-1+t*b)%(n-1))
            token=np.where((physical>=1)&(physical<=27),physical,0)
            bad+=token==0;rolling=(rolling%(28**3))*28+token
            if t>=3:scores+=table[rolling]
            old=deck[:,0].copy();tail=deck[ids,r].copy()
            deck[:,0]=c;deck[ids,p]=tail;deck[ids,r]=old
            pos[:,c]=0;pos[ids,tail]=p;pos[ids,old]=r
    return scores-2*bad,bad

def attack(messages,b,table,steps=100,restarts=2,start_key=None,staged=True,fixed=None):
    rng=np.random.default_rng(20261010);n=83;aa,bb=np.triu_indices(n,1)
    fixed={} if fixed is None else fixed
    free=np.array([k not in fixed for k in range(n)])
    keep=free[aa]&free[bb];aa=aa[keep];bb=bb[keep];B=len(aa);start=time.time();global_best=None
    stages=[24,48,max(map(len,messages))] if staged else [max(map(len,messages))]
    for restart in range(restarts):
        key=np.array(start_key) if start_key is not None and restart==0 else rng.permutation(n)
        if fixed:
            for position,label in fixed.items():key[position]=label
            key[free]=rng.permutation([x for x in range(n) if x not in fixed.values()])
        for limit in stages:
            active=[m[:limit] for m in messages];stage_best=None
            for step in range(steps):
                keys=np.tile(key,(B+1,1));ids=np.arange(B)
                keys[ids,aa]=key[bb];keys[ids,bb]=key[aa]
                scores,bad=language_scores(active,keys,b,table);k=int(np.argmax(scores))
                if stage_best is None or scores[k]>stage_best['score']:
                    stage_best={'score':float(scores[k]),'key':keys[k].copy(),'outside':int(bad[k]),'step':step}
                temperature=7*(1-step/steps)**2
                move=int(np.argmax(scores+temperature*rng.gumbel(size=len(scores))))
                key=keys[move]
                if step%25==0:print('restart',restart,'prefix',limit,'step',step,'best score',round(stage_best['score'],1),'outside',stage_best['outside'],flush=True)
            key=stage_best['key']
            if limit==stages[-1] and (global_best is None or stage_best['score']>global_best['score']):global_best=stage_best
    pt=decode(messages,global_best['key'],b)
    assert all(encrypt_physical(p,global_best['key'],1,b)==c for p,c in zip(pt,messages))
    return {'score':global_best['score'],'outside_english_alphabet':global_best['outside'],
            'initial_deck':global_best['key'].tolist(),'plaintext_positions':pt,'candidate_text':[readable(p) for p in pt],
            'shuffle_offset':b,'neighbor_offset':1,'prefix_stages':stages,'steps_per_stage':steps,
            'restarts':restarts,'seconds':time.time()-start,'exact_replay':True,
            'warning':'Unverified candidate text is a search artifact, not a decryption.'}

def make_control(b,near=False):
    text=clean(WORK/'pg1661.txt');rng=np.random.default_rng(20261011);key=rng.permutation(83)
    pt=[encode(text[10000+5000*i:10120+5000*i]) for i in range(9)]
    ct=[encrypt_physical(p,key,1,b) for p in pt];damaged=key.copy()
    for _ in range(5):
        a,c=rng.choice(83,2,replace=False);damaged[a],damaged[c]=damaged[c],damaged[a]
    return ct,pt,key,damaged if near else None

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');ap.add_argument('--near',action='store_true')
    ap.add_argument('--shuffle',type=int,default=9);ap.add_argument('--steps',type=int,default=70)
    ap.add_argument('--restarts',type=int,default=2);ap.add_argument('--no-stages',action='store_true');args=ap.parse_args()
    table=model()
    if args.control:messages,pt,key,initial=make_control(args.shuffle,args.near)
    else:messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());initial=None
    out=attack(messages,args.shuffle,table,args.steps,args.restarts,initial,not args.no_stages)
    if args.control:
        out['planted_exact_plaintext_recovered']=out['plaintext_positions']==pt
        out['matching_plaintext_positions']=sum(a==b for x,y in zip(pt,out['plaintext_positions']) for a,b in zip(x,y))
        out['control_positions']=sum(map(len,pt));out['started_five_key_swaps_from_truth']=args.near
        true_score,_=language_scores(messages,np.array([key]),args.shuffle,table);out['true_key_score']=float(true_score[0])
    out['training_source']='https://www.gutenberg.org/ebooks/1342';out['control_source']='https://www.gutenberg.org/ebooks/1661'
    out['source_hashes']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [WORK/'pg1342.txt',WORK/'pg1661.txt']}
    name='english_clocked_'+('control' if args.control else 'eyes')+'_'+str(args.shuffle)+('_near' if args.near else '')+'.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in out.items() if k not in ['initial_deck','plaintext_positions','candidate_text','source_hashes']})
