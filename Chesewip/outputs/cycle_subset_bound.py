"""Exact subset lower bounds by exhaustive circular-support placement.

For each label b, selected positions include z_b + {t: b_t=b} mod L.
On a single cycle all z_b are distinct. A subset already requiring K positions
proves that the full selection alphabet has at least K symbols.
"""
from pathlib import Path
import json,time,argparse
from progressive_reduction import deswap
ROOT=Path(__file__).resolve().parent

def supports(messages,n,top):
    L=n-1;rows={i:0 for i in range(n) if i!=top}
    for msg in messages:
        for t,b in enumerate(deswap(msg,top,n)):
            if b==top:
                if t==0:continue  # Allow the identity selection at the start.
                raise ValueError('adjacent repeat')
            rows[b]|=1<<(t%L)
    return rows

def feasible(patterns,L,bound,node_limit=10000000):
    mask=(1<<L)-1
    rots=[[((p<<s)|(p>>(L-s)))&mask if s else p for s in range(L)] for p in patterns]
    nodes=0
    def dfs(k,union,occupied):
        nonlocal nodes
        nodes+=1
        if nodes>node_limit:raise TimeoutError('node limit')
        if union.bit_count()>bound:return None
        if k==len(patterns):return []
        choices=[]
        for shift,p in enumerate(rots[k]):
            if occupied>>shift&1:continue
            u=union|p;c=u.bit_count()
            if c<=bound:choices.append((c,shift,u))
        choices.sort()
        for c,shift,u in choices:
            rest=dfs(k+1,u,occupied|(1<<shift))
            if rest is not None:return [shift]+rest
        return None
    try:
        witness=dfs(1,patterns[0],1)
        return dict(status='sat' if witness is not None else 'unsat',nodes=nodes,
                    shifts=None if witness is None else [0]+witness)
    except TimeoutError:return dict(status='unknown',nodes=nodes)

def bound_for(messages,n,top,count=6,target=36):
    rows=supports(messages,n,top)
    labels=sorted(rows,key=lambda c:rows[c].bit_count(),reverse=True)[:count]
    identity_cost=int(any(m[0]==top for m in messages))
    r=feasible([rows[c] for c in labels],n-1,target-identity_cost)
    return dict(top=top,labels=labels,target_alphabet=target,
                identity_selection_cost=identity_cost,**r)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--count',type=int,default=6)
    ap.add_argument('--bound',type=int,default=36);args=ap.parse_args()
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    results=[];start=time.time()
    for top in range(83):
        r=bound_for(messages,83,top,args.count,args.bound);results.append(r)
        if len(results)%10==0:print('completed',len(results),'top candidates;',r['status'],flush=True)
    out=dict(seconds=time.time()-start,results=results,
             all_unsat=all(r['status']=='unsat' for r in results))
    (ROOT/('cycle_subset_'+str(args.count)+'_'+str(args.bound)+'.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('All unsat:',out['all_unsat'],'seconds:',out['seconds'])
