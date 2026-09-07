from pathlib import Path
import json,time,argparse,collections
from integer_return_paths import solve
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
from return_displacement import graph
ROOT=Path(__file__).resolve().parent

def components(pts,edges):
    parent={x:x for pt in pts for x in pt}
    def root(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    used=set()
    for _,_,_,mi,r,t in edges:
        vs=pts[mi][r+1:t+1];used.update(vs)
        for v in vs:parent[root(v)]=root(vs[0])
    groups={}
    for edge in edges:groups.setdefault(root(edge[0]),[]).append(edge)
    return sorted(groups.values(),key=lambda es:len({x for _,_,_,mi,r,t in es for x in pts[mi][r+1:t+1]}),reverse=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--gap',type=int,default=12);ap.add_argument('--rotation',type=int,default=9);ap.add_argument('--timeout',type=int,default=3000);ap.add_argument('--eliminate-free',action='store_true');args=ap.parse_args()
    ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(ct);pts=make_plaintexts(ct,eq);es=[e for e in graph(ct,pts) if e[2]<=args.gap];groups=components(pts,es);results=[];start=time.time()
    for k,edges in enumerate(groups):
        r=solve(ct,pts,args.rotation,gap_limit=args.gap,timeout=args.timeout,edge_subset=edges,eliminate_free=args.eliminate_free);r['component_index']=k;results.append(r)
        print({k:v for k,v in r.items() if k!='selector_assignment'},flush=True)
    out={'eliminated_free_selectors':args.eliminate_free,'gap':args.gap,'rotation':args.rotation,'components':results,'seconds':time.time()-start,'assumed_equalities':eq,
         'combined_status':'unsat' if any(r['status']=='unsat' for r in results) else 'sat' if all(r['status']=='sat' for r in results) else 'unknown',
         'warning':'Only selected return paths. No initial-key consistency or alphabet bound.'}
    (ROOT/(f'component_returns_{args.gap}_{args.rotation}'+('_free' if args.eliminate_free else '')+'.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('combined',out['combined_status'],'seconds',out['seconds'])
