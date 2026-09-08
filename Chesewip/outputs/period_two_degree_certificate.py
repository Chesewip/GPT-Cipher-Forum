"""Universal period-2 function-codebook exclusion from observed graph degrees.

For the middle-coordinate function y=F(x,z), every full output-state outdegree
or indegree is 5*m. Each table row/column output multiplicity m occurs in five
states. Thus sum_k ceil(H_k/5) <= 25, H_k=#observed degrees >5*(k-1).
"""
from pathlib import Path
from collections import defaultdict
import itertools,json,hashlib
from one_coordinate_function_screen import function_control
ROOT=Path(__file__).resolve().parent

def graph(messages,strip,reverse,first):
    succ=defaultdict(set);pred=defaultdict(set);labels=set()
    for raw in messages:
        seq=raw[int(strip):]
        if reverse:seq=seq[::-1]
        labels.update(seq)
        for i in range(int(first==1),len(seq)-1,2):
            succ[seq[i]].add(seq[i+1]);pred[seq[i+1]].add(seq[i])
    return labels,succ,pred

def summarize(labels,adj):
    degrees={label:len(adj[label]) for label in sorted(labels)}
    tails=[sum(d>5*k for d in degrees.values()) for k in range(5)]
    return dict(degrees=degrees,tail_counts=tails,required_table_entries=sum((h+4)//5 for h in tails))

def main():
    data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values())
    out=dict(status='Exact period-2 exclusion for any one-coordinate function; cipher unsolved.',
        ciphertext_sha256=hashlib.sha256(data).hexdigest(),coordinate_values=5,table_entries=25,cases=[],controls=[])
    for strip,reverse,first in itertools.product([False,True],[False,True],[1,2]):
        labels,succ,pred=graph(messages,strip,reverse,first)
        outs=summarize(labels,succ);ins=summarize(labels,pred)
        direction='outgoing' if outs['required_table_entries']>25 else 'incoming'
        selected=outs if direction=='outgoing' else ins
        assert selected['required_table_entries']>25
        assert max(ins['degrees'].values())>5 and max(outs['degrees'].values())>5
        out['cases'].append(dict(strip_first=strip,reverse=reverse,first_block=first,
            outgoing=outs,incoming=ins,middle_axis_certificate_direction=direction,
            outer_axis0_in_degree_witness=max(ins['degrees'],key=ins['degrees'].get),
            outer_axis2_out_degree_witness=max(outs['degrees'],key=outs['degrees'].get)))
    for seed in [909120,909121,909122]:
        c=function_control(seed,1,2);labels,succ,pred=graph(c['ciphertext'],False,False,2)
        c['outgoing']=summarize(labels,succ);c['incoming']=summarize(labels,pred)
        assert c['outgoing']['required_table_entries']<=25 and c['incoming']['required_table_entries']<=25
        out['controls'].append(c)
    (ROOT/'period_two_degree_certificate.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('All 8 boundary/read views require 26 entries in a 25-entry table; all 3 determined axes excluded. Controls pass.')

if __name__=='__main__':main()
