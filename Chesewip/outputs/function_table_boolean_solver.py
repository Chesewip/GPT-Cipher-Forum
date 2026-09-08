"""Explicit finite-table/one-hot encoding, independent of the UF/BV encoding.

This discovery solver uses Boolean choices for coordinates, code assignments,
and the 25-cell function table. Solver timeouts remain inconclusive.
"""
from pathlib import Path
import sys,json,time,itertools,hashlib
try:import z3
except ImportError:
    sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'work'/'pydeps'))
    import z3
from nonlinear_coordinate_closure import routed_triples,closure
ROOT=Path(__file__).resolve().parent
POINTS=list(itertools.product(range(5),repeat=3))

def solve(messages,axis,period,strip,reverse,timeout_ms,known_table=None):
    start=time.monotonic();rows=routed_triples(messages,period,period,strip,reverse)
    labels=sorted({v//3 for row in rows for v in row});_,uf=closure(rows,labels,axes=(axis,))
    roots=sorted({uf.root(v) for row in rows for v in row});reduced=set(tuple(uf.root(v) for v in row) for row in rows)
    xs={v:[z3.Bool('x_'+str(v)+'_'+str(d)) for d in range(5)] for v in roots}
    neg={v:[z3.Not(x) for x in values] for v,values in xs.items()}
    table=[[[z3.Bool('t_'+str(x)+'_'+str(y)+'_'+str(z)) for z in range(5)] for y in range(5)] for x in range(5)]
    key={label:[z3.Bool('k_'+str(label)+'_'+str(code)) for code in range(125)] for label in labels}
    s=z3.SolverFor('QF_FD');s.set(timeout=timeout_ms,random_seed=909100)
    for values in xs.values():s.add(z3.PbEq([(v,1) for v in values],1))
    for row in table:
        for values in row:s.add(z3.PbEq([(v,1) for v in values],1))
    if known_table is not None:
        for x,y in itertools.product(range(5),repeat=2):s.add(table[x][y][known_table[x][y]])
    else:
        # Common digit renaming is valid only when the table is unknown.
        seen=[z3.BoolVal(False) for _ in range(5)]
        for root in roots:
            for value in range(1,5):s.add(z3.Implies(xs[root][value],seen[value-1]))
            seen=[z3.Or(seen[value],xs[root][value]) for value in range(5)]
    clauses=[]
    for label in labels:
        s.add(z3.PbEq([(v,1) for v in key[label]],1))
        for code,point in enumerate(POINTS):
            clauses.extend(z3.Implies(key[label][code],xs[uf.root(3*label+d)][point[d]]) for d in range(3))
    for code in range(125):s.add(z3.PbLe([(key[label][code],1) for label in labels],1))
    other=[i for i in range(3) if i!=axis]
    for row in reduced:
        u,v,w=row[other[0]],row[other[1]],row[axis]
        for x,y,z in POINTS:clauses.append(z3.Or(neg[u][x],neg[v][y],neg[w][z],table[x][y][z]))
    s.add(*clauses);built=time.monotonic()
    print('Built Boolean model','known table' if known_table is not None else 'unknown table','seconds',round(built-start,2),flush=True)
    result=s.check();out=dict(status=str(result),axis=axis,period=period,first_block=period,strip_first=strip,reverse=reverse,
        timeout_ms=timeout_ms,known_table=known_table,encoding_seconds=built-start,solve_seconds=time.monotonic()-built,z3_version=z3.get_version_string())
    if result==z3.sat:
        m=s.model();partial={label:next(code for code in range(125) if z3.is_true(m.eval(key[label][code]))) for label in labels}
        available=iter(sorted(set(range(125))-set(partial.values())))
        output_key=[partial[label] if label in partial else next(available) for label in range(125)]
        f=[[next(z for z in range(5) if z3.is_true(m.eval(table[x][y][z]))) for y in range(5)] for x in range(5)]
        values={root:next(d for d in range(5) if z3.is_true(m.eval(xs[root][d]))) for root in roots}
        out.update(key=output_key,table=f,decoded=[sum(w*values[uf.root(v)] for w,v in zip([25,5,1],row)) for row in rows])
    elif result==z3.unknown:out['reason']=s.reason_unknown()
    return out

def main():
    controls=json.loads((ROOT/'one_coordinate_function_screen.json').read_text(encoding='utf-8'))['controls']
    data=(ROOT/'ciphertext.json').read_bytes();eyes=list(json.loads(data).values())
    out=dict(status='Boolean finite-table pilot; no decipherment.',ciphertext_sha256=hashlib.sha256(data).hexdigest(),runs=[])
    path=ROOT/'function_table_boolean_pilot.json'
    jobs=[('control_known',controls[0],True),('control_unknown',controls[0],False),('eyes',None,False),('control_known',controls[1],True)]
    for kind,c,known in jobs:
        r=solve(c['ciphertext'] if c else eyes,c['axis'] if c else 1,c['period'] if c else 2,False,False,20000,c['table'] if known else None)
        r['kind']=kind;r['control_seed']=c['seed'] if c else None;out['runs'].append(r)
        path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
        print(kind,r['status'],'solver seconds',round(r['solve_seconds'],2),flush=True)

if __name__=='__main__':main()
