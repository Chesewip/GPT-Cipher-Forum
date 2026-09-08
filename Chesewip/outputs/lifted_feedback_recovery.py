"""Calibrated nonlinear feedback recovery through two unknown label maps.

Repeated-input rows are linear in separate output and feedback maps. Only if
those maps are identified do we enumerate the three explicit linking rules.
"""
from pathlib import Path
import hashlib,json,random,sys
import numpy as np
from frozen_candidate_search import table,clean,ALPHABET,evaluate
ROOT=Path(__file__).resolve().parent

def rows_for(messages,equalities):
    rows=[]
    for i,s,j,t,n in equalities:
        for d in range(n):
            a,b=s+d,t+d;row=[0]*166
            for col,sign in [(messages[i][a],1),(83+messages[i][a-1],-1),(messages[j][b],-1),(83+messages[j][b-1],1)]:row[col]+=sign
            if any(row):rows.append([v%83 for v in row])
    return rows

def solve_maps(messages,equalities,complete_missing=False):
    rows=rows_for(messages,equalities);matrix=np.array(rows,dtype=np.int64).reshape((-1,166));rank=0;pivots=[]
    for col in range(166):
        choices=np.flatnonzero(matrix[rank:,col])
        if not len(choices):continue
        k=rank+int(choices[0]);matrix[[rank,k]]=matrix[[k,rank]];matrix[rank]=matrix[rank]*pow(int(matrix[rank,col]),-1,83)%83
        mult=matrix[:,col].copy();mult[rank]=0;matrix=(matrix-mult[:,None]*matrix[rank])%83;pivots.append(col);rank+=1
    out=dict(rank=rank,nullity=166-rank,nonzero_rows=len(rows),status='underdetermined_label_maps')
    inactive=[j for j in range(166) if not any(row[j] for row in rows)]
    completion=rank!=163 and complete_missing and 166-len(inactive)-rank==3 and len([j for j in inactive if j<83])<=1 and not set(inactive)&{0,1,83}
    if rank!=163 and not completion:return out
    # Normalize output labels 0,1 to 0,1 and feedback label 0 to 0.
    fixed=[(0,0),(1,1),(83,0)]+[(j,0) for j in inactive]
    aug=np.array([row+[0] for row in rows]+[[int(j==c) for j in range(166)]+[v] for c,v in fixed],dtype=np.int64)
    r=0
    for col in range(166):
        k=next((i for i in range(r,len(aug)) if aug[i,col]),None)
        if k is None:return out
        aug[[r,k]]=aug[[k,r]];aug[r]=aug[r]*pow(int(aug[r,col]),-1,83)%83
        mult=aug[:,col].copy();mult[r]=0;aug=(aug-mult[:,None]*aug[r])%83;r+=1
    if any(not row[:166].any() and row[166] for row in aug):return out
    values=aug[:166,166].tolist();u,v=values[:83],values[83:]
    if completion:
        missing=[j for j in inactive if j<83];known=[j for j in range(83) if j not in missing]
        unused=sorted(set(range(83))-{u[j] for j in known})
        if len(unused)!=len(missing):return out
        for j,value in zip(missing,unused):u[j]=value
        for j in inactive:
            if j>=83:v[j-83]=None
        out.update(linear_inactive_columns=inactive,completed_output_labels=missing)
    if len(set(u))!=83:return out
    out.update(status='normalized_label_maps_recovered',output_map=u,feedback_map=v,families={})
    for name in ['add','square','inverse']:
        f=table(name);matches=[]
        for scale in range(1,83):
            for shift in range(83):
                key=[(scale*x+shift)%83 for x in u];constant=int(f[shift])
                if all(v[j] is None or (int(f[key[j]])-scale*v[j])%83==constant for j in range(83)):matches.append([scale,shift])
        out['families'][name]=dict(affine_parameters=matches)
        if matches:
            scale,shift=matches[0];key=[(scale*x+shift)%83 for x in u]
            code=sorted({(key[m[t]]-int(f[key[m[t-1]]]))%83 for m in messages[:6] for t in range(2,len(m))})
            out['families'][name].update(selected_key=key,frozen_codebook=code)
    return out

