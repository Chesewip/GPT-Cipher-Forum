"""Independent finite hitting-set checker; no SMT is used for this check."""
from pathlib import Path
import json,functools,argparse,time
from synchronized_cycle_bound import reduction
from cycle_subset_bound import feasible
ROOT=Path(__file__).resolve().parent

def can_hit(group_lists,budget):
    groups=tuple(sorted(set(sum(1<<c for c in g) for g in group_lists)))
    calls=0
    @functools.lru_cache(None)
    def dfs(remaining,k):
        nonlocal calls
        calls+=1
        if not remaining:return True
        if k==0:return False
        ordered=sorted(remaining,key=int.bit_count)
        # Any pairwise-disjoint subfamily needs one deletion per group.
        occupied=0;packing=0
        for g in ordered:
            if not g&occupied:
                occupied|=g;packing+=1
        if packing>k:return False
        first=ordered[0];vertices=[]
        while first:
            bit=first&-first;first-=bit
            vertices.append(bit)
        vertices.sort(key=lambda b:sum(bool(b&g) for g in remaining),reverse=True)
        return any(dfs(tuple(g for g in remaining if not g&b),k-1) for b in vertices)
    answer=dfs(groups,budget)
    return answer,calls

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('certificate');args=ap.parse_args()
    path=ROOT/args.certificate;data=json.loads(path.read_text())
    assert data['status']=='excluded'
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    L,M=data['cycle_partition'];rows,_,_,_=reduction(messages,L+M,L)
    start=time.time()
    for group in data['bad_groups']:
        assert feasible([rows[c] for c in group],M,data['outside_alphabet_bound'])['status']=='unsat'
    possible,calls=can_hit(data['bad_groups'],data['hitting_set_budget'])
    assert not possible
    result=dict(certificate=path.name,bad_groups_rechecked=len(data['bad_groups']),
                independent_hitting_set_nodes=calls,passed=True,seconds=time.time()-start)
    (ROOT/('checked_'+path.name)).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(result)
