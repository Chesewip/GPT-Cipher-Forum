"""Search the equivalent passage-entry constraints instead of stepwise equalities."""
from pathlib import Path
import argparse, collections, json, time
import numpy as np
from ring_order_search import neighbor_indices, fixture
from shared_update_support import assumptions
from rotation_vote_search import direct_errors
from clocked_key_attack import decode
from context_entry_solver import entry_test
ROOT = Path(__file__).resolve().parent


def prepare(ct, eq):
    edges = sorted(set((i, s, c, j, t, d)
                       for i, s, j, t, length in eq
                       for c, d in zip(ct[i][s:s + length], ct[j][t:t + length])))
    requested = collections.defaultdict(set)
    for i, s, c, j, t, d in edges:
        requested[i, s].add(c)
        requested[j, t].add(d)
    lengths = [max([t for i, t in requested if i == mi] + [0]) for mi in range(len(ct))]
    return edges, requested, lengths


def scores(ct, keys, prepared, b, soft=0):
    edges, requested, lengths = prepared
    B, n = keys.shape
    M = n - 1
    ids = np.arange(B)
    snapshots = {}
    invalid = np.isin(keys[:, 0], [row[0] for row in ct]).astype(int)
    for mi, (row, length) in enumerate(zip(ct, lengths)):
        deck = keys.copy()
        pos = np.argsort(keys, axis=1)
        for t in range(length + 1):
            for c in requested.get((mi, t), []):
                p = pos[:, c]
                snapshots[mi, t, c] = np.where(p == 0, 0, 1 + (p - 1 + t * b) % M)
            if t == length:
                break
            c = row[t]
            p = pos[:, c].copy()
            r = np.where(p == 0, 0, 1 + p % M)
            old, tail = deck[:, 0].copy(), deck[ids, r].copy()
            deck[:, 0] = c
            deck[ids, p] = tail
            deck[ids, r] = old
            pos[:, c] = 0
            pos[ids, tail] = p
            pos[ids, old] = r
    bad = np.zeros(B, dtype=int)
    dist = np.zeros(B)
    for i, s, c, j, t, d in edges:
        p, q = snapshots[i, s, c], snapshots[j, t, d]
        bad += p != q
        delta = np.abs(p - q)
        dist += np.where((p == 0) != (q == 0), 1.0, np.minimum(delta, M - delta) / (M / 2))
    if any(a == c for row in ct for a, c in zip(row, row[1:])):
        invalid[:] = 1
    return bad + 10000 * invalid, dist


def verify():
    rng = np.random.default_rng(20261123)
    checks = 0
    for n in [4, 7, 83]:
        from clocked_three_cycle_scan import encrypt_physical
        b = int(rng.integers(n - 1))
        key = rng.permutation(n)
        pt = [rng.integers(1, n, 14).tolist() for _ in range(2)]
        pt[1][6:12] = pt[0][3:9]
        eq = [(0, 3, 1, 6, 6)]
        ct = [encrypt_physical(row, key, 1, b) for row in pt]
        candidates = np.array([key] + [rng.permutation(n) for _ in range(60)])
        bad, distance = scores(ct, candidates, prepare(ct, eq), b)
        for k, errors in zip(candidates, bad):
            assert (errors == 0) == entry_test(ct, k, b, eq)
            checks += 1
        assert bad[0] == 0 and distance[0] == 0
    return checks


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', type=int, default=160)
    ap.add_argument('--soft', type=float, default=1)
    ap.add_argument('--output', required=True)
    a = ap.parse_args()
    checks = verify()
    ct, cl, planted, truept, fixture_seed = fixture(82)
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
    eq = assumptions(raw)
    prepared = prepare(ct, eq)
    rng = np.random.default_rng(20261124)
    key = rng.permutation(83)
    moves = neighbor_indices(83)
    best = 100000
    winner = None
    history = []
    start = time.time()
    for step in range(a.steps):
        keys = key[moves]
        bad, distance = scores(ct, keys, prepared, 9)
        k = int(np.argmin(bad))
        if int(bad[k]) < best:
            best = int(bad[k])
            winner = keys[k].copy()
            history.append([step, best])
        if best == 0:
            break
        temp = 1.5 * (1 - step / a.steps) + 0.1
        pick = int(np.argmin(bad + a.soft * distance - temp * rng.gumbel(size=len(bad))))
        key = keys[pick].copy()
        if step % 10 == 0:
            print('step', step, 'best entry disagreements', best, flush=True)
    err, pt = direct_errors(ct, winner.tolist(), 9, cl)
    assert (err == 0) == (best == 0)
    # The equality-only model has a cyclic bottom-coordinate gauge.
    aligned = [sum(a != 0 and b != 0 and (a - b) % 82 == delta for p, q in zip(pt, truept) for a, b in zip(p, q)) for delta in range(82)]
    result = dict(status='structural_model_fit' if best == 0 else 'search_inconclusive', control=True,
                  control_seed=fixture_seed, search_seed=20261124, rotation=9, alphabet_bound=None,
                  started_from_random_key=True, initial_deck=winner.tolist(), plaintext_positions=pt,
                  entry_disagreements=best, unique_entry_constraints=len(prepared[0]),
                  shared_selection_disagreements=err, exact_planted_plaintext_recovered=pt == truept,
                  maximum_correct_plaintext_after_cyclic_shift=max(aligned),
                  best_cyclic_shift=int(np.argmax(aligned)),
                  history=history, steps_requested=a.steps, soft_weight=a.soft,
                  seconds=time.time() - start, independent_batch_checks=checks,
                  warning='Known rotation. A failed random-start heuristic does not exclude the model; cyclic alignment is a control diagnostic, not plaintext recovery.')
    (ROOT / a.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print({k: v for k, v in result.items() if k not in ['initial_deck', 'plaintext_positions', 'history']}, flush=True)