def fixture(name,seed,text):
    rng=random.Random(seed);lengths=[501]*6+[151]*3;plain=[]
    for n in lengths:
        start=rng.randrange(len(text)-n);plain.append([None]+[ALPHABET.index(c) for c in text[start:start+n-1]])
    train=[]
    for block in range(20):
        start=3+24*block
        for mi in range(1,6):plain[mi][start:start+10]=plain[0][start:start+10];train.append([0,start,mi,start,10])
    plain[0][474:501]=list(range(27));late=[[6,50,7,60,27],[6,50,8,70,27]]
    for i,s,j,t,n in late:plain[j][t:t+n]=plain[i][s:s+n]
    f=table(name);allowed=sorted(set(range(83))-{(x-int(f[x]))%83 for x in range(83)})
    codes=rng.sample(allowed,27);perm=rng.sample(range(83),83);key=[perm.index(i) for i in range(83)]
    initials=[rng.randrange(83) for _ in plain];cipher=[]
    for state,pt in zip(initials,plain):
        ct=[rng.randrange(83)]
        for p in pt[1:]:state=(int(f[state])+codes[p])%83;ct.append(perm[state])
        cipher.append(ct)
    return dict(name=name,seed=seed,plaintext=plain,ciphertext=cipher,true_key=key,input_codebook=codes,
                initial_states=initials,training_equalities=train,late_equalities=late)

def main():
    data=(ROOT/'ciphertext.json').read_bytes();parent=(ROOT/'state_memory_comparison.json').read_bytes();sets=json.loads(parent)['assumption_sets']
    source=ROOT.parent/'work'/'pg1661.txt';text=clean(source);messages=list(json.loads(data).values())
    out=dict(executed_date='2026-09-08',status='Lifted-map candidate calibration, not an Eye decipherment.',ciphertext_sha256=hashlib.sha256(data).hexdigest(),
        parent_sha256=hashlib.sha256(parent).hexdigest(),control_text_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        eye_training_equalities=sets['early'],eye=solve_maps(messages,sets['early']),controls=[])
    print('Eye early maps',out['eye']['status'],'rank',out['eye']['rank'],flush=True)
    for i,name in enumerate(['add','square','inverse']):
        c=fixture(name,909850+i,text);r=solve_maps(c['ciphertext'],c['training_equalities']);c['result']=r
        if 'families' in r:
            for family,record in r['families'].items():
                if record['affine_parameters']:
                    record['heldout']=evaluate(c['ciphertext'],c['late_equalities'],dict(name=family,key=record['selected_key'],codebook=record['frozen_codebook']))
        out['controls'].append(c)
        print('Control',name,r['status'],'rank',r['rank'],'family counts',{k:len(v['affine_parameters']) for k,v in r.get('families',{}).items()},flush=True)
    (ROOT/'lifted_feedback_recovery.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

def complete():
    raw=(ROOT/'lifted_feedback_recovery.json').read_bytes();source=json.loads(raw);out=dict(parent_sha256=hashlib.sha256(raw).hexdigest(),controls=[])
    for c in source['controls']:
        r=solve_maps(c['ciphertext'],c['training_equalities'],True)
        for name,record in r.get('families',{}).items():
            if record['affine_parameters']:
                record['heldout']=evaluate(c['ciphertext'],c['late_equalities'],dict(name=name,key=record['selected_key'],codebook=record['frozen_codebook']))
        out['controls'].append(dict(seed=c['seed'],result=r))
        print('Completed control',c['name'],r['status'],{k:len(v['affine_parameters']) for k,v in r.get('families',{}).items()},flush=True)
    (ROOT/'lifted_feedback_completion.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':
    if '--complete' in sys.argv:complete()
    else:main()
