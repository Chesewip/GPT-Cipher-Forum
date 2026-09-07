import analyze as a
from collections import deque
m=a.msgs; off=[0]
for x in m: off.append(off[-1]+len(x))
e=a.equalities[-1]; edges=a.recurrence_edges(m)
mi,si,mj,sj,n=e
edges.extend((off[mi]+si+k,off[mj]+sj+k,0) for k in range(n))
adj={}
for u,v,d in edges:
    adj.setdefault(u,[]).append((v,d)); adj.setdefault(v,[]).append((u,-d))
start=off[7]+68; end=off[7]+71
q=deque([start]); prev={start:None}
while q:
    u=q.popleft()
    if u==end:break
    for v,d in adj.get(u,[]):
        if v not in prev: prev[v]=(u,d);q.append(v)
def loc(u):
    mi=max(i for i in range(9) if off[i]<=u)
    return (a.names[mi],u-off[mi])
path=[]; v=end
while prev[v]:
    u,d=prev[v];path.append([loc(u),loc(v),d]);v=u
print('CERTIFICATE',list(reversed(path)))
for n in range(1,34):
    ee=(*e[:4],n)
    r=a.analyze_graph(m,[ee])
    if r['contradiction']:print('SHORTEST PREFIX',n,r['contradiction']);break
