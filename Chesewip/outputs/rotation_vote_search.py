"""Direct full-key search, scoring all rotations from one rotating-frame replay.

Repeated plaintext selections satisfy (p_v-p_u)+(t_v-t_u)*b = 0 mod 82.
Each comparison therefore votes for a small set of possible rotations.
No plaintext language or alphabet-size objective is used.
"""
from pathlib import Path
import json,time,argparse,math,collections
import numpy as np
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from clocked_key_attack import decode
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent

def prepare(classes,M):
    counter=collections.Counter(x for cl in classes for x in cl);shared={x:i for i,x in enumerate(x for x,c in counter.items() if c>1)}
    labels=[[shared.get(x,-1) for x in cl] for cl in classes];first={};relations=[]
    for mi,cl in enumerate(labels):
        for t,g in enumerate(cl):
            if g<0:continue
            if g in first:relations.append((g,mi,t,t-first[g][1]))
            else:first[g]=(mi,t)
    lookup={}
    for dt in {r[3] for r in relations}:
        lookup[dt]=[[b for b in range(M) if (dp+dt*b)%M==0] for dp in range(M)]
    return labels,len(shared),len(relations),lookup

def scores(messages,keys,prepared):
    labels,G,C,lookup=prepared;B,n=keys.shape;M=n-1;ids=np.arange(B);votes=np.zeros((B,M),dtype=np.int16);invalid=np.zeros(B,dtype=np.int16)
    first_pos={};first_time={}
    for mi,message in enumerate(messages):
        deck=keys.copy();pos=np.argsort(keys,axis=1)
        for t,c in enumerate(message):
            p=pos[:,c].copy();invalid+=p==0;g=labels[mi][t]
            if g>=0:
                if g not in first_pos:first_pos[g]=p.copy();first_time[g]=t
                else:
                    dt=t-first_time[g];dp=(p-first_pos[g])%M
                    if dt%M==0:votes+=(dp==0)[:,None]
                    else:
                        table=lookup[dt]
                        for delta in np.unique(dp):
                            bs=table[int(delta)]
                            if bs:
                                idx=np.flatnonzero(dp==delta);votes[np.ix_(idx,bs)]+=1
            r=np.where(p==0,0,1+p%M);old=deck[:,0].copy();tail=deck[ids,r].copy()
            deck[:,0]=c;deck[ids,p]=tail;deck[ids,r]=old
            pos[:,c]=0;pos[ids,tail]=p;pos[ids,old]=r
    return votes-(C+1)*invalid[:,None],C,invalid

def direct_errors(messages,key,b,classes):
    pt=decode(messages,key,b);seen={};errors=0
    for cl,m in zip(classes,pt):
        for x,p in zip(cl,m):
            if x in seen:errors+=p!=seen[x]
            else:seen[x]=p
    return errors,pt

def search(messages,classes,steps=60,restarts=1,start_key=None,seed=20261105,temperature=1.4,block_moves=0,temperature_floor=0.1):
    rng=np.random.default_rng(seed);n=83;M=82;prepared=prepare(classes,M);aa,bb=np.triu_indices(n,1);start=time.time();best=None
    for restart in range(restarts):
        key=np.array(start_key,dtype=int) if restart==0 and start_key is not None else rng.permutation(n)
        for step in range(steps):
            keys=np.tile(key,(len(aa)+1,1));idx=np.arange(len(aa));keys[idx,aa]=key[bb];keys[idx,bb]=key[aa]
            if block_moves:
                extra=[]
                for _ in range(block_moves):
                    a,c,e=sorted(rng.choice(np.arange(1,n+1),3,replace=False).tolist());extra.append(np.concatenate([key[:a],key[c:e],key[a:c],key[e:]]))
                keys=np.concatenate([keys,np.array(extra)])
            votes,C,invalid=scores(messages,keys,prepared);values=votes.max(axis=1);k=int(np.argmax(values));b=int(np.argmax(votes[k]))
            if best is None or int(values[k])>best['votes']:
                best={'votes':int(values[k]),'comparisons':C,'key':keys[k].copy(),'rotation':b,'restart':restart,'step':step,'invalid':int(invalid[k])}
            if step%10==0:print('restart',restart,'step',step,'best agreements',best['votes'],'of',C,'rotation',best['rotation'],flush=True)
            if best['votes']==C and best['invalid']==0:break
            temp=temperature*(1-step/steps)+temperature_floor;pick=int(np.argmax(values+temp*rng.gumbel(size=len(values))));key=keys[pick]
        if best['votes']==C and best['invalid']==0:break
    errors,pt=direct_errors(messages,best['key'].tolist(),best['rotation'],classes)
    assert errors==best['comparisons']-best['votes']-(best['comparisons']+1)*best['invalid']
    assert all(encrypt_physical(p,best['key'],1,best['rotation'])==c for p,c in zip(pt,messages))
    return {'status':'structural_model_fit' if errors==0 and best['invalid']==0 else 'search_inconclusive',
            'initial_deck':best['key'].tolist(),'rotation':best['rotation'],'plaintext_positions':pt,'shared_selection_disagreements':errors,
            'comparisons':best['comparisons'],'temperature':temperature,'temperature_floor':temperature_floor,'block_moves':block_moves,'invalid_top_selections':best['invalid'],'seconds':time.time()-start,'steps_requested':steps,'restarts_requested':restarts,
            'exact_ciphertext_replay':True,'warning':'Exact ciphertext replay alone is automatic for a valid key in this decryptable family. Only zero disagreements fits the stated repeated-plaintext assumptions; neither authenticates meaningful plaintext.'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');ap.add_argument('--near',action='store_true');ap.add_argument('--steps',type=int,default=50);ap.add_argument('--restarts',type=int,default=1);args=ap.parse_args()
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(raw);cl=make_plaintexts(raw,eq);initial=None
    if args.control:
        rng=np.random.default_rng(20261106);key=rng.permutation(83);values={x:int(rng.integers(1,83)) for row in cl for x in row};pt=[[values[x] for x in row] for row in cl]
        for i,row in enumerate(pt):row[0]=i+1
        raw=[encrypt_physical(row,key,1,9) for row in pt]
        if args.near:
            initial=key.copy()
            for _ in range(5):a,b=rng.choice(83,2,replace=False);initial[a],initial[b]=initial[b],initial[a]
        # Voting agrees with direct decoding on random keys and all rotations.
        candidates=np.array([key]+[rng.permutation(83) for _ in range(3)]);v,C,bad=scores(raw,candidates,prepare(cl,82))
        for ki,k in enumerate(candidates):
            for b in range(82):
                error,_=direct_errors(raw,k.tolist(),b,cl);assert int(v[ki,b])==C-error-(C+1)*int(bad[ki])
        assert v[0,9]==C
    r=search(raw,cl,args.steps,args.restarts,initial)
    r['assumed_equalities']=eq
    if args.control:r.update(exact_planted_plaintext_recovered=r['plaintext_positions']==pt,planted_rotation=9,started_five_key_swaps_away=args.near,all_rotation_scoring_checks=328)
    name='rotation_vote_'+('control' if args.control else 'eyes')+('_near' if args.near else '')+'.json'
    (ROOT/name).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({k:v for k,v in r.items() if k not in ['initial_deck','plaintext_positions','assumed_equalities']},flush=True)
