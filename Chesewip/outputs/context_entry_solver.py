"""Replace equal-input runs by equal card positions at run entry.

In a label-equivariant positional deck cipher, equal plaintext runs preserve
the entire relative card-label permutation. Therefore every observed label pair
in the run can be compared at its entry snapshot. This is equivalent to replaying
the equalities, not an additional plaintext assumption. No alphabet bound.
"""
from pathlib import Path
import argparse, collections, itertools, json, sys, time
import numpy as np
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'work/pydeps'))
import z3
from clocked_key_attack import decode
from clocked_three_cycle_scan import encrypt_physical
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts


def solve(ct, equalities, b, n=83, timeout=20000, fixed=None, compact=False):
    start = time.time()
    M = n - 1
    width = n.bit_length() if compact else (2 * n).bit_length()
    bv = lambda x: z3.BitVecVal(int(x), width)
    solver = z3.SolverFor('QF_BV') if compact else z3.Solver()
    solver.set(timeout=timeout)
    requested = collections.defaultdict(set)
    edges = set()
    for i, s, j, t, length in equalities:
        assert length > 0 and s + length <= len(ct[i]) and t + length <= len(ct[j])
        for c, d in zip(ct[i][s:s + length], ct[j][t:t + length]):
            requested[i, s].add(c)
            requested[j, t].add(d)
            edges.add((i, s, c, j, t, d))
    lengths = [max([t for mi, t in requested if mi == i] + [0]) for i in range(len(ct))]
    observed = set(c for (mi, t), cards in requested.items() for c in cards)
    observed.update(c for row, length in zip(ct, lengths) for c in row[:length])
    observed.update(row[0] for row in ct if row)
    gauge = not fixed
    fixed = fixed or {ct[0][0]: 1}
    observed.update(fixed)
    initial = {}
    free = []
    available = [p for p in range(n) if p not in fixed.values()]
    for c in sorted(observed):
        if c in fixed:
            initial[c] = bv(fixed[c])
        else:
            v = z3.BitVec('entry_initial_' + str(c), width)
            initial[c] = v
            free.append(v)
            if compact:
                solver.add(z3.ULT(v, bv(n)), *[v != bv(p) for p in fixed.values()])
            else:
                solver.add(z3.Or(*[v == bv(p) for p in available]))
    if free:
        solver.add(z3.Distinct(*free))
    for row in ct:
        if row:
            solver.add(initial[row[0]] != bv(0))
        if any(a == c for a, c in zip(row, row[1:])):
            solver.add(False)
    snapshots = {}
    intermediate = 0
    for mi, (row, length) in enumerate(zip(ct, lengths)):
        need = set(row[:length])
        need.update(c for (i, t), cards in requested.items() if i == mi for c in cards)
        pos = {c: initial[c] for c in need}
        for t in range(length + 1):
            for c in requested[mi, t]:
                snapshots[mi, t, c] = pos[c]
            if t == length:
                break
            c = row[t]
            p = pos[c]
            solver.add(p != bv(0))
            neighbor = z3.If(p == bv(M), bv(1), p + bv(1))
            future = set(row[t + 1:length])
            future.update(c for (i, u), cards in requested.items() if i == mi and u > t for c in cards)
            nxt = {}
            for card in future:
                q = pos[card]
                expr = bv(0) if card == c else z3.simplify(z3.If(q == bv(0), neighbor, z3.If(q == neighbor, p, q)))
                if expr.num_args() > 0:
                    v = z3.BitVec('entry_%d_%d_%d' % (mi, t, card), width)
                    solver.add(v == expr)
                    intermediate += 1
                else:
                    v = expr
                nxt[card] = v
            pos = nxt
    for i, s, c, j, t, d in sorted(edges):
        p, q = snapshots[i, s, c], snapshots[j, t, d]
        offset = ((s - t) * b) % M
        moved = z3.If(p == bv(0), bv(0), z3.If(z3.ULE(p, bv(M - offset)), p + bv(offset), p - bv(M - offset)))
        solver.add(moved == q)
    encoded = time.time()
    status = str(solver.check())
    out = dict(status=status, rotation=b, context_count=len(equalities), unique_position_constraints=len(edges),
               encoded_prefix_lengths=lengths, output_lengths=list(map(len, ct)), free_key_entries=len(free),
               materialized_positions=intermediate, encoding_seconds=encoded - start,
               solve_seconds=time.time() - encoded, bottom_rotation_gauge=gauge, alphabet_bound=None,
               fixed_initial_positions=fixed if not gauge else None, compact_domains=compact,
               bit_vector_width=width, solver_logic='QF_BV' if compact else 'general')
    if status == 'unknown':
        out['reason'] = solver.reason_unknown()
    if status == 'sat':
        model = solver.model()
        key = [-1] * n
        for c, v in initial.items():
            key[model.eval(v).as_long()] = c
        missing = iter(c for c in range(n) if c not in key)
        key = [next(missing) if c < 0 else c for c in key]
        pt = decode(ct, key, b)
        assert all(p != 0 for row in pt for p in row)
        assert all(pt[i][s:s + length] == pt[j][t:t + length] for i, s, j, t, length in equalities)
        assert all(encrypt_physical(row, key, 1, b) == message for row, message in zip(pt, ct))
        out.update(initial_deck=key, plaintext_positions=pt, exact_common_key_replay=True)
    out['scope'] = 'Exact fixed-rotation unit-neighbor model and listed plaintext equalities, no language or alphabet assumption. SAT is a structural fit, not authenticated plaintext.'
    return out


