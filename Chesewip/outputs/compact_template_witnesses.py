"""Compact engineered witnesses for minimum-change East1/West1 templates.

A fresh token may be repeated several times within a run. Its one fixed
permutation must produce the entire run. This reduces alphabet size while
retaining reversibility and the actual ciphertext. These are artificial
counterexamples, not meaningful plaintext or proposed Noita mechanisms.
"""
from pathlib import Path
import json,random
from sharp_prefix_counterexample import fill,permutation
ROOT=Path(__file__).resolve().parent

def partial_map(a,b):
    f={};g={}
    for x,y in zip(a,b):
        if (x in f and f[x]!=y) or (y in g and g[y]!=x):return None
        f[x]=y;g[y]=x
    return f

def complete_relation(f,n,forbidden,rng):
    domains=[x for x in range(n) if x not in f];targets=[x for x in range(n) if x not in f.values()]
    for _ in range(100):
        rng.shuffle(targets);out={**f,**dict(zip(domains,targets))}
        if forbidden is None or out[forbidden[0]]!=forbidden[1]:return [out[x] for x in range(n)]
    raise ValueError('Forbidden boundary relation cannot be avoided')

def instructions(a,b,cuts,cap):
    out=[];N=len(a)
    for lo,hi in zip(cuts,cuts[1:]):
        out.append((lo,1,False));t=lo+1
        while t<hi:
            for length in range(min(cap,hi-t),0,-1):
                seq=a[t-1:t+length]
                if partial_map(seq[1:],seq[:-1]) is not None:break
            out.append((t,length,True));t+=length
    return out

def construct(a,b,cuts,cap=3,seed=20261025,max_attempts=5000):
    rng=random.Random(seed);n=83;plan=instructions(a,b,cuts,cap);nletters=sum(1 if same else 2 for _,_,same in plan)
    if nletters>82:raise ValueError('Too many distinct output sources')
    observed=[]
    for lo,hi in zip(cuts,cuts[1:]):
        f=partial_map(a[lo:hi],b[lo:hi])
        if f is None:raise ValueError('Inconsistent shared-plaintext segment')
        forbidden=None if hi==len(a) else (a[hi],b[hi])
        if forbidden is not None and f.get(forbidden[0])==forbidden[1]:raise ValueError('Reversibility forces equality at proposed change')
        observed.append((f,forbidden))
    for attempt in range(1,max_attempts+1):
        relations=[complete_relation(f,n,forbidden,rng) for f,forbidden in observed]
        key=list(range(n));rng.shuffle(key);da=key.copy();db=key.copy();pa=[];pb=[];perms=[];sources=set();trace=[];okay=True
        for t,length,same in plan:
            if not same:
                sa=da.index(a[t]);sb=db.index(b[t])
                if sa==sb or sa==0 or sb==0 or sa in sources or sb in sources:okay=False;break
                block=cuts.index(t);rel=relations[block];na=fill({0:a[t]},n,rng);nb=[rel[x] for x in na]
                qa=permutation(da,na);qb=permutation(db,nb)
                pa.append(len(perms));perms.append(qa);pb.append(len(perms));perms.append(qb)
                sources.update([sa,sb]);da,db=na,nb
                trace.append(sum(x!=y for x,y in zip(da,db)))
            else:
                orbit=[0]+[da.index(x) for x in a[t:t+length]]
                fixed=partial_map(orbit[1:],orbit[:-1]);assert fixed is not None
                source=orbit[1]
                if source==0 or source in sources:okay=False;break
                domain=[x for x in range(n) if x not in fixed];target=[x for x in range(n) if x not in fixed.values()]
                rng.shuffle(target);q={**fixed,**dict(zip(domain,target))};q=[q[x] for x in range(n)]
                inverse=[q.index(x) for x in range(n)];token=len(perms);perms.append(q);sources.add(source)
                for j in range(length):
                    da=[da[x] for x in inverse];db=[db[x] for x in inverse]
                    assert da[0]==a[t+j] and db[0]==b[t+j]
                    pa.append(token);pb.append(token);trace.append(sum(x!=y for x,y in zip(da,db)))
        if not okay:continue
        assert len(pa)==len(pb)==len(a) and len(perms)==nletters
        assert len({q.index(0) for q in perms})==nletters and all(q[0]!=0 for q in perms)
        changed=[t for t,(x,y) in enumerate(zip(pa,pb)) if x!=y];assert changed==cuts[:-1]
        return {'status':'Engineered counterexample; not a decryption','prefix_length':len(a),
                'alphabet_size':len(perms),'attempts':attempt,'plaintext_difference_positions':changed,
                'common_initial_deck':key,'plaintext_tokens':[pa,pb],'per_letter_permutations':perms,
                'relative_state_support_by_position':trace,'maximum_token_run_length':cap,
                'warning':'Tokens are artificial, often repeated in runs. No linguistic plaintext is claimed.'}
    return {'status':'inconclusive','attempts':max_attempts,'alphabet_size_requested':nletters,'cuts':cuts}

if __name__=='__main__':
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());a,b=[m[:50] for m in raw[:2]];results=[];rejected=[]
    for c1 in range(22,26):
        for c2 in range(28,34):
            cuts=[0,c1,c2,50]
            try:result=construct(a,b,cuts)
            except ValueError as ex:rejected.append({'cuts':cuts,'reason':str(ex)});continue
            if result['status']=='inconclusive':print('inconclusive',cuts,flush=True)
            else:print(cuts,'alphabet',result['alphabet_size'],'attempts',result['attempts'],flush=True)
            results.append(result)
    (ROOT/'compact_template_witnesses.json').write_text(json.dumps({'witnesses':results,'rejected':rejected},indent=2)+'\n',encoding='utf-8',newline='\r\n')
