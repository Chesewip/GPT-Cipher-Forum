import contextlib,io
with contextlib.redirect_stdout(io.StringIO()):
    import analyze as a
import json
shifted=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in a.equalities]
print(json.dumps(a.analyze_graph(a.msgs,shifted),indent=2))
for k,e in enumerate(shifted):
    r=a.analyze_graph(a.msgs,[e])
    if r['contradiction']:print(k,r)
