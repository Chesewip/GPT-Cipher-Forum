"""Show each edge is necessary in this isolated six-edge affine certificate."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
cert=json.loads((ROOT/'checked_affine_six_edge_certificate.json').read_text());edges=cert['edges'];labels=sorted({e[k] for e in edges for k in ['source_label','target_label']});out=[]
for removed in range(6):
 found=None
 for slope in [1,2,3]:
  s=z3.Solver();s.set(timeout=5000);x={c:z3.Int('x_'+str(c)) for c in labels};u=z3.Int('offset_A');v=z3.Int('offset_B');s.add(z3.Distinct(*x.values()),x[47]==0,x[54]==1)
  for value in list(x.values())+[u,v]:s.add(value>=0,value<83)
  for i,e in enumerate(edges):
   if i==removed:continue
   a=1 if e['context']=='A' else slope;b=u if e['context']=='A' else v;s.add(x[e['target_label']]==(a*x[e['source_label']]+b)%83)
  status=str(s.check())
  if status=='sat':
   model=s.model();coords={c:model.eval(t).as_long() for c,t in x.items()};parameters={'A':[1,model.eval(u).as_long()],'B':[slope,model.eval(v).as_long()]};assert len(set(coords.values()))==len(labels)
   matched=[]
   for e in edges:
    a,b=parameters[e['context']];matched.append(coords[e['target_label']]==(a*coords[e['source_label']]+b)%83)
   assert sum(matched)==5 and not matched[removed]
   found=dict(removed_edge=removed,coordinates=coords,parameters=parameters,matched_edges=matched);break
 assert found is not None,removed
 out.append(found)
(ROOT/'affine_six_edge_minimality.json').write_text(json.dumps(dict(status='each_single_edge_deletion_has_an_affine_embedding',witnesses=out,scope='Minimality of these six isolated mapping constraints only. The remaining full passage constraints may still exclude affine embeddings.'),indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Verified affine completions for all six single-edge deletions.',flush=True)
