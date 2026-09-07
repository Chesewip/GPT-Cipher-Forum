"""Exact collision bounds for arbitrary 3x3 quinary first-order feedback.

No plaintext equality or language assumptions. Exhaustive finite matrix family.
"""
from pathlib import Path
from collections import Counter
import itertools, hashlib, json, time
import numpy as np
ROOT=Path(__file__).resolve().parent
V=np.array(list(itertools.product(range(5),repeat=3)),dtype=np.int64)
WEIGHTS=np.array([25,5,1],dtype=np.int64)
REPS=[(0,1)+p for p in itertools.permutations((2,3,4))]
DIRECTIONS=np.array([v for v in V if any(v) and next(x for x in v if x)!=0 and next(x for x in v if x)==1])
DINDEX={tuple(v):i for i,v in enumerate(DIRECTIONS)}


def observations(messages,pi=(0,1,2,3,4),lag=1,reverse=False):
    x,y=[],[]
    for raw in messages:
        body=raw[1:]
        if reverse: body=body[::-1]
        digits=np.array(pi)[V[body]]
        x.extend(digits[:-lag]);y.extend(digits[lag:])
    return np.array(x),np.array(y)


def collision_table(x,y):
    table=np.zeros((31,125),dtype=np.int64);constant=0
    for i in range(len(x)):
        dx=(x[i+1:]-x[i])%5;dy=(y[i+1:]-y[i])%5
        for u,v in zip(dx,dy):
            nz=np.flatnonzero(u)
            if not len(nz):
                constant+=int(not np.any(v));continue
            inv=pow(int(u[nz[0]]),-1,5)
            d=tuple((u*inv)%5);w=int(((v*inv)%5)@WEIGHTS)
            table[DINDEX[d],w]+=1
    return constant,table


def score_matrices(constant,table):
    # Matrix rows indexed by their base-5 row coefficient code, each 0..124.
    dots=(V@DIRECTIONS.T)%5
    scores=np.full((125,125,125),constant,dtype=np.int64)
    for j in range(31):
        z=dots[:,j]
        codes=25*z[:,None,None]+5*z[None,:,None]+z[None,None,:]
        scores+=table[j,codes]
    return scores


def min_pairs(n,k):
    q,r=divmod(n,k)
    return r*q*(q+1)//2+(k-r)*q*(q-1)//2


def bound(n,maximum):
    return next(k for k in range(1,126) if min_pairs(n,k)<=maximum)


def result(x,y):
    c,t=collision_table(x,y);scores=score_matrices(c,t)
    best=tuple(int(i) for i in np.unravel_index(int(np.argmax(scores)),scores.shape))
    a=V[list(best)];res=(y-x@a.T)%5;codes=res@WEIGHTS
    counts=Counter(map(int,codes));coll=sum(n*(n-1)//2 for n in counts.values())
    assert coll==int(scores[best])
    hist=Counter(map(int,scores.ravel()))
    return dict(observations=len(x),matrices_tested=int(scores.size),
                constant_identical_pairs=c,direction_collision_table=t.tolist(),
                maximum_collision_pairs=coll,universal_support_lower_bound=bound(len(x),coll),
                first_maximizing_matrix=a.tolist(),maximizer_support=len(counts),
                maximizer_counts=dict(sorted(counts.items())),
                collision_score_histogram=dict(sorted(hist.items())))


def generated_control(seed,pi):
    rng=np.random.default_rng(seed);a=rng.integers(0,5,size=(3,3));alphabet=rng.choice(125,27,replace=False)
    messages=[];truth=[]
    for length in [99,103,118,102,137,124,119,120,114]:
        previous=rng.integers(0,5,size=3);body=[int(previous@WEIGHTS)];pts=[]
        for _ in range(length-2):
            p=V[int(rng.choice(alphabet))];current=(a@previous+p)%5
            body.append(int(current@WEIGHTS));pts.append(int(p@WEIGHTS));previous=current
        messages.append([0]+body);truth.extend(pts)
    # Convert from the planted coordinate convention back to canonical digits.
    inv=np.argsort(pi);messages=[[int(inv[V[v]]@WEIGHTS) for v in m] for m in messages]
    x,y=observations(messages,pi);decoded=((y-x@a.T)%5)@WEIGHTS
    assert decoded.tolist()==truth and len(set(truth))==27
    out=result(x,y)
    assert out['universal_support_lower_bound']<=27
    out.update(seed=seed,direction_mapping=list(pi),matrix=a.tolist(),ciphertext=messages,
               planted_plaintext=truth,planted_support=27)
    return out


def main():
    start=time.time();path=ROOT/'ciphertext.json';messages=list(json.loads(path.read_text(encoding='utf-8')).values())
    out=dict(status='Exact finite-family collision bound; cipher unsolved.',
        corpus_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),modulus=5,
        model='P_t = C_t - A C_(t-lag) + k over F5^3; arbitrary 3x3 A and common constant k.',
        first_symbol='Header excluded; lag preceding body symbols unconstrained.',
        direction_representatives=REPS,cases=[],controls=[],
        caveat='Canonical trigram grouping retained. No plaintext assumptions. Nonlinear block relabeling, higher-order feedback, per-message keys or offsets are outside scope.')
    target=ROOT/'quinary_feedback_screen.json'
    def save():target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    for index,pi in enumerate(REPS):
        r=result(*observations(messages,pi));r.update(direction_mapping=list(pi),lag=1,reverse=False)
        out['cases'].append(r);save()
        print('Direction convention',index+1,'bound',r['universal_support_lower_bound'],'max pairs',r['maximum_collision_pairs'],'maximizer support',r['maximizer_support'],flush=True)
    for i,pi in enumerate([REPS[0],REPS[-1]]):
        out['controls'].append(generated_control(907300+i,pi));save()
        print('Generated control',i+1,'passed',flush=True)
    out['seconds']=time.time()-start;save()

if __name__=='__main__':main()
