"""Expose small arithmetic witnesses and disjoint-core pigeonhole proofs."""
from pathlib import Path
import json,math,itertools
ROOT=Path(__file__).resolve().parent

def arithmetic(group,edges,max_length):
    vertices=set(group);adj={v:[] for v in group}
    for u,v,d in edges:
        if u in vertices and v in vertices:adj[u].append((v,d));adj[v].append((u,-d))
    pot={};components=[]
    for root in group:
        if root in pot:continue
        pot[root]=0;stack=[root];members=[];g=0
        while stack:
            u=stack.pop();members.append(u)
            for v,d in adj[u]:
                if v not in pot:pot[v]=pot[u]+d;stack.append(v)
                else:g=math.gcd(g,pot[u]+d-pot[v])
        candidates=[M for M in range(len(members),max_length+1) if not g or g%M==0]
        failures=[]
        for M in candidates:
            pair=next(((a,b) for a,b in itertools.combinations(members,2) if (pot[a]-pot[b])%M==0),None)
            if pair is None:break
            failures.append({'cycle_length':M,'colliding_distinct_labels':pair})
        else:
            return {'labels':members,'offsets':{v:pot[v] for v in members},'cycle_length_must_divide':abs(g),
                    'candidate_cycle_lengths':candidates,'collisions':failures,
                    'induced_edges':[(u,v,d) for u,v,d in edges if u in members and v in members]}
    raise AssertionError('No arithmetic contradiction')

def main():
    saved=json.loads((ROOT/'trimmed_isomorph_3.json').read_text());out=[]
    for result in saved:
        if 'bad_groups' not in result:continue
        groups=result['bad_groups'];L=result['top_cycle']
        masks=[sum(1<<v for v in g) for g in groups];packing=[]
        for k in range(len(groups),0,-1):
            found=False
            for ids in itertools.combinations(range(len(groups)),k):
                seen=0
                for i in ids:
                    if seen&masks[i]:break
                    seen|=masks[i]
                else:packing=list(ids);found=True;break
            if found:break
        item={'top_cycle':L,'maximum_disjoint_core_count':len(packing),'disjoint_core_indices':packing,
              'pigeonhole_exclusion':len(packing)>L,
              'arithmetic_core_certificates':[arithmetic(g,result['edges'],83-L) for g in groups]}
        out.append(item);print('L',L,'disjoint contradictory cores',len(packing),'only',L,'possible exceptional labels')
    (ROOT/'conditional_arithmetic_certificates.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
