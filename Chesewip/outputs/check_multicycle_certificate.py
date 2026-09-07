"""Check two-residual-cycle certificates with independent finite CSP search.

No SMT is used to decide the coloring problem. Every integer allocation of
the available alphabet between the two residual cycles is checked.
"""
from pathlib import Path
import json,argparse,itertools,time
from multicycle_bound import get_rows
from cycle_subset_bound import feasible
ROOT=Path(__file__).resolve().parent

def colorable(labels,lengths,budgets,top_budget,rows,groups,node_limit=1000000):
    size=len(labels);index={b:i for i,b in enumerate(labels)}
    domains=[7]*size;edges=[];caps=[top_budget]+lengths;nodes=0
    for k,(M,A) in enumerate(zip(lengths,budgets),1):
        bit=1<<k;mask=(1<<M)-1
        for b in labels:
            if rows[M][b].bit_count()>A:domains[index[b]]&=~bit
        for b,c in itertools.combinations(labels,2):
            p,q=rows[M][b],rows[M][c]
            possible=False
            for shift in range(1,M):
                rotated=((q<<shift)|(q>>(M-shift)))&mask
                if (p|rotated).bit_count()<=A:possible=True;break
            if not possible:edges.append((bit,(index[b],index[c])))
        for g in groups:
            if g['length']==M and g['minimum_alphabet']>A:
                edges.append((bit,tuple(index[b] for b in g['labels'])))
    incidence=[0]*size
    for bit,vertices in edges:
        for v in vertices:incidence[v]+=1
    def dfs(ds):
        nonlocal nodes
        nodes+=1
        if nodes>node_limit:raise TimeoutError('independent coloring node limit')
        changed=True
        while changed:
            changed=False
            if any(d==0 for d in ds):return False
            for k,cap in enumerate(caps):
                bit=1<<k;forced=sum(d==bit for d in ds)
                if forced>cap:return False
                if forced==cap:
                    for i,d in enumerate(ds):
                        if d!=bit and d&bit:ds[i]&=~bit;changed=True
            for bit,vertices in edges:
                if any(not ds[v]&bit for v in vertices):continue
                free=[v for v in vertices if ds[v]!=bit]
                if not free:return False
                if len(free)==1:ds[free[0]]&=~bit;changed=True
        unfixed=[i for i,d in enumerate(ds) if d.bit_count()>1]
        if not unfixed:return True
        v=max(unfixed,key=lambda i:(-ds[i].bit_count(),incidence[i]))
        # Try ordinary cycle membership before spending a deletion.
        for bit in [2,4,1]:
            if ds[v]&bit:
                branch=ds.copy();branch[v]=bit
                if dfs(branch):return True
        return False
    try:return {'possible':dfs(domains),'nodes':nodes}
    except TimeoutError:return {'possible':None,'nodes':nodes}

def check(path):
    start=time.time();data=json.loads(path.read_text());assert data['status']=='excluded'
    L,*lengths=data['cycle_partition'];assert len(lengths)==2
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    rows,_,_=get_rows(messages,L+sum(lengths),L,lengths);labels=sorted(next(iter(rows.values())))
    for g in data['bad_groups']:
        r=feasible([rows[g['length']][b] for b in g['labels']],g['length'],g['minimum_alphabet']-1)
        assert r['status']=='unsat',g
    allocations=[];total=data['alphabet_bound']-data['top_cost']
    for a in range(max(0,total-lengths[1]),min(total,lengths[0])+1):
        b=total-a
        if lengths[0]==lengths[1] and a>b:continue
        r=colorable(labels,lengths,[a,b],L,rows,data['bad_groups'])
        allocations.append({'budgets':[a,b],**r})
        print(path.name,[a,b],r,flush=True)
        assert r['possible'] is False
    out={'certificate':path.name,'bad_groups_rechecked':len(data['bad_groups']),
         'alphabet_allocations':allocations,'passed':True,'seconds':time.time()-start}
    (ROOT/('checked_'+path.name)).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('certificate');args=ap.parse_args()
    out=check(ROOT/args.certificate);print('PASSED',out['seconds'])
