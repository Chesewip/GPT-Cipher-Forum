"""Exact loop-transfer diagnostics and cyclic-feedback calibration.

The cyclic family is established prior work. Exclusions are conditional on
listed plaintext equalities; engineered token streams are not plaintext.
"""
from pathlib import Path
from collections import Counter
import json,hashlib,random,itertools
from state_memory_comparison import observations,Union
ROOT=Path(__file__).resolve().parent
MOD=83

def equations(messages,equalities):
    result=[]
    for i,s,j,t,n in equalities:
        for k in range(n):
            a,b=s+k,t+k
            if min(a,b)<2:continue
            row=[0]*MOD
            for label,sign in [(messages[i][a],1),(messages[i][a-1],-1),(messages[j][b],-1),(messages[j][b-1],1)]:row[label]=(row[label]+sign)%MOD
            if any(row):result.append(dict(positions=[[i,a],[j,b]],row=row))
    return result

def basis(rows,proof=False):
    bs={}
    for i,original in enumerate(rows):
        row=original.copy();coeff=[0]*len(rows)
        if proof:coeff[i]=1
        for p,(v,w) in sorted(bs.items()):
            a=row[p]
            if a:
                row=[(x-a*y)%MOD for x,y in zip(row,v)]
                if proof:coeff=[(x-a*y)%MOD for x,y in zip(coeff,w)]
        if any(row):
            p=next(j for j,x in enumerate(row) if x);a=pow(row[p],-1,MOD)
            bs[p]=([(a*x)%MOD for x in row],[(a*x)%MOD for x in coeff] if proof else [])
    return bs

def forced_pair(bs,a,b):
    row=[0]*MOD;row[a]=1;row[b]=MOD-1;weights=None
    for p,(v,w) in sorted(bs.items()):
        c=row[p]
        if c:
            row=[(x-c*y)%MOD for x,y in zip(row,v)]
            if w:
                if weights is None:weights=[0]*len(w)
                weights=[(x+c*y)%MOD for x,y in zip(weights,w)]
    return None if any(row) else (weights or [])

def screen(messages,equalities):
    eqs=equations(messages,equalities);rows=[e['row'] for e in eqs];bs=basis(rows)
    pairs=[[a,b] for a in range(MOD) for b in range(a) if forced_pair(bs,a,b) is not None]
    out=dict(rank=len(bs),nullity=MOD-len(bs),equation_count=len(rows),forced_label_collisions=pairs)
    if not pairs:out['status']='linear_constraints_survive';return out
    # Obtain a short irredundant certificate for the first forced pair. This
    # deletion procedure does not establish globally minimum support.
    a,b=pairs[0];indices=list(range(len(rows)))
    for index in indices.copy():
        trial=[v for v in indices if v!=index]
        if forced_pair(basis([rows[v] for v in trial]),a,b) is not None:indices=trial
    reduced=[rows[v] for v in indices];weights=forced_pair(basis(reduced,True),a,b)
    assert weights is not None
    out.update(status='injective_output_map_impossible',certificate=dict(labels=[a,b],terms=[dict(positions=eqs[v]['positions'],coefficient=c) for v,c in zip(indices,weights) if c]))
    return out

def normalize_key(key):
    inv=pow((key[1]-key[0])%MOD,-1,MOD)
    return [((v-key[0])*inv)%MOD for v in key]

def recover(messages,equalities):
    rows=[e['row'] for e in equations(messages,equalities)];bs=basis(rows)
    free=[j for j in range(MOD) if j not in bs];vectors=[]
    for j in free:
        v=[0]*MOD;v[j]=1
        for p,(row,_) in sorted(bs.items(),reverse=True):v[p]=-sum(row[k]*v[k] for k in range(p+1,MOD))%MOD
        vectors.append(v)
    out=dict(rank=len(bs),nullity=len(free))
    if len(free)==2:
        nonconstant=next(v for v in vectors if len(set(v))>1)
        if nonconstant[0]!=nonconstant[1]:
            key=normalize_key(nonconstant)
            if len(set(key))==MOD:
                out.update(status='output_map_recovered_up_to_affine_change',normalized_label_to_residue=key);return out
    out['status']='linear_information_insufficient_for_unique_map'
    return out

