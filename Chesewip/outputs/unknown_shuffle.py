"""Exact SMT model: swap selected bottom card to top, then shuffle bottom.

Unknown shared initial deck, unknown shared permutation, alphabet bounded by A.
Install z3-solver to use. All emitted candidates are replayed before acceptance.
"""
from pathlib import Path
import argparse, json, random, sys, time

ROOT = Path(__file__).resolve().parent
LOCAL_DEPS = ROOT.parent / 'work' / 'pydeps'
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))
import z3

def encrypt(plaintext, permutation, initial):
    deck = initial[:]
    out = []
    for p in plaintext:
        deck[0], deck[p+1] = deck[p+1], deck[0]
        out.append(deck[0])
        new = [None] * len(permutation)
        for i, j in enumerate(permutation):
            new[j] = deck[i+1]
        deck[1:] = new
    return out

def decrypt(ciphertext, permutation, initial):
    deck = initial[:]
    out = []
    for c in ciphertext:
        p = deck.index(c)-1
        if p < 0:
            raise ValueError('output equals current top')
        out.append(p)
        deck[0], deck[p+1] = deck[p+1], deck[0]
        new = [None] * len(permutation)
        for i, j in enumerate(permutation):
            new[j] = deck[i+1]
        deck[1:] = new
    return out

def canon(seq):
    ids = {}
    return [ids.setdefault(x, len(ids)) for x in seq]

def solve(messages, n, alphabet, timeout_ms=30000, equalities=(),
          fixed=None, symmetry=True, gauge=False):
    start = time.time()
    solver = z3.Solver()
    solver.set(timeout=timeout_ms)
    P = z3.Function('P', z3.IntSort(), z3.IntSort())
    pv = [P(i) for i in range(n-1)]
    solver.add(z3.Distinct(pv))
    solver.add(*[z3.And(v >= 0, v < n-1) for v in pv])
    initial_top = z3.Int('initial_top')
    solver.add(initial_top >= 0, initial_top < n)
    y = [z3.Int('initial_position_' + str(i)) for i in range(n)]
    solver.add(z3.Distinct(y))
    for i, v in enumerate(y):
        solver.add(v >= -1, v < n-1, (v == -1) == (initial_top == i))
        if gauge:
            solver.add(v == z3.If(i < initial_top, i,
                                 z3.If(i == initial_top, -1, i-1)))
    ps = [[z3.Int('p_%d_%d' % (mi,t)) for t in range(len(m))]
          for mi,m in enumerate(messages)]
    flat = sum(ps, [])
    solver.add(*[z3.And(p >= 0, p < (n-1 if gauge else alphabet)) for p in flat])
    if gauge:
        used = z3.Function('used', z3.IntSort(), z3.BoolSort())
        solver.add(z3.AtMost(*[used(i) for i in range(n-1)], alphabet))
        solver.add(*[used(p) for p in flat])
    if symmetry and fixed is None and not gauge:
        # Relabeling bottom positions conjugates P and changes neither outputs
        # nor plaintext equality patterns. Canonical first-use names remove it.
        solver.add(flat[0] == 0)
        maximum = flat[0]
        for k,p in enumerate(flat[1:], 1):
            solver.add(p <= maximum + 1)
            nxt = z3.Int('max_' + str(k))
            solver.add(nxt == z3.If(p > maximum, p, maximum))
            maximum = nxt
    def power(v, d):
        for _ in range(d):
            v = P(v)
        return v
    for mi, ct in enumerate(messages):
        last = {}
        for t,c in enumerate(ct):
            if c in last:
                r = last[c]
                if t == r+1:
                    solver.add(False)
                else:
                    solver.add(ps[mi][t] == power(ps[mi][r+1], t-r-1))
            elif t == 0:
                solver.add(ps[mi][t] == y[c])
            else:
                # An initially-top card is displaced by the first selection.
                v = z3.If(initial_top == c, ps[mi][0], y[c])
                solver.add(ps[mi][t] == power(v, t))
            last[c] = t
    for mi,si,mj,sj,length in equalities:
        for k in range(length):
            solver.add(ps[mi][si+k] == ps[mj][sj+k])
    if fixed is not None:
        perm, initial = fixed
        if gauge:
            canonical_initial = [initial[0]] + sorted(initial[1:])
            rename = [canonical_initial.index(c)-1 for c in initial[1:]]
            canonical_perm = [None]*(n-1)
            for i,j in enumerate(perm):
                canonical_perm[rename[i]] = rename[j]
            initial,perm = canonical_initial,canonical_perm
        for i,v in enumerate(perm):
            solver.add(P(i) == v)
        for pos,c in enumerate(initial):
            solver.add(y[c] == pos-1)
    build_time = time.time()-start
    answer = solver.check()
    result = dict(status=str(answer), alphabet_bound=alphabet, deck_size=n,
                  symbols=sum(map(len,messages)), build_seconds=build_time,
                  total_seconds=time.time()-start,
                  sorted_bottom_gauge=gauge,
                  plaintext_equality_assumptions=list(equalities))
    if answer == z3.unknown:
        result['reason'] = solver.reason_unknown()
    if answer == z3.sat:
        model = solver.model()
        perm = [model.eval(v).as_long() for v in pv]
        initial = [None]*n
        for c,v in enumerate(y):
            initial[model.eval(v).as_long()+1] = c
        plain = [decrypt(ct,perm,initial) for ct in messages]
        assert len(set(sum(plain,[]))) <= alphabet
        if not gauge:
            assert max(sum(plain,[])) < alphabet
        assert all(encrypt(pt,perm,initial)==ct for pt,ct in zip(plain,messages))
        assert all([model.eval(p).as_long() for p in row]==pt
                   for row,pt in zip(ps,plain))
        result.update(permutation=perm, initial_deck=initial,
                      plaintext_selections=plain, exact_replay=True)
    return result

