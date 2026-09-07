"""Positive controls and independent finite certificates for the conditional test."""
from pathlib import Path
import json,random,argparse
import numpy as np
from synchronized_isomorph import test,top_selections,invalid_component
from progressive_reduction import RUNS
from key_swap_attack import encrypt
from check_synchronized_certificate import can_hit
ROOT=Path(__file__).resolve().parent

def main(skip=1):
    rng=np.random.default_rng(20260922)
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    lengths=list(map(len,messages));offsets=np.cumsum([0]+lengths).tolist();parent=list(range(offsets[-1]))
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    runs=[(i,s+skip-1,j,t+skip-1,n-skip+1) for i,s,j,t,n in RUNS]
    for i,s,j,t,n in RUNS:
        for k in range(skip,n):parent[root(offsets[i]+s+k)]=root(offsets[j]+t+k)
    controls=[]
    for L in range(1,9):
        for trial in range(10):
            q=np.arange(83,dtype=np.int32)
            for p in range(L):q[p]=(p+1)%L
            q[L:]=rng.permutation(np.arange(L,83))
            initial=rng.permutation(83);alphabet=rng.choice(np.arange(1,83),32,replace=False)
            assigned={r:int(rng.choice(alphabet)) for r in {root(x) for x in parent}}
            pt=[[assigned[root(offsets[i]+t)] for t in range(n)] for i,n in enumerate(lengths)]
            ct=[encrypt(p,q,initial) for p in pt]
            r=test(ct,L,runs)
            assert r['status']!='excluded_conditionally',(L,trial,r)
            # Independently check every directly observed top selection.
            known=top_selections(ct,L)
            for mi,entries in enumerate(known):
                for t,p in entries.items():assert p==(pt[mi][t] if pt[mi][t]<L else None)
            controls.append({'top_cycle':L,'trial':trial,'status':r['status']})
        print('Repeated-plaintext controls passed for top cycle',L,flush=True)
    saved=[test(messages,L,runs) for L in range(1,9)];checks=[]
    if skip>1:
        (ROOT/('trimmed_isomorph_'+str(skip)+'.json')).write_text(json.dumps(saved,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    for result in saved:
        L=result['top_cycle'];fresh=test(messages,L,runs)
        assert fresh['status']=='excluded_conditionally'
        if result['reason']=='incompatible_reduced_permutation':
            edges=result['edges'];labels=set(u for u,v,d in edges)|set(v for u,v,d in edges)
            for group in result['bad_groups']:
                assert invalid_component(edges,labels-set(group),83-L) is not None
            hit,nodes=can_hit(result['bad_groups'],L);assert not hit
            checks.append({'top_cycle':L,'independent_hitting_nodes':nodes,'bad_groups':len(result['bad_groups'])})
        else:checks.append({'top_cycle':L,'direct_selection_contradiction':True})
    # Larger top cycles: the same claimed plaintext selection has observed
    # return gaps 8 and 9. For L>=9 both are in the first top orbit traversal,
    # so the selected positions Q^7(0), Q^8(0) are necessarily different.
    west=messages[1];distances=[]
    for t in [38,68]:
        r=max(r for r in range(t) if west[r]==west[t]);distances.append(t-r)
    assert distances==[8,9]
    assert skip<=4  # The relative-position-4 return-gap witness remains assumed.
    out={'passed':True,'first_included_relative_plaintext_position':skip,'generated_repeated_plaintext_controls':len(controls),
         'control_details':controls,'small_top_cycle_certificates':checks,
         'top_cycles_9_through_83_excluded_by_return_gaps':distances,
         'conditional_conclusion':'Every fixed positional permutation Q is excluded in the one-swap model under the stated internal-plaintext equalities.'}
    name='checked_synchronized_isomorph.json' if skip==1 else 'checked_trimmed_isomorph_'+str(skip)+'.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Passed all 80 controls and all finite certificates.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--skip',type=int,default=1);args=ap.parse_args();main(args.skip)