def entry_test(ct, key, b, eq):
    snapshots = {}
    for mi, row in enumerate(ct):
        deck = list(key)
        for t, c in enumerate(row):
            snapshots[mi, t] = deck.copy()
            p = deck.index(c)
            if p == 0:
                return False
            r = 1 + p % (len(key) - 1)
            deck[0], deck[p], deck[r] = deck[p], deck[r], deck[0]
            if b:
                deck = [deck[0]] + deck[-b:] + deck[1:-b]
    return all(snapshots[i, s].index(c) == snapshots[j, t].index(d)
               for i, s, j, t, length in eq
               for c, d in zip(ct[i][s:s + length], ct[j][t:t + length]))


def verify():
    rng = np.random.default_rng(20261122)
    checks = 0
    fixtures = 0
    for n in [4, 5, 6]:
        for trial in range(8):
            b = int(rng.integers(n - 1))
            key = rng.permutation(n)
            pt = [rng.integers(1, n, 9).tolist() for _ in range(2)]
            pt[1][4:8] = pt[0][2:6]
            eq = [(0, 2, 1, 4, 4)]
            ct = [encrypt_physical(row, key, 1, b) for row in pt]
            if trial % 2:
                ct[1][int(rng.integers(9))] = int(rng.integers(n))
            possible = False
            for k in itertools.permutations(range(n)):
                decoded = decode(ct, k, b)
                expected = all(p != 0 for row in decoded for p in row) and decoded[0][2:6] == decoded[1][4:8]
                assert entry_test(ct, k, b, eq) == expected
                checks += 1
                possible |= expected
            for compact in [False, True]:
                r = solve(ct, eq, b, n, timeout=5000, compact=compact)
                assert r['status'] in ['sat', 'unsat']
                assert (r['status'] == 'sat') == possible
                fixtures += 1
    return dict(exhaustive_key_equivalence_checks=checks, solver_fixtures=fixtures)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--control', action='store_true')
    ap.add_argument('--length', type=int, default=32)
    ap.add_argument('--rotation', type=int, default=9)
    ap.add_argument('--timeout', type=int, default=20000)
    ap.add_argument('--headers', action='store_true')
    ap.add_argument('--compact', action='store_true')
    ap.add_argument('--output', required=True)
    a = ap.parse_args()
    if a.verify:
        result = verify()
    else:
        raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
        eq = [(i, s, j, t, min(length, a.length - s, a.length - t))
              for i, s, j, t, length in assumptions(raw) if s < a.length and t < a.length]
        ct = [row[:a.length] for row in raw]
        truept = None
        if a.control:
            from adaptive_equality_search import fixture
            control, cl, key, planted = fixture()
            ct = [row[:a.length] for row in control]
            truept = [row[:a.length] for row in planted]
        fixed = {row[0]: i + 1 for i, row in enumerate(ct)} if a.headers else None
        result = solve(ct, eq, a.rotation, timeout=a.timeout, fixed=fixed, compact=a.compact)
        result.update(equalities=eq, control=a.control, numbered_headers_assumed=a.headers)
        if a.control:
            result['exact_planted_plaintext_recovered'] = result.get('plaintext_positions') == truept
    (ROOT / a.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print({k: v for k, v in result.items() if k not in ['initial_deck', 'plaintext_positions', 'equalities']}, flush=True)
