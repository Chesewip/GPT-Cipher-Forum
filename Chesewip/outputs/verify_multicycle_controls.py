"""Generated positive controls for the full multicycle bound and reduction."""
from pathlib import Path
import json
import numpy as np
from multicycle_bound import get_rows,prove
from synchronized_cycle_bound import reduction
from key_swap_attack import partition_q,encrypt
ROOT=Path(__file__).resolve().parent

def main():
    rng=np.random.default_rng(20260921);results=[];checks=0
    partitions=[[L,83-L] for L in range(1,9)]+[[1,41,41],[2,40,41],[3,40,40],[4,39,40],[8,37,38],[2,54,18,6,1,1,1]]
    for parts in partitions:
        q=partition_q(parts);L=parts[0];initial=rng.permutation(83);pos=np.argsort(initial)
        alphabet=rng.choice(np.arange(1,83),32,replace=False)
        pt=[rng.choice(alphabet,120).tolist() for _ in range(9)]
        ct=[encrypt(p,q,initial) for p in pt]
        base,F,ws,obs=reduction(ct,83,L);U=set(initial[:L].tolist())
        boundaries=np.cumsum([0]+parts)
        for mi,t,b in obs:
            if b in F or b in U:continue
            p0=int(pos[b]);k=next(k for k in range(1,len(parts)) if boundaries[k]<=p0<boundaries[k+1])
            expected=int(boundaries[k])+(p0-int(boundaries[k])+t)%parts[k]
            assert pt[mi][t]==expected
            checks+=1
        # The actual unknown deck and alphabet must also satisfy every derived
        # support group, regardless of whether the solver finds that deck.
        result=prove(ct,parts,32,iterations=40,node_limit=20000,seconds=30)
        assert result['status']!='excluded',result
        rows,_,_=get_rows(ct,83,L,parts[1:])
        for g in result['bad_groups']:
            M=g['length']
            for k in range(1,len(parts)):
                if parts[k]!=M:continue
                assigned=[b for b in g['labels'] if boundaries[k]<=pos[b]<boundaries[k+1]]
                if len(assigned)==len(g['labels']):
                    used=set()
                    for b in assigned:
                        p=rows[M][b]
                        used.update((int(pos[b])-int(boundaries[k])+t)%M for t in range(M) if p>>t&1)
                    assert len(used)>=g['minimum_alphabet']
        results.append({'parts':parts,'planted_alphabet':32,'status':result['status'],'derived_groups':len(result['bad_groups'])})
        print(results[-1],flush=True)
    out={'generated_observations_checked':checks,'positive_controls':results,'passed':True}
    (ROOT/'multicycle_controls.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('All controls passed',checks)

if __name__=='__main__':main()
