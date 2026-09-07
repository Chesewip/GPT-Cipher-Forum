"""Circular-order key search, with independent scoring and recovery checks.

This is a heuristic for the unit-neighbor three-cycle model, not a decryption.
The known rotation and contiguous alphabet are explicit control assumptions.
"""
from pathlib import Path
import argparse, collections, json, time
import numpy as np
from clocked_key_attack import decode
from clocked_three_cycle_scan import encrypt_physical
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
ROOT = Path(__file__).resolve().parent


def relations(classes):
    groups = collections.defaultdict(list)
    for index, label in enumerate(x for row in classes for x in row):
        groups[label].append(index)
    pairs = [(a, b, 1 / (len(g) - 1)) for g in groups.values()
             for i, a in enumerate(g) for b in g[i + 1:]]
    return pairs


def batch_decode(ct, keys, b):
    batch, n = keys.shape
    ids = np.arange(batch)
    result = np.empty((batch, sum(map(len, ct))), dtype=np.int16)
    index = 0
    for row in ct:
        deck = keys.copy()
        pos = np.argsort(keys, axis=1)
        for t, c in enumerate(row):
            p = pos[:, c].copy()
            result[:, index] = np.where(p == 0, 0, 1 + (p - 1 + t * b) % (n - 1))
            index += 1
            r = np.where(p == 0, 0, 1 + p % (n - 1))
            old, tail = deck[:, 0].copy(), deck[ids, r].copy()
            deck[:, 0] = c
            deck[ids, p] = tail
            deck[ids, r] = old
            pos[:, c] = 0
            pos[ids, tail] = p
            pos[ids, old] = r
    return result


def score(pt, pairs, n, alphabet=None, soft=0.0):
    invalid = np.count_nonzero(pt == 0, axis=1)
    outside = np.zeros(len(pt), dtype=np.int32) if alphabet is None else np.count_nonzero(pt > alphabet, axis=1)
    equality = np.zeros(len(pt))
    distance = np.zeros(len(pt))
    for a, b, w in pairs:
        d = np.abs(pt[:, a] - pt[:, b])
        equality += w * (d != 0)
        distance += w * np.minimum(d, n - 1 - d) / ((n - 1) / 2)
    if alphabet is not None:
        # Circular distance from each out-of-range selection to the allowed arc.
        d = np.minimum(np.maximum(pt - alphabet, 0), n - pt)
        distance += np.sum(d, axis=1) / ((n - 1) / 2)
    cost = 10000 * invalid + outside + 2 * equality + soft * distance
    return cost, outside, equality, invalid


def neighbor_indices(n):
    base = list(range(n))
    moves = [base]
    # Remove one bottom card and insert it at each other bottom position.
    for a in range(1, n):
        short = base[:a] + base[a + 1:]
        for b in range(1, n):
            if a != b:
                moves.append(short[:b] + [a] + short[b:])
    for a in range(1, n):
        for b in range(a + 2, n + 1):
            moves.append(base[:a] + base[a:b][::-1] + base[b:])
    for a in range(1, n):
        trial = base.copy()
        trial[0], trial[a] = trial[a], trial[0]
        moves.append(trial)
    for a in range(1, n - 1):
        moves.append([0] + base[1 + a:] + base[1:1 + a])
    return np.unique(np.array(moves, dtype=np.int16), axis=0)


