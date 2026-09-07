"""Sharp three-change construction for the first 50 East1/West1 symbols.

This intentionally constructed cipher is a mathematical counterexample,
not a proposed Noita key or meaningful plaintext. It uses arbitrary fixed
per-letter shuffles and a common initial deck, with distinct non-top source
positions for all letters, so it is reversible and prevents adjacent repeats.
"""
from pathlib import Path
import json,random
from plaintext_change_bounds import encrypt,latest_changes
ROOT=Path(__file__).resolve().parent

def complete_partial(pairs,n):
    f=dict(pairs);assert len(set(f.values()))==len(f)
    for start in list(f):
        if start in f.values():continue
        end=start
        while end in f:end=f[end]
        f[end]=start
    for x in range(n):f.setdefault(x,x)
    assert set(f.values())==set(range(n))
    return [f[x] for x in range(n)]

def fill(assigned,n,rng):
    assert len(set(assigned.values()))==len(assigned)
    free=[x for x in range(n) if x not in assigned.values()];rng.shuffle(free);out=[None]*n
    for p,c in assigned.items():out[p]=c
    it=iter(free)
    return [next(it) if x is None else x for x in out]

def permutation(before,after):
    pos={c:p for p,c in enumerate(after)}
    return [pos[c] for c in before]

if __name__=='__main__':
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());a,b=[m[:50] for m in raw[:2]]
    n=83;cuts=[0,25,33,50];rng=random.Random(20261022);relations=[]
    for left,right in zip(cuts,cuts[1:]):
        relation=complete_partial(list(zip(a[left:right],b[left:right])),n)
        assert all(relation[x]==y for x,y in zip(a[left:right],b[left:right]));relations.append(relation)
    pa=[];pb=[];token=0
    for t in range(50):
        pa.append(token);token+=1
        if t in cuts[:-1]:pb.append(token);token+=1
        else:pb.append(pa[-1])
    assert token==53
    sources=[x+1 for x in range(token)]
    key=fill({sources[pa[0]]:a[0],sources[pb[0]]:b[0]},n,rng)
    da=key.copy();db=key.copy();perms=[None]*token;trace=[]
    for t in range(50):
        block=max(i for i,left in enumerate(cuts[:-1]) if left<=t);rel=relations[block]
        inv=[rel.index(x) for x in range(n)];assign={0:a[t]}
        if t+1<50:
            assign[sources[pa[t+1]]]=a[t+1]
            if pa[t+1]!=pb[t+1]:assign[sources[pb[t+1]]]=inv[b[t+1]]
        nexta=fill(assign,n,rng);nextb=[rel[c] for c in nexta]
        qa=permutation(da,nexta);qb=permutation(db,nextb)
        assert qa[sources[pa[t]]]==0 and qb[sources[pb[t]]]==0
        if pa[t]==pb[t]:assert qa==qb
        perms[pa[t]]=qa;perms[pb[t]]=qb
        da=nexta;db=nextb
        trace.append({'position':t,'plaintext_tokens':[pa[t],pb[t]],'ciphertext':[da[0],db[0]],
                      'different_deck_positions':sum(x!=y for x,y in zip(da,db))})
    assert all(p is not None for p in perms)
    assert all(p.index(0)==sources[i] and p[0]!=0 for i,p in enumerate(perms))
    assert encrypt(pa,key,perms)==a and encrypt(pb,key,perms)==b
    assert sum(x!=y for x,y in zip(pa,pb))==3
    assert all(t['different_deck_positions']>0 for t in trace)
    out={'status':'Constructed counterexample, not a Noita decryption','ciphertext_prefix_length':50,
         'plaintext_alphabet_size':token,'plaintext_difference_positions':[0,25,33],
         'minimum_change_bound':latest_changes(a,b)['minimum_total_with_common_initial_deck'],
         'common_initial_deck':key,'plaintext_tokens':[pa,pb],'per_letter_permutations':perms,
         'relative_label_permutations':relations,'trace':trace,
         'matched_real_ciphertext_exactly':True,'all_deck_states_remain_distinct':True,
         'warning':'The arbitrary shuffles were engineered to fit this prefix. The tokens have no linguistic interpretation and the remaining messages are not fitted.'}
    (ROOT/'sharp_prefix_counterexample.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('matched actual prefixes; 53 reversible letters; 3 plaintext differences; relation supports', [sum(x!=y for x,y in enumerate(r)) for r in relations])
