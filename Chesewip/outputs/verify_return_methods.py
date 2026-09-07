"""Independent physical checks of return constraints and support contraction."""
from pathlib import Path
import json,random
from integer_return_paths import solve
from component_return_paths import components
from return_displacement import graph
from clocked_three_cycle_scan import encrypt_physical
from shared_update_support import scan,scan_blocks
ROOT=Path(__file__).resolve().parent
rng=random.Random(20261103);pinned=[];unknown=[];support_controls=[]
for n in [7,19,83]:
    for trial in range(4):
        rotation=rng.randrange(n-1);key=rng.sample(list(range(n)),n)
        shared=[rng.randrange(1,n) for _ in range(14)]
        pts=[[rng.randrange(1,n) for _ in range(8)]+shared+[rng.randrange(1,n) for _ in range(10)] for j in range(3)]
        classes=[[('shared',t-8) if 8<=t<22 else (j,t) for t in range(len(pt))] for j,pt in enumerate(pts)]
        ct=[encrypt_physical(pt,key,1,rotation) for pt in pts]
        r=solve(ct,classes,rotation,n,gap_limit=10000,timeout=10000,pinned=pts);assert r['status']=='sat';pinned.append({'n':n,'rotation':rotation,'seconds':r['seconds']})
        edges=[e for e in graph(ct,classes) if e[2]<=6]
        for group in components(classes,edges):
            r=solve(ct,classes,rotation,n,gap_limit=6,timeout=5000,edge_subset=group,eliminate_free=True);assert r['status']=='sat';unknown.append({'n':n,'variables':r['variables'],'eliminated':r['eliminated_free_selectors']})
        results=scan(ct,classes,n);assert all(r['status']=='bound' and r['ratio']<=5 for r in results);support_controls.append({'n':n,'alignments':len(results)})

# Explicitly track each returning card in a physical deck of positions.
physical_checks=0
for n in [7,19,83]:
    for trial in range(30):
        rotation=rng.randrange(n-1);key=rng.sample(list(range(n)),n);pt=[rng.randrange(1,n) for _ in range(80)]
        ct=encrypt_physical(pt,key,1,rotation);last={}
        for t,c in enumerate(ct):
            if c in last:
                r=last[c];deck=list(range(n));tracked=deck[0]
                for s in range(r+1,t+1):
                    p=pt[s];neighbor=1+p%(n-1);old=deck[0];chosen=deck[p];tail=deck[neighbor]
                    deck[0]=chosen;deck[p]=tail;deck[neighbor]=old
                    assert (deck[0]==tracked)==(s==t)
                    if rotation:deck=[deck[0]]+deck[-rotation:]+deck[1:-rotation]
                gap=t-r;assert (1+(gap-1)*rotation-(pt[t]-pt[r+1]))%(n-1)<=gap-2;physical_checks+=1
            last[c]=t

# Independent row DP for all contracted windows on random partial permutations.
window_checks=0
for trial in range(80):
    n=7;bs=[]
    for k in range(6):
        perm=rng.sample(list(range(n)),n);rows=rng.sample(list(range(n)),rng.randrange(1,n))
        bs.append({'lo':k,'hi':k+1,'mapping':{x:perm[x] for x in rows}})
    fast=scan_blocks(bs,n)['ratio'];best=0
    for start in range(5):
        for end in range(start+1,6):
            total=0
            for x in range(n):
                costs=[0]*n
                for b in bs[start:end+1]:
                    f=b['mapping'];allowed={f[x]} if x in f else set(range(n))-set(f.values());low=min(costs)+1
                    costs=[min(costs[y],low) if y in allowed else 100000 for y in range(n)]
                total+=min(costs)
            best=max(best,total/(end-start));window_checks+=1
    assert fast==best
out={'pinned_full_return_controls':pinned,'unpinned_component_controls':len(unknown),'free_selectors_eliminated_in_controls':sum(r['eliminated'] for r in unknown),'independent_physical_card_return_checks':physical_checks,'shared_passage_support_controls':support_controls,'independent_contracted_window_checks':window_checks,'status':'All checks passed.'}
(ROOT/'checked_return_methods.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(out)
