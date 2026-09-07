"""SMT attack after exact progressive reduction, with a fixed trial top label."""
from pathlib import Path
import sys,json,random,time,argparse,math
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'work/pydeps'))
import z3
from progressive_reduction import deswap

def encrypt(pt,q,top):
    deck=list(range(len(q)));ct=[]
    for p in pt:
        deck[top],deck[p]=deck[p],deck[top]
        ct.append(deck[top]);new=[None]*len(q)
        for i,j in enumerate(q):new[j]=deck[i]
        deck=new
    return ct

def solve(messages,n,top,A,timeout=30):
    start=time.time();bits=(n-1).bit_length()
    B=z3.BitVecSort(bits)
    val=lambda i:z3.BitVecVal(i,bits)
    solver=z3.Solver();solver.set(timeout=int(timeout*1000))
    levels=max(map(len,messages)).bit_length()
    powers=[z3.Array('Q_power_'+str(k),B,B) for k in range(levels)]
    q=[z3.Select(powers[0],val(i)) for i in range(n)]
    solver.add(z3.Distinct(q),q[top]==val(top))
    solver.add(*[z3.ULT(x,val(n)) for x in q])
    for k in range(1,levels):
        for i in range(n):
            v=z3.Select(powers[k-1],val(i))
            solver.add(z3.Select(powers[k],val(i))==z3.Select(powers[k-1],v))
    used=z3.Array('used',B,z3.BoolSort())
    solver.add(z3.AtMost(*[z3.Select(used,val(i)) for i in range(n)],A))
    solver.add(z3.Not(z3.Select(used,val(top))))
    ps=[]
    for m in messages:
        row=[]
        for t,b in enumerate(deswap(m,top,n)):
            x=val(b)
            for k in range(levels):
                if (t>>k)&1:x=z3.Select(powers[k],x)
            solver.add(z3.Select(used,x));row.append(x)
        ps.append(row)
    answer=solver.check()
    result=dict(status=str(answer),seconds=time.time()-start,top=top,n=n,alphabet=A)
    if answer==z3.unknown:result['reason']=solver.reason_unknown()
    if answer==z3.sat:
        model=solver.model();perm=[model.eval(x).as_long() for x in q]
        plain=[[model.eval(x).as_long() for x in row] for row in ps]
        assert all(encrypt(pt,perm,top)==ct for pt,ct in zip(plain,messages))
        assert len(set(sum(plain,[])))<=A
        result.update(permutation=perm,plaintext=plain,exact_replay=True)
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--timeout',type=int,default=40)
    ap.add_argument('--large',action='store_true');args=ap.parse_args()
    n,A,length,count=(83,27,120,9) if args.large else (11,4,40,4)
    rng=random.Random(20260907);top=rng.randrange(n)
    bottom=[i for i in range(n) if i!=top];shuffled=bottom[:];rng.shuffle(shuffled)
    q=list(range(n))
    for i,j in zip(bottom,shuffled):q[i]=j
    letters=rng.sample(bottom,A)
    pts=[[rng.choice(letters) for _ in range(length)] for _ in range(count)]
    cts=[encrypt(pt,q,top) for pt in pts]
    r=solve(cts,n,top,A,args.timeout)
    if r['status']=='sat':
        def canon(x):
            ids={};return [ids.setdefault(v,len(ids)) for v in x]
        r['planted_plaintext_pattern_recovered']=canon(sum(pts,[]))==canon(sum(r['plaintext'],[]))
        r['planted_permutation_recovered']=r['permutation']==q
    (ROOT/('reduced_smt_'+str(n)+'.json')).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps({k:v for k,v in r.items() if k not in ['permutation','plaintext']},indent=2))
