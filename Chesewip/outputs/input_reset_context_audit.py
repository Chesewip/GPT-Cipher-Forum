"""Conditional context-triggered overwrite audit; no Eye plaintext recovery.

Ordinary increments may depend on the whole shared input window. At an
overwrite, the replacement state and trigger depend only on that window.
"""
from pathlib import Path
import hashlib,json,random
from periodic_reset_screen import eliminate
from recurrence_transfer_audit import equations,screen
ROOT=Path(__file__).resolve().parent

def eligible(messages,equalities,trim):
    trimmed=[[i,s+trim,j,t+trim,n-trim] for i,s,j,t,n in equalities if n>trim]
    return [e for e in equations(messages,trimmed)
            if messages[e['positions'][0][0]][e['positions'][0][1]] !=
               messages[e['positions'][1][0]][e['positions'][1][1]]]

def result_for(eqs):
    r=eliminate([e['row'] for e in eqs])
    if r['status']=='forced_output_collision':
        co=r.pop('coefficients')
        r['certificate']=dict(labels=r.pop('labels'),terms=[dict(positions=e['positions'],coefficient=c) for e,c in zip(eqs,co) if c])
    r['equation_count']=len(eqs)
    return r

def integer_proof(messages,equalities,trim):
    trimmed=[[i,s+trim,j,t+trim,n-trim] for i,s,j,t,n in equalities if n>trim]
    proof=screen(messages,trimmed)['certificate']
    for term in proof['terms']:
        if term['coefficient']>41:term['coefficient']-=83
    total=[0]*83
    for term in proof['terms']:
        for (mi,t),sgn in zip(term['positions'],[1,-1]):
            total[messages[mi][t]]+=sgn*term['coefficient']
            total[messages[mi][t-1]]-=sgn*term['coefficient']
    wanted=[0]*83;wanted[proof['labels'][0]]=1;wanted[proof['labels'][1]]=-1
    assert total==wanted
    return dict(trim=trim,certificate=proof,integer_sum=total)

def control(messages,seed,length,timing):
    rng=random.Random(seed);starts=[rng.randrange(6,25) for _ in messages]
    word=[rng.randrange(2,27) for _ in range(60)];word[12]=0;word[32]=1
    reset_contexts={tuple(word[d-length+1:d+1]) for d in [12,32]}
    plain=[[None]+[rng.randrange(27) for _ in m[1:]] for m in messages]
    for pt,s in zip(plain,starts):pt[s:s+60]=word
    contexts={tuple(pt[max(1,t-length+1):t+1]) for pt in plain for t in range(1,len(pt))}
    table={h:(rng.randrange(1,83),rng.randrange(83),h in reset_contexts) for h in sorted(contexts)}
    perm=rng.sample(range(83),83);key=[perm.index(label) for label in range(83)]
    initial=[rng.randrange(83) for _ in messages];cipher=[];resets=[]
    for pt,state in zip(plain,initial):
        ct=[rng.randrange(83)];rs=[]
        for t,p in enumerate(pt[1:],1):
            h=tuple(pt[max(1,t-length+1):t+1]);step,replacement,trigger=table[h]
            if timing=='before':
                state=replacement if trigger else (state+step)%83;ct.append(perm[state])
            else:
                output=(state+step)%83;ct.append(perm[output]);state=replacement if trigger else output
            if trigger:rs.append(t)
        cipher.append(ct);resets.append(rs)
    eq=[[0,starts[0],i,starts[i],60] for i in range(1,9)]
    trim=length-1 if timing=='before' else length
    usable=eligible(cipher,eq,trim);r=result_for(usable)
    assert r['status']=='no_forced_collision'
    assert all(sum(v*w for v,w in zip(e['row'],key))%83==0 for e in usable)
    raw=equations(cipher,[[i,s+trim,j,t+trim,n-trim] for i,s,j,t,n in eq])
    bad=[e['positions'] for e in raw if sum(v*w for v,w in zip(e['row'],key))%83]
    naive=result_for(raw);assert naive['status']=='forced_output_collision' and bad
    suffixes=[]
    for i,s,j,t,n in eq:
        first=next(d for d in range(trim,n) if s+d in resets[i])
        start=first+(timing=='after')
        assert cipher[i][s+start:s+n]==cipher[j][t+start:t+n]
        suffixes.append(dict(messages=[i,j],shared_reset_offset=first,equal_output_suffix_offset=start,length=n-start))
    return dict(seed=seed,context_length=length,timing=timing,plaintext=plain,ciphertext=cipher,
                equalities=eq,initial_states=initial,true_label_to_residue=key,
                context_table=[dict(context=list(h),step=a,replacement=b,trigger=c) for h,(a,b,c) in sorted(table.items())],
                reset_positions=resets,trim=trim,result=r,naive_result=naive,
                incorrectly_retained_rows=bad,synchronized_suffixes=suffixes)

def main():
    data=(ROOT/'ciphertext.json').read_bytes();source=(ROOT/'state_memory_comparison.json').read_bytes()
    messages=list(json.loads(data).values());assumptions=json.loads(source)['assumption_sets']
    out=dict(status='Conditional context-triggered overwrite exclusion; no Eye key.',
             ciphertext_sha256=hashlib.sha256(data).hexdigest(),parent_sha256=hashlib.sha256(source).hexdigest(),
             assumption_sets={name:assumptions[name] for name in ['early','late','strong']},screens={},integer_proofs={},controls=[])
    for name,eq in out['assumption_sets'].items():
        cases=[]
        for trim in range(28):
            r=result_for(eligible(messages,eq,trim));r['trim']=trim;cases.append(r)
        out['screens'][name]=cases
        print(name,'excluded trims',[r['trim'] for r in cases if r['status']=='forced_output_collision'],flush=True)
    for name,trim in [('early',10),('late',16)]:out['integer_proofs'][name]=integer_proof(messages,assumptions[name],trim)
    for j,(length,timing) in enumerate((l,t) for l in [1,2,5] for t in ['before','after']):
        c=control(messages,909600+j,length,timing);out['controls'].append(c)
        print('Control',c['seed'],length,timing,'eligible rows',c['result']['equation_count'],'unmasked wrong rows',len(c['incorrectly_retained_rows']),flush=True)
    (ROOT/'input_reset_context_audit.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
