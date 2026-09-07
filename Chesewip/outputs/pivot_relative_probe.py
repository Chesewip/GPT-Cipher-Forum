"""Necessary relative-map bridge test for a constant third-position cycle.

The actual pivot contents and common shuffle are relaxed. SAT is not a deck
realization. UNSAT excludes this larger local transition system.
"""
from pathlib import Path
import json
import random
import sys
import time
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'work/pydeps'))
import z3


def partial(a, b):
    pairs = list(zip(a, b))
    d = dict(pairs)
    assert all(d[x] == y for x, y in pairs) and len(d) == len(set(d.values()))
    return d


def probe(early, late, a, b, previous, n=83, timeout=10000, fixed=None):
    start = time.monotonic()
    labels = sorted(early.keys() | late.keys() | set(a) | {previous[0]})
    initial = {x: z3.Int('pivot_initial_%d' % x) for x in labels}
    solver = z3.Solver()
    solver.set(timeout=timeout)
    solver.add(*[z3.And(v >= 0, v < n) for v in initial.values()])
    solver.add(z3.Distinct(*initial.values()))
    solver.add(*[initial[x] == y for x, y in early.items()])
    solver.add(initial[previous[0]] == previous[1])
    if fixed is not None:
        solver.add(*[initial[x] == fixed[x] for x in labels])
    pos = initial
    trace = [pos]
    thirds = []
    old_a, old_b = previous
    for t, (ca, cb) in enumerate(zip(a, b)):
        r = pos[ca]
        third = z3.Int('pivot_third_%d' % t)
        thirds.append(third)
        solver.add(third >= 0, third < n)
        solver.add(z3.Implies(r != cb, z3.And(third != r, third != cb, third != old_b)))
        new = {}
        for x in labels:
            v = z3.Int('pivot_state_%d_%d' % (t, x))
            expr = z3.If(r == cb, pos[x], z3.If(pos[x] == r, cb,
                          z3.If(pos[x] == cb, third, z3.If(pos[x] == third, r, pos[x]))))
            solver.add(v == expr)
            new[x] = v
        solver.add(new[ca] == cb, new[old_a] == old_b)
        pos = new
        trace.append(pos)
        old_a, old_b = ca, cb
    solver.add(*[pos[x] == y for x, y in late.items()])
    status = str(solver.check())
    out = dict(status=status, seconds=time.monotonic() - start, modeled_labels=len(labels), transitions=len(a))
    if status == 'unknown':
        out['reason'] = solver.reason_unknown()
    if status == 'sat':
        model = solver.model()
        values = {x: model.eval(initial[x]).as_long() for x in labels}
        missing_x = sorted(set(range(n)) - values.keys())
        missing_y = sorted(set(range(n)) - set(values.values()))
        values.update(zip(missing_x, missing_y))
        out.update(initial_relation=[values[x] for x in range(n)],
                   third_targets=[model.eval(v).as_long() for v in thirds])
        physical = out['initial_relation'].copy()
        for t, (ca, cb, third) in enumerate(zip(a, b, out['third_targets'])):
            r = physical[ca]
            if r != cb:
                cycle = {r: cb, cb: third, third: r}
                physical = [cycle.get(v, v) for v in physical]
            assert all(physical[x] == model.eval(trace[t + 1][x]).as_long() for x in labels)
        assert sorted(physical) == list(range(n))
        assert all(physical[x] == y for x, y in late.items())
        out['final_relation'] = physical
    return out


def encrypt(pt, key, pivot, shuffle):
    deck = list(key)
    ct, trace = [], []
    for p in pt:
        assert p not in [0, pivot]
        deck[0], deck[p], deck[pivot] = deck[p], deck[pivot], deck[0]
        deck = [deck[shuffle[i]] for i in range(len(deck))]
        ct.append(deck[0])
        trace.append(deck.copy())
    return ct, trace


def controls():
    rng = random.Random(9072030)
    records = []
    for n in [7, 19, 83]:
        for trial in range(5):
            pivot = rng.randrange(1, n)
            allowed = [x for x in range(1, n) if x != pivot]
            shuffle = [0] + rng.sample(range(1, n), n - 1)
            pts = [[rng.choice(allowed) for t in range(50)] for _ in range(2)]
            pts[1][3:20] = pts[0][3:20]
            pts[1][23:50] = pts[0][23:50]
            encrypted = [encrypt(pt, rng.sample(range(n), n), pivot, shuffle) for pt in pts]
            a, b = [x[0] for x in encrypted]
            early, late = partial(a[2:20], b[2:20]), partial(a[22:], b[22:])
            entry = dict(zip(encrypted[0][1][19], encrypted[1][1][19]))
            for fixed in [entry, None]:
                r = probe(early, late, a[20:23], b[20:23], [a[19], b[19]], n, fixed=fixed)
                assert r['status'] == 'sat', (n, trial, r)
                records.append(dict(n=n, trial=trial, fixed_entry=fixed is not None, status=r['status']))
    return records


if __name__ == '__main__':
    checks = controls()
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
    a, b = raw[6][48:98], raw[8][49:99]
    early, late = partial(a[2:20], b[2:20]), partial(a[22:], b[22:])
    result = probe(early, late, a[20:23], b[20:23], [a[19], b[19]])
    result.update(controls=checks, early_map=early, late_map=late, output_a=a[20:23], output_b=b[20:23],
                  previous_outputs=[a[19], b[19]],
                  scope='Necessary local relaxation for constant-pivot three-card cycles plus an arbitrary common fixed bottom shuffle, under the two trimmed phase plaintext assumptions. SAT is not a full deck realization.')
    (ROOT / 'pivot_relative_probe.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print(result['status'], 'seconds', result['seconds'], 'generated checks', len(checks), flush=True)
