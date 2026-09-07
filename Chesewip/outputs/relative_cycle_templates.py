"""Exact relative-state relaxation for unit-neighbor anchored three-cycles.

Different plaintext choices produce a relative five-cycle or two disjoint
transpositions. We allow their conjugating deck to vary freely at each change,
so SAT is a relaxation, not an actual common-shuffle cipher key.
"""
from pathlib import Path
import sys,json,time,argparse,random
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3

def transform(x,pts,five):
    a,b,c,d,e=pts
    return z3.If(x==a,b,z3.If(x==b,z3.If(five,c,a),z3.If(x==c,d,
           z3.If(x==d,z3.If(five,e,c),z3.If(z3.And(five,x==e),a,x)))))

def permutation(points,five,n):
    a,b,c,d,e=points;out=list(range(n))
    if five:
        for x,y in zip(points,points[1:]+points[:1]):out[x]=y
    else:out[a]=b;out[b]=a;out[c]=d;out[d]=c
    return out

def solve(a,b,cuts,n=83,timeout=5000):
    start=time.time();width=(n-1).bit_length();bv=lambda x:z3.BitVecVal(x,width)
    solver=z3.SolverFor('QF_BV');solver.set(timeout=timeout)
    changes=[]
    for j in range(len(cuts)-1):
        pts=[z3.BitVec(f'x_{j}_{k}',width) for k in range(5)];five=z3.Bool(f'five_{j}')
        solver.add(*(z3.ULT(x,bv(n)) for x in pts))
        solver.add(z3.Distinct(*pts[:4]),z3.Implies(five,z3.Distinct(*pts)))
        solver.add(z3.ULT(pts[0],pts[1]),z3.ULT(pts[0],pts[2]))
        solver.add(z3.Implies(five,z3.And(z3.ULT(pts[0],pts[3]),z3.ULT(pts[0],pts[4]))))
        solver.add(z3.Implies(z3.Not(five),z3.And(z3.ULT(pts[2],pts[3]),pts[4]==bv(0))))
        changes.append((pts,five))
        lo,hi=cuts[j:j+2]
        for x,y in set(zip(a[lo:hi],b[lo:hi])):
            image=bv(x)
            for points,kind in reversed(changes):image=transform(image,points,kind)
            solver.add(image==bv(y))
        # Different plaintexts need different physical output source positions.
        image=bv(a[lo])
        for points,kind in reversed(changes[:-1]):image=transform(image,points,kind)
        solver.add(image!=bv(b[lo]))
    status=str(solver.check());out={'status':status,'cuts_zero_based':cuts,'seconds':time.time()-start}
    if status=='unknown':out['reason']=solver.reason_unknown()
    if status=='sat':
        m=solver.model();rel=list(range(n));witness=[]
        for j,(points,kind) in enumerate(changes):
            pts=[m.eval(x).as_long() for x in points];five=z3.is_true(m.eval(kind));delta=permutation(pts,five,n)
            assert rel[a[cuts[j]]]!=b[cuts[j]]
            rel=[rel[delta[x]] for x in range(n)]
            assert all(rel[x]==y for x,y in zip(a[cuts[j]:cuts[j+1]],b[cuts[j]:cuts[j+1]]))
            witness.append({'five_cycle':five,'points':pts,'relative_permutation':rel.copy()})
        out['witness']=witness
    return out

def control_cases():
    rng=random.Random(20261029);results=[]
    for n in [11,83]:
        for trial in range(4):
            cuts=[0,10,20,30];rel=list(range(n));a=[];b=[]
            for lo,hi in zip(cuts,cuts[1:]):
                pts=rng.sample(range(n),5);delta=permutation(pts,bool(rng.randrange(2)),n);previous=rel;rel=[rel[delta[x]] for x in range(n)]
                for t in range(lo,hi):
                    allowed=[x for x in range(n) if (t!=lo or previous[x]!=rel[x]) and (not a or (x!=a[-1] and rel[x]!=b[-1]))]
                    x=rng.choice(allowed);a.append(x);b.append(rel[x])
            r=solve(a,b,cuts,n,10000);assert r['status']=='sat',r;results.append({'n':n,'seconds':r['seconds']})
    return results

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--controls',action='store_true');ap.add_argument('--timeout',type=int,default=5000);args=ap.parse_args()
    if args.controls:
        out={'controls':control_cases()};name='relative_cycle_controls.json';print(out,flush=True)
    else:
        raw=list(json.loads((ROOT/'ciphertext.json').read_text()).values());a,b=[x[:50] for x in raw[:2]]
        templates=json.loads((ROOT/'checked_compact_templates.json').read_text())['possible_difference_positions_zero_based'];results=[]
        for cut in templates:
            r=solve(a,b,cut+[50],timeout=args.timeout);results.append(r);print({k:v for k,v in r.items() if k!='witness'},flush=True)
        out={'results':results,'warning':'SAT is only relative-state compatibility. UNSAT excludes exactly the specified change template under the unit-neighbor three-cycle model with a common initial deck.'};name='relative_cycle_templates.json'
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
