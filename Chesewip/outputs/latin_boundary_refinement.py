"""Refine closure survivors using conditional equality and a six-clique.

An edge proves that two formal coordinate variables must take different
values. Six pairwise adjacent variables cannot use only five digits.
"""
from pathlib import Path
from collections import Counter
import json,itertools,time,hashlib
from nonlinear_coordinate_closure import routed_triples,closure
from latin_dependency_screen import pack_proof
ROOT=Path(__file__).resolve().parent

def clique(adj,size=6):
    def visit(chosen,candidates):
        if len(chosen)==size:return chosen
        if candidates.bit_count()<size-len(chosen):return None
        while candidates:
            bit=candidates&-candidates;candidates-=bit;v=bit.bit_length()-1
            result=visit(chosen+[v],candidates&adj[v])
            if result is not None:return result
        return None
    return visit([], (1<<len(adj))-1)

def main():
    started=time.monotonic();raw_bytes=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(raw_bytes).values())
    parent_bytes=(ROOT/'latin_dependency_boundaries.json').read_bytes();parent=json.loads(parent_bytes)
    out=dict(status='Conditional-equality graph refinement; no decipherment.',
             ciphertext_sha256=hashlib.sha256(raw_bytes).hexdigest(),parent_sha256=hashlib.sha256(parent_bytes).hexdigest(),cases=[])
    for case in parent['cases']:
        if case['status']!='closure_survives':continue
        triples=routed_triples(messages,case['period'],case['first_block'],case['strip_first'],case['reverse'])
        labels=sorted(set(v//3 for row in triples for v in row));_,uf=closure(triples,labels)
        freq=Counter(uf.root(v) for row in triples for v in row)
        variables=sorted(freq,key=lambda v:(-freq[v],v));adj=[0]*len(variables);tests=0;edges=[];found=None
        for i,var in enumerate(variables):
            for j in range(i):
                result,_=closure(triples,labels,assumptions=[(var,variables[j])]);tests+=1
                if result['status']=='forced_output_collision':
                    adj[i]|=1<<j;adj[j]|=1<<i;edges.append([j,i])
            if (i+1)%10==0 or i==len(variables)-1:
                found=clique(adj)
                print('Case',case['period'],case['first_block'],case['strip_first'],case['reverse'],'variables',i+1,'tests',tests,'edges',len(edges),'clique',found,flush=True)
                if found is not None:break
        r={k:case[k] for k in ['strip_first','reverse','period','first_block']}
        r.update(coordinate_variables=variables,inequality_edges=edges,conditional_pairs_tested=tests)
        if found is not None:
            selected=[variables[i] for i in found];branches=[]
            for a,b in itertools.combinations(selected,2):
                proof,_=closure(triples,labels,assumptions=[(a,b)])
                assert proof['status']=='forced_output_collision';proof['assumption']=[a,b]
                branches.append(pack_proof(proof))
            r.update(status='six_pairwise_distinct_coordinate_values',variables=selected,branches=branches)
        else:r['status']='no_six_clique_found'
        out['cases'].append(r)
        (ROOT/'latin_boundary_refinement.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    out['seconds']=time.monotonic()-started
    (ROOT/'latin_boundary_refinement.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