def control(messages,source_equalities,seed,dense):
    rng=random.Random(seed);positions=[(i,t) for i,m in enumerate(messages) for t in range(1,len(m))];index={v:i for i,v in enumerate(positions)}
    if dense:
        starts=[rng.randrange(2,25) for _ in messages];eqs=[[0,starts[0],j,starts[j],60] for j in range(1,len(messages))]
    else:eqs=source_equalities
    u=Union(len(positions))
    for i,s,j,t,n in eqs:
        for d in range(n):u.join(index[i,s+d],index[j,t+d],None)
    selected={u.root(v):rng.randrange(27) for v in range(len(positions))}
    plain=[[None]+[selected[u.root(index[i,t])] for t in range(1,len(m))] for i,m in enumerate(messages)]
    steps=rng.sample(range(1,MOD),27);perm=rng.sample(range(MOD),MOD);key=[perm.index(label) for label in range(MOD)]
    initials=[rng.randrange(MOD) for _ in messages] if dense else [0]*len(messages)
    ciphertext=[]
    for state,pt in zip(initials,plain):
        c=[rng.randrange(MOD)]
        for p in pt[1:]:state=(state+steps[p])%MOD;c.append(perm[state])
        ciphertext.append(c)
    result=recover(ciphertext,eqs)
    if result['status']=='output_map_recovered_up_to_affine_change':
        assert result['normalized_label_to_residue']==normalize_key(key)
    else:
        assert all(sum(e['row'][j]*key[j] for j in range(MOD))%MOD==0 for e in equations(ciphertext,eqs))
    return dict(seed=seed,layout='nine_repeated_60_token_passages' if dense else 'existing_eye_hypothesis_layout',equalities=eqs,
        plaintext=plain,ciphertext=ciphertext,initial_residues=initials,input_steps=steps,true_label_to_residue=key,result=result)

def loop_tests(messages,word_sources,edges):
    loops=[]
    for mi,start,n,word in word_sources:
        c=messages[mi][start:start+n]
        for a,b in itertools.combinations(range(n),2):
            if c[a]!=c[b]:continue
            subword=word[a+1:b+1];complete=0;bad=[]
            for initial in range(MOD):
                q=initial;path=[]
                for token in subword:
                    if (token,q) not in edges:break
                    finish,location=edges[token,q];path.append(dict(token=token,before=q,after=finish,location=location));q=finish
                else:
                    complete+=1
                    if q!=initial:bad.append(dict(initial=initial,finish=q,path=path))
            loops.append(dict(source=[mi,start,n],equal_output_offsets=[a,b],word=subword,fully_observed_paths=complete,violations=bad))
    return loops

def main():
    data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values());parent_bytes=(ROOT/'state_memory_comparison.json').read_bytes();parent=json.loads(parent_bytes)
    out=dict(status='Loop diagnostics and conditional cyclic-feedback replication; no decipherment.',ciphertext_sha256=hashlib.sha256(data).hexdigest(),parent_sha256=hashlib.sha256(parent_bytes).hexdigest(),engineered_loop_tests=[],cyclic_cases={},controls=[])
    for wi,w in enumerate(parent['engineered_fits']):
        edges={}
        for mi,(m,pt,q) in enumerate(zip(messages,w['body_tokens'],w['initial_states'])):
            for t,(c,p) in enumerate(zip(m[1:],pt),1):edges[p,q]=(c,[mi,t]);q=c
        words=[(mi,start,n,w['body_tokens'][mi][start-1:start-1+n]) for mi,start,n in [(1,37,15),(6,71,27)]]
        out['engineered_loop_tests'].append(dict(parent_witness=wi,loops=loop_tests(messages,words,edges)))
    # Keep every input class separate unless the stated passage hypotheses
    # or the same observed (previous,current) pair identify them.
    nodes,positions=observations(messages,dict(kind='window',memory=1,header='metadata'));u=Union(len(nodes))
    for i,s,j,t,n in parent['assumption_sets']['full_prefix']:
        for k in range(n):
            if (i,s+k) in positions and (j,t+k) in positions:u.join(positions[i,s+k],positions[j,t+k],None)
    tokens=[u.root(v) for v in range(len(nodes))];edges={}
    for (mi,t),v in positions.items():edges[tokens[v],nodes[v][0][0]]=(nodes[v][1],[mi,t])
    words=[(mi,start,n,[tokens[positions[mi,t]] for t in range(start,start+n)]) for mi,start,n in [(1,37,15),(6,71,27)]]
    out['unmerged_loop_test']=dict(node_tokens=tokens,token_classes=len(set(tokens)),loops=loop_tests(messages,words,edges))
    sets=parent['assumption_sets'].copy();sets['within_W1']=[sets['early'][0]];sets['within_E2']=[sets['early'][1]]
    for name,eqs in sets.items():
        result=screen(messages,eqs);result['equalities']=eqs;out['cyclic_cases'][name]=result
        print('Cyclic',name,result['status'],'nullity',result['nullity'],'certificate terms',len(result.get('certificate',{}).get('terms',[])),flush=True)
    for dense,seeds in [(False,range(909400,909403)),(True,range(909420,909423))]:
        for seed in seeds:
            c=control(messages,sets['full_prefix'],seed,dense);out['controls'].append(c);print('Control',seed,c['result']['status'],'nullity',c['result']['nullity'],flush=True)
    (ROOT/'recurrence_transfer_audit.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
