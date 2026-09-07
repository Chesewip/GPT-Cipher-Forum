import json,itertools
r=json.load(open('outputs/affine_strong_contexts_trim3.json'));g={i+1:dict(m) for i,m in enumerate(r['observed_maps'])};g.update({-i:{v:k for k,v in m.items()} for i,m in list(g.items())});level=[((k,),m) for k,m in g.items()];seen=set();rel=[]
for depth in range(1,9):
 nxt=[]
 for w,d in level:
  fixed=[x for x,y in d.items() if x==y]
  if len(fixed)>=2:rel.append((w,fixed))
  for k,m in g.items():
   if k==-w[-1]:continue
   nd={x:m[y] for x,y in d.items() if y in m}
   if len(nd)<2:continue
   sig=(tuple(sorted(nd.items())),k)
   if sig in seen:continue
   seen.add(sig);nxt.append((w+(k,),nd))
 print(depth,len(level),'relations',len(rel))
 level=nxt
print(rel[:20])