def synthetic(n, a, length, count, seed):
    rng=random.Random(seed)
    permutation=list(range(n-1)); rng.shuffle(permutation)
    initial=list(range(n)); rng.shuffle(initial)
    plain=[[rng.randrange(a) for _ in range(length)] for _ in range(count)]
    return [encrypt(pt,permutation,initial) for pt in plain],plain,permutation,initial

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--case', choices=['small','large','eyes'],default='small')
    ap.add_argument('--alphabet',type=int,default=27)
    ap.add_argument('--timeout',type=int,default=30)
    ap.add_argument('--fixed',action='store_true')
    ap.add_argument('--isomorphs',action='store_true')
    ap.add_argument('--no-symmetry',action='store_true')
    ap.add_argument('--gauge',action='store_true')
    args=ap.parse_args()
    eq=[]; fixed=None; plain=None
    if args.case=='eyes':
        msgs=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
        n=83; a=args.alphabet
        if args.isomorphs:
            runs=[(1,34,1,64,26),(2,39,2,74,24),(0,40,0,68,10),
                  (1,40,2,45,11),(1,40,2,80,11),(3,18,4,24,14),
                  (3,18,5,23,14),(6,51,7,53,12),(6,51,8,52,12),
                  (6,68,7,71,33)]
            eq=[(i,s+1,j,t+1,k-1) for i,s,j,t,k in runs]
    else:
        n,a,length,count=(11,4,40,4) if args.case=='small' else (83,27,120,9)
        msgs,plain,perm,initial=synthetic(n,a,length,count,20260907)
        if args.fixed: fixed=(perm,initial)
    result=solve(msgs,n,a,args.timeout*1000,eq,fixed,not args.no_symmetry,args.gauge)
    if plain is not None and result['status']=='sat':
        result['planted_plaintext_pattern_recovered']=canon(sum(plain,[]))==canon(sum(result['plaintext_selections'],[]))
    name='smt_'+args.case+('_fixed' if args.fixed else '')+('_gauge' if args.gauge else '')+('_isomorphs' if args.isomorphs else '')+'_'+str(a)+'.json'
    (ROOT/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['permutation','initial_deck','plaintext_selections']},indent=2),flush=True)

if __name__=='__main__': main()
