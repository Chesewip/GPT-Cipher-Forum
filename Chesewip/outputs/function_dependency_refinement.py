"""Pigeonhole refinement of unresolved single-coordinate function settings."""
from pathlib import Path
from collections import Counter
import json,itertools,time,hashlib,argparse
from nonlinear_coordinate_closure import routed_triples,closure
from latin_dependency_screen import pack_proof
from latin_boundary_refinement import clique
ROOT=Path(__file__).resolve().parent

def refine(messages,axis,period,strip,reverse,max_variables):
    triples=routed_triples(messages,period,period,strip,reverse)
    labels=sorted({v//3 for row in triples for v in row});_,uf=closure(triples,labels,axes=(axis,))
    freq=Counter(uf.root(v) for row in triples for v in row)
    variables=sorted(freq,key=lambda v:(-freq[v],v))[:max_variables]
    adj=[0]*len(variables);edges=[];tests=0;found=None
    for i,var in enumerate(variables):
        for j in range(i):
            result,_=closure(triples,labels,axes=(axis,),assumptions=[(var,variables[j])]);tests+=1
            if result['status']=='forced_output_collision':
                adj[i]|=1<<j;adj[j]|=1<<i;edges.append([j,i])
        if i>=5:
            found=clique(adj)
            if found is not None:break
    out=dict(axis=axis,period=period,first_block=period,strip_first=strip,reverse=reverse,
        coordinate_variables=variables,inequality_edges=edges,conditional_pairs_tested=tests)
    if found is None:out['status']='no_six_clique_found'
    else:
        selected=[variables[i] for i in found];branches=[]
        for a,b in itertools.combinations(selected,2):
            proof,_=closure(triples,labels,axes=(axis,),assumptions=[(a,b)])
            assert proof['status']=='forced_output_collision';proof['assumption']=[a,b]
            branches.append(pack_proof(proof))
        out.update(status='six_pairwise_distinct_coordinate_values',variables=selected,branches=branches)
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--max-variables',type=int,default=16);args=ap.parse_args()
    started=time.monotonic();data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values())
    source_bytes=(ROOT/'one_coordinate_function_screen.json').read_bytes();source=json.loads(source_bytes)
    out=dict(status='Bounded inequality-graph refinement, not a decipherment.',max_variables=args.max_variables,
             ciphertext_sha256=hashlib.sha256(data).hexdigest(),source_sha256=hashlib.sha256(source_bytes).hexdigest(),cases=[],controls=[])
    path=ROOT/('function_dependency_refinement_'+str(args.max_variables)+'.json')
    def save():path.write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    for c in source['cases']:
        if c['status']!='closure_survives':continue
        r=refine(messages,c['axis'],c['period'],c['strip_first'],c['reverse'],args.max_variables)
        out['cases'].append(r)
        if len(out['cases'])%10==0:
            save();print('Processed',len(out['cases']),'new exclusions',sum(r['status']=='six_pairwise_distinct_coordinate_values' for r in out['cases']),flush=True)
    for c in source['controls']:
        r=refine(c['ciphertext'],c['axis'],c['period'],False,False,args.max_variables)
        assert r['status']=='no_six_clique_found';r['control_seed']=c['seed'];out['controls'].append(r)
    out['seconds']=time.monotonic()-started;save()

if __name__=='__main__':main()
