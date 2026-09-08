"""Finite-domain solver for an unknown one-coordinate function and output map.

Timeouts are inconclusive. Satisfiable models require independent replay and
are not plaintext authentication. Z3 is optional via the historical work path.
"""
from pathlib import Path
import sys,json,time,hashlib,argparse
try:import z3
except ImportError:
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'work'/'pydeps'))
    import z3
from nonlinear_coordinate_closure import routed_triples,closure
ROOT=Path(__file__).resolve().parent

def solve(messages,axis,period,first,strip,reverse,timeout_ms,seed):
    start=time.monotonic();triples=routed_triples(messages,period,first,strip,reverse)
    labels=sorted({v//3 for row in triples for v in row});_,uf=closure(triples,labels,axes=(axis,))
    roots=sorted({uf.root(v) for row in triples for v in row})
    xs={v:z3.BitVec('v'+str(v),3) for v in roots};f=z3.Function('F',z3.BitVecSort(3),z3.BitVecSort(3),z3.BitVecSort(3))
    solver=z3.Solver();solver.set(timeout=timeout_ms,random_seed=seed)
    for x in xs.values():solver.add(z3.ULE(x,4))
    for x in range(5):
        for y in range(5):solver.add(z3.ULE(f(x,y),4))
    solver.add(z3.Distinct(*[z3.Concat(*(xs[uf.root(3*label+d)] for d in range(3))) for label in labels]))
    other=[i for i in range(3) if i!=axis]
    for row in set(tuple(uf.root(v) for v in row) for row in triples):solver.add(f(xs[row[other[0]]],xs[row[other[1]]])==xs[row[axis]])
    # A common permutation of all five digit names is a true symmetry.
    # Value precedence chooses names in order of first appearance.
    solver.add(xs[roots[0]]==0);maximum=xs[roots[0]]
    for root in roots[1:]:
        solver.add(z3.ULE(xs[root],maximum+1))
        maximum=z3.If(z3.UGE(maximum,xs[root]),maximum,xs[root])
    result=solver.check();out=dict(axis=axis,period=period,first_block=first,strip_first=strip,reverse=reverse,
        timeout_ms=timeout_ms,seed=seed,coordinate_classes=len(roots),status=str(result),seconds=time.monotonic()-start,
        z3_version=z3.get_version_string())
    if result==z3.sat:
        model=solver.model();values={v:model.eval(x,model_completion=True).as_long() for v,x in xs.items()}
        partial={label:sum(w*values[uf.root(3*label+d)] for d,w in enumerate([25,5,1])) for label in labels}
        available=iter(sorted(set(range(125))-set(partial.values())))
        key=[partial[label] if label in partial else next(available) for label in range(125)]
        out.update(key=key,table=[[model.eval(f(x,y),model_completion=True).as_long() for y in range(5)] for x in range(5)],
                   decoded=[sum(w*values[uf.root(v)] for w,v in zip([25,5,1],row)) for row in triples])
    elif result==z3.unknown:out['reason']=solver.reason_unknown()
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--timeout-ms',type=int,default=5000);args=ap.parse_args()
    raw_bytes=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(raw_bytes).values())
    out=dict(status='Finite-domain pilot; no decipherment.',ciphertext_sha256=hashlib.sha256(raw_bytes).hexdigest(),real=[],controls=[])
    path=ROOT/'function_table_solver_pilot.json'
    def save():path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    for strip,reverse in [(False,False),(True,False),(False,True),(True,True)]:
        r=solve(messages,1,2,2,strip,reverse,args.timeout_ms,909000);out['real'].append(r);save()
        print('Eyes',strip,reverse,r['status'],round(r['seconds'],2),flush=True)
    control_data=json.loads((ROOT/'one_coordinate_function_screen.json').read_text(encoding='utf-8'))
    for c in control_data['controls']:
        r=solve(c['ciphertext'],c['axis'],c['period'],c['period'],False,False,args.timeout_ms,909010+c['axis'])
        r['control_seed']=c['seed'];out['controls'].append(r);save()
        print('Control',c['seed'],r['status'],round(r['seconds'],2),flush=True)

if __name__=='__main__':main()
