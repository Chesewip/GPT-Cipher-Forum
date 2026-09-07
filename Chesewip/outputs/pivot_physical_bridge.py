"""Exact three-transition physical bridge with arbitrary common bottom shuffle.

Entry A's cards name positions, so its entry deck is identity and its observed
top label is the anchor position. This is a coordinate gauge, not a known key.
Only the three boundary transitions are realized, not the 50-output passages.
"""
from pathlib import Path
import json
import random
import sys
import time
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'work/pydeps'))
import z3
from pivot_relative_probe import partial, encrypt


def solve(early, late, a, b, previous, n=83, timeout=20000, fixed=None):
    start = time.monotonic()
    anchor = previous[0]
    solver = z3.Solver()
    solver.set(timeout=timeout)
    q = z3.Function('physical_shuffle', z3.IntSort(), z3.IntSort())
    q_values = [q(i) for i in range(n)]
    solver.add(*[z3.And(v >= 0, v < n) for v in q_values], z3.Distinct(*q_values), q(anchor) == anchor)
    pivot = z3.Int('physical_pivot')
    solver.add(pivot >= 0, pivot < n, pivot != anchor)
    labels_a = sorted(early.keys() | late.keys() | set(a) | {anchor})
    labels_b = sorted(set(early.values()) | set(late.values()) | set(b) | {previous[1]})
    pa = {c: z3.IntVal(c) for c in labels_a}
    pb = {c: z3.Int('physical_initial_b_%d' % c) for c in labels_b}
    initial_b = pb.copy()
    solver.add(*[z3.And(v >= 0, v < n) for v in pb.values()], z3.Distinct(*pb.values()))
    solver.add(pb[previous[1]] == anchor)
    solver.add(*[pb[y] == x for x, y in early.items()])
    if fixed:
        solver.add(pivot == fixed['pivot'])
        solver.add(*[q(i) == v for i, v in enumerate(fixed['shuffle'])])
        solver.add(*[pb[c] == fixed['positions_b'][c] for c in labels_b])
    selections = []
    for t, (ca, cb) in enumerate(zip(a, b)):
        p, r = pa[ca], pb[cb]
        selections.append([p, r])
        solver.add(p != anchor, p != pivot, r != anchor, r != pivot)
        states = []
        for side, positions, choice in [('a', pa, p), ('b', pb, r)]:
            result = {}
            for c, old in positions.items():
                v = z3.Int('physical_%s_%d_%d' % (side, t, c))
                moved = z3.If(old == choice, anchor, z3.If(old == anchor, pivot, z3.If(old == pivot, choice, old)))
                solver.add(v == q(moved))
                result[c] = v
            states.append(result)
        pa, pb = states
    solver.add(*[pa[x] == pb[y] for x, y in late.items()])
    status = str(solver.check())
    out = dict(status=status, seconds=time.monotonic() - start, anchor=anchor,
               modeled_labels=[len(labels_a), len(labels_b)], transitions=len(a))
    if status == 'unknown':
        out['reason'] = solver.reason_unknown()
    if status == 'sat':
        m = solver.model()
        deck_b = [-1] * n
        for c, position in initial_b.items():
            deck_b[m.eval(position).as_long()] = c
        rest = iter(sorted(set(range(n)) - set(deck_b)))
        deck_b = [next(rest) if c < 0 else c for c in deck_b]
        out.update(initial_decks=[list(range(n)), deck_b], pivot=m.eval(pivot).as_long(),
                   shuffle_destinations=[m.eval(q(i)).as_long() for i in range(n)],
                   selections=[[m.eval(p).as_long(), m.eval(r).as_long()] for p, r in selections])
        replay(out, early, late, a, b)
    return out