def verify():
    rng = np.random.default_rng(20261120)
    checks = 0
    for n in [4, 5, 9, 83]:
        moves = neighbor_indices(n)
        assert np.all(np.sort(moves, axis=1) == np.arange(n))
        key = rng.permutation(n)
        b = int(rng.integers(n - 1))
        pt = [rng.integers(1, n, 20).tolist() for _ in range(3)]
        ct = [encrypt_physical(row, key, 1, b) for row in pt]
        keys = np.array([key] + [rng.permutation(n) for _ in range(12)])
        decoded = batch_decode(ct, keys, b)
        for candidate, row in zip(keys, decoded):
            independent = decode(ct, candidate.tolist(), b)
            assert row.tolist() == sum(independent, [])
            checks += 1
        classes = [[(t % 7) for t in range(20)] for _ in pt]
        pairs = relations(classes)
        _, outside, equality, invalid = score(decoded, pairs, n, max(1, n // 3))
        flatcl = sum(classes, [])
        for k, row in enumerate(decoded.tolist()):
            grouped = collections.defaultdict(list)
            for c, p in zip(flatcl, row):
                grouped[c].append(p)
            expected = sum(sum(x != y for i, x in enumerate(g) for y in g[i + 1:]) / (len(g) - 1)
                           for g in grouped.values() if len(g) > 1)
            assert abs(expected - equality[k]) < 1e-8
            assert outside[k] == sum(p > max(1, n // 3) for p in row)
            assert invalid[k] == row.count(0)
            checks += 1
    return checks


def fixture(alphabet):
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
    cl = make_plaintexts(raw, assumptions(raw))
    seed = 20261117 if alphabet == 27 else 20261106
    rng = np.random.default_rng(seed)
    key = rng.permutation(83)
    values = {x: int(rng.integers(1, alphabet + 1)) for row in cl for x in row}
    pt = [[values[x] for x in row] for row in cl]
    for i, row in enumerate(pt):
        row[0] = i + 1
    return [encrypt_physical(row, key, 1, 9) for row in pt], cl, key, pt, seed


def search(ct, cl, steps, seed, alphabet, soft, truekey=None, truept=None, start_key=None, headers=False):
    rng = np.random.default_rng(seed)
    key = rng.permutation(83) if start_key is None else np.array(start_key)
    moves = neighbor_indices(83)
    if headers:
        for i, row in enumerate(ct):
            p = i + 1
            q = int(np.flatnonzero(key == row[0])[0])
            key[p], key[q] = key[q], key[p]
        fixed = np.arange(1, len(ct) + 1)
        moves = moves[np.all(moves[:, fixed] == fixed, axis=1)]
    pairs = relations(cl)
    best = float('inf')
    winner = None
    history = []
    start = time.time()
    for step in range(steps):
        keys = key[moves]
        decoded = batch_decode(ct, keys, 9)
        cost, outside, eq, invalid = score(decoded, pairs, 83, alphabet, soft)
        hard = outside + 2 * eq + 10000 * invalid
        k = int(np.argmin(hard))
        if hard[k] < best - 1e-8:
            best = float(hard[k])
            winner = keys[k].copy()
            history.append([step, best, int(outside[k]), float(eq[k])])
        if best < 1e-8:
            break
        temp = 1.5 * (1 - step / steps) + 0.1
        pick = int(np.argmin(cost - temp * rng.gumbel(size=len(cost))))
        key = keys[pick].copy()
        if step % 10 == 0:
            print('step', step, 'best hard cost', round(best, 3), 'outside', history[-1][2], flush=True)
    pt = decode(ct, winner.tolist(), 9)
    assert all(encrypt_physical(p, winner, 1, 9) == c for p, c in zip(pt, ct))
    seen = {}
    star_errors = 0
    for labels, row in zip(cl, pt):
        for label, p in zip(labels, row):
            if label in seen:
                star_errors += p != seen[label]
            else:
                seen[label] = p
    result = dict(status='structural_model_fit' if best < 1e-8 else 'search_inconclusive',
                  initial_deck=winner.tolist(), plaintext_positions=pt, rotation=9,
                  hard_cost=best, shared_selection_disagreements=star_errors,
                  outside_alphabet=sum(p > alphabet for row in pt for p in row) if alphabet else None,
                  invalid_top_selections=sum(p == 0 for row in pt for p in row),
                  steps_requested=steps, seed=seed, alphabet_bound=alphabet, soft_weight=soft,
                  numbered_headers_assumed=headers,
                  unique_neighbors_per_step=len(moves), history=history, seconds=time.time() - start,
                  exact_ciphertext_replay=True,
                  warning='Known rotation, optional known contiguous alphabet. A random-start heuristic failure does not exclude a cipher. Replay does not authenticate plaintext.')
    if truept is not None:
        result['exact_planted_plaintext_recovered'] = pt == truept
        result['correct_plaintext_positions'] = sum(a == b for p, q in zip(pt, truept) for a, b in zip(p, q))
        planted_edges = set(zip(truekey[1:], np.roll(truekey[1:], -1)))
        result['correct_directed_ring_edges'] = sum(edge in planted_edges for edge in zip(winner[1:], np.roll(winner[1:], -1)))
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', type=int, default=80)
    ap.add_argument('--alphabet', type=int, default=27)
    ap.add_argument('--soft', type=float, default=0)
    ap.add_argument('--seed', type=int, default=20261121)
    ap.add_argument('--output', required=True)
    ap.add_argument('--source')
    ap.add_argument('--headers', action='store_true')
    a = ap.parse_args()
    checks = verify()
    ct, cl, key, pt, fixture_seed = fixture(a.alphabet)
    initial = json.loads((ROOT / a.source).read_text())['initial_deck'] if a.source else None
    result = search(ct, cl, a.steps, a.seed, a.alphabet if a.alphabet < 82 else None, a.soft, key, pt, initial, a.headers)
    result.update(control=True, control_seed=fixture_seed, independent_checks=checks, started_from_random_key=a.source is None, source=a.source)
    (ROOT / a.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print({k: v for k, v in result.items() if k not in ['initial_deck', 'plaintext_positions', 'history']}, flush=True)
