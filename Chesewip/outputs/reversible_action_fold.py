"""Saturate action folding with the reversible fixed-output constraint.

Two letters whose inverse updates send top to the same source must be the
same plaintext symbol, if each state must decrypt the output uniquely.
"""
from pathlib import Path
import json,time,random
from permutation_action_fold import solve,make_plaintexts
ROOT=Path(__file__).resolve().parent

def reversible_fold(pts,cts):
    parent={x:x for pt in pts for x in pt}
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    history=[]
    while True:
        current=[[root(x) for x in pt] for pt in pts]
        r=solve(current,cts,include_forced=True)
        groups=r.pop('forced_equal_operations',[]);fixed=r.pop('forced_fixed_output_operations',[])
        history.append({**r,'forced_operation_merges':sum(len(g)-1 for g in groups),'forced_top_fixed_operations':len(fixed)})
        if r['status']=='contradiction' or not groups:break
        for g in groups:
            for x in g[1:]:parent[root(x)]=root(g[0])
    return {'status':r['status'],'iterations':history,'final_plaintext_classes':len({root(x) for x in parent})}

if __name__=='__main__':
    from progressive_reduction import RUNS
    from plaintext_change_bounds import encrypt
    rng=random.Random(20261027);checked=0
    for n in [5,11,83]:
        for _ in range(20):
            perms=[]
            for source in range(1,min(n,6)):
                q=list(range(n));rng.shuffle(q);k=q.index(0);q[k],q[source]=q[source],q[k];perms.append(q)
            key=list(range(n));rng.shuffle(key)
            pts=[[rng.randrange(len(perms)) for _ in range(30)] for j in range(3)]
            cts=[encrypt(p,key,perms) for p in pts]
            # Hide most equal plaintext relations, retaining only one shared occurrence class.
            masked=[[x if t%3==0 else ('fresh',j,t) for t,x in enumerate(pt)] for j,pt in enumerate(pts)]
            result=reversible_fold(masked,cts);assert result['status']=='relaxation_survives';checked+=1
    raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());prefixes=[]
    for i in range(len(raw)):
        for j in range(i):
            t=1
            while t<min(len(raw[i]),len(raw[j])) and raw[i][t]==raw[j][t]:t+=1
            if t>1:prefixes.append((i,1,j,1,t-1))
    out={'valid_reversible_controls':checked,'models':[]}
    for trim in [1,2,3]:
        eq=[(i,s+trim,j,t+trim,n-trim) for i,s,j,t,n in RUNS]+prefixes
        started=time.time();r=reversible_fold(make_plaintexts(raw,eq),raw);r.update(trim=trim,seconds=time.time()-started,assumed_equalities=eq)
        out['models'].append(r);print({k:v for k,v in r.items() if k!='assumed_equalities'},flush=True)
    out['warning']='Necessary consistency closure only; surviving graphs do not establish an 83-card or small-alphabet realization.'
    (ROOT/'reversible_action_fold.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