def replay(witness, early, late, a, b):
    decks = [d.copy() for d in witness['initial_decks']]
    n, anchor, pivot = len(decks[0]), witness['anchor'], witness['pivot']
    assert all(sorted(d) == list(range(n)) for d in decks)
    shuffle = witness['shuffle_destinations']
    assert sorted(shuffle) == list(range(n)) and shuffle[anchor] == anchor
    relation = dict(zip(*decks))
    assert all(relation[x] == y for x, y in early.items())
    ciphertext = [[], []]
    for choices in witness['selections']:
        for side, p in enumerate(choices):
            assert p not in [anchor, pivot]
            d = decks[side]
            d[anchor], d[p], d[pivot] = d[p], d[pivot], d[anchor]
            new = [None] * n
            for old, dest in enumerate(shuffle):
                new[dest] = d[old]
            decks[side] = new
            ciphertext[side].append(new[anchor])
    assert ciphertext == [a, b]
    relation = dict(zip(*decks))
    assert all(relation[x] == y for x, y in late.items())
    return dict(ciphertext=ciphertext, final_decks=decks)


def controls():
    rng = random.Random(9072031)
    checks = []
    for n in [7, 19, 83]:
        pivot = rng.randrange(1, n)
        alphabet = [p for p in range(1, n) if p != pivot]
        shuffle = [0] + rng.sample(range(1, n), n - 1)
        pts = [[rng.choice(alphabet) for _ in range(50)] for side in range(2)]
        pts[1][3:20] = pts[0][3:20]
        pts[1][23:50] = pts[0][23:50]
        encrypted = [encrypt(pt, rng.sample(range(n), n), pivot, shuffle) for pt in pts]
        a, b = [e[0] for e in encrypted]
        da, db = [e[1][19] for e in encrypted]
        # Old position i gets coordinate da[i]. Conjugate the shuffle, which
        # encrypt() represents by destination-to-source rather than source-to-dest.
        source_to_dest = [shuffle.index(i) for i in range(n)]
        gauge_q = [None] * n
        for i in range(n):
            gauge_q[da[i]] = da[source_to_dest[i]]
        gauge_b = [None] * n
        for i, c in enumerate(db):
            gauge_b[c] = da[i]
        fixed = dict(pivot=da[pivot], shuffle=gauge_q, positions_b=gauge_b)
        early, late = partial(a[2:20], b[2:20]), partial(a[22:], b[22:])
        for pinned in [True, False]:
            if n == 83 and not pinned:
                continue
            r = solve(early, late, a[20:23], b[20:23], [a[19], b[19]], n, timeout=3000,
                      fixed=fixed if pinned else None)
            assert r['status'] != 'unsat', r
            checks.append(dict(n=n, planted_mechanism_fixed=pinned, status=r['status'], seconds=r['seconds'], reason=r.get('reason')))
            print('Control:', checks[-1], flush=True)
    return checks


if __name__ == '__main__':
    checks = controls()
    print('Physical generated checks:', checks, flush=True)
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
    a, b = raw[6][48:98], raw[8][49:99]
    early, late = partial(a[2:20], b[2:20]), partial(a[22:], b[22:])
    if all(c['status'] == 'sat' for c in checks):
        r = solve(early, late, a[20:23], b[20:23], [a[19], b[19]], timeout=30000)
    else:
        r = dict(status='not_run_after_control_timeout', seconds=0,
                 reason='The unknown-mechanism solver did not pass generated calibration. No real-cipher exclusion is inferred.')
    r.update(controls=checks, early_map=early, late_map=late,
             earlier_attempt=dict(status='generated_control_timeout', seconds=20.06199999999808,
                                  modeled_labels=[18, 18], saved_result=False,
                                  note='Original controls asserted SAT and stopped on UNKNOWN before running the real bridge. The driver now retains unknown outcomes.'),
             output_a=a[20:23], output_b=b[20:23], previous_outputs=[a[19], b[19]],
             scope='Actual three-transition bridge with independent entry decks and one common constant pivot and bottom shuffle. The surrounding passage histories are not realized. SAT is not a full cipher key.')
    (ROOT / 'pivot_physical_bridge.json').write_text(json.dumps(r, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print(r['status'], 'seconds', r['seconds'], flush=True)
