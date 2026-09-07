"""Incremental exact passage-entry solver with BV, finite-domain or integer encodings.

All key positions remain free except the existing circular-coordinate gauge.
The circuit is built once, then passage constraints are added by output cutoff.
No solver initial-value hints and no candidate key entries are pinned.
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


class Problem:
    def __init__(self, ct, eq, b, n=83, encoding='bv', simplify_headers=False, lazy_distinct=False):
        self.ct, self.eq, self.b, self.n = ct, eq, b, n
        self.encoding = encoding
        self.lazy_distinct = lazy_distinct
        self.learned_distinct_pairs = 0
        self.start = time.time()
        self.solver = z3.SolverFor({'bv': 'QF_BV', 'fd': 'QF_FD', 'int': 'QF_LIA'}[encoding])
        integer = encoding == 'int'
        width = n.bit_length()
        val = (lambda x: z3.IntVal(int(x))) if integer else (lambda x: z3.BitVecVal(int(x), width))
        var = z3.Int if integer else (lambda name: z3.BitVec(name, width))
        le = (lambda x, y: x <= y) if integer else z3.ULE
        M = n - 1
        requested = collections.defaultdict(set)
        levels = {}
        for i, s, j, t, length in eq:
            assert length > 0 and s + length <= len(ct[i]) and t + length <= len(ct[j])
            for k, (c, d) in enumerate(zip(ct[i][s:s + length], ct[j][t:t + length])):
                edge = (i, s, c, j, t, d)
                level = max(s + k + 1, t + k + 1)
                levels[edge] = min(levels.get(edge, level), level)
                if not (simplify_headers and s == t == 1 and c == d):
                    requested[i, s].add(c)
                    requested[j, t].add(d)
        lengths = [max([t for i, t in requested if i == mi] + [0]) for mi in range(len(ct))]
        observed = set(c for cards in requested.values() for c in cards)
        observed.update(c for i, s, c, j, t, d in levels if simplify_headers and s == t == 1 and c == d)
        observed.update(c for row, length in zip(ct, lengths) for c in row[:length])
        observed.update(row[0] for row in ct if row)
        fixed = {ct[0][0]: 1}
        self.initial = {}
        free = []
        for c in sorted(observed):
            if c in fixed:
                self.initial[c] = val(fixed[c])
            else:
                v = var('inc_initial_%d' % c)
                self.initial[c] = v
                free.append(v)
                if integer:
                    self.solver.add(v >= 0, v < n, v != 1)
                else:
                    self.solver.add(z3.ULT(v, val(n)), v != val(1))
        if free and not lazy_distinct:
            self.solver.add(z3.Distinct(*free))
        for row in ct:
            if row:
                self.solver.add(self.initial[row[0]] != val(0))
            if any(a == c for a, c in zip(row, row[1:])):
                self.solver.add(False)
        snapshots = {}
        intermediate = 0
        for mi, (row, length) in enumerate(zip(ct, lengths)):
            future_need = [set(row[t:length]) | set(c for (i, u), cards in requested.items() if i == mi and u >= t for c in cards)
                           for t in range(length + 1)]
            pos = {c: self.initial[c] for c in future_need[0]}
            for t in range(length + 1):
                for c in requested.get((mi, t), []):
                    snapshots[mi, t, c] = pos[c]
                if t == length:
                    break
                c = row[t]
                p = pos[c]
                self.solver.add(p != val(0))
                neighbor = z3.If(p == val(M), val(1), p + val(1))
                nxt = {}
                for card in sorted(future_need[t + 1]):
                    q = pos[card]
                    expr = val(0) if card == c else z3.simplify(z3.If(q == val(0), neighbor, z3.If(q == neighbor, p, q)))
                    if expr.num_args() > 0:
                        v = var('inc_position_%d_%d_%d' % (mi, t, card))
                        self.solver.add(v == expr)
                        intermediate += 1
                    else:
                        v = expr
                    nxt[card] = v
                pos = nxt
        self.pending = []
        simplified = 0
        for edge, level in sorted(levels.items(), key=lambda item: (item[1], item[0])):
            i, s, c, j, t, d = edge
            if simplify_headers and s == t == 1 and c == d:
                h, k = ct[i][0], ct[j][0]
                if h == k:
                    expr = z3.BoolVal(True)
                elif c in [h, k]:
                    expr = z3.BoolVal(False)
                else:
                    succ = lambda x: z3.If(self.initial[x] == val(M), val(1), self.initial[x] + val(1))
                    expr = z3.And(self.initial[c] != val(0), self.initial[c] != succ(h), self.initial[c] != succ(k))
                self.pending.append((level, expr))
                simplified += 1
                continue
            p, q = snapshots[i, s, c], snapshots[j, t, d]
            offset = ((s - t) * b) % M
            moved = z3.If(p == val(0), val(0), z3.If(le(p, val(M - offset)), p + val(offset), p - val(M - offset)))
            self.pending.append((level, moved == q))
        self.added = 0
        self.level = 0
        self.metadata = dict(encoding=encoding, rotation=b, deck_size=n, free_key_entries=len(free),
                             materialized_positions=intermediate, encoded_prefix_lengths=lengths,
                             unique_entry_constraints=len(levels), encoding_seconds=time.time() - self.start,
                             fixed_initial_positions=None, bottom_rotation_gauge=True,
                             first_step_simplification=simplify_headers, simplified_entry_constraints=simplified,
                             uniqueness_strategy='lazy' if lazy_distinct else 'eager')

    def check(self, level, timeout):
        assert level >= self.level
        self.level = level
        while self.added < len(self.pending) and self.pending[self.added][0] <= level:
            self.solver.add(self.pending[self.added][1])
            self.added += 1
        start = time.time()
        collision_rounds = []
        while True:
            remaining = timeout - int(1000 * (time.time() - start))
            if remaining <= 0:
                status = 'unknown'
                break
            self.solver.set(timeout=remaining)
            status = str(self.solver.check())
            if status != 'sat' or not self.lazy_distinct:
                break
            model = self.solver.model()
            groups = collections.defaultdict(list)
            for c, v in self.initial.items():
                groups[model.eval(v).as_long()].append(c)
            collisions = [cards for cards in groups.values() if len(cards) > 1]
            if not collisions:
                break
            for cards in collisions:
                self.solver.add(z3.Distinct(*[self.initial[c] for c in cards]))
                self.learned_distinct_pairs += len(cards) * (len(cards) - 1) // 2
            collision_rounds.append(dict(colliding_groups=len(collisions),
                                         cards_in_collisions=sum(map(len, collisions)),
                                         total_distinct_pairs_added=self.learned_distinct_pairs))
        out = dict(status=status, prefix_length=level, active_entry_constraints=self.added,
                   solve_seconds=time.time() - start, timeout_ms=timeout,
                   collision_refinement_rounds=collision_rounds, total_distinct_pairs_added=self.learned_distinct_pairs)
        if status == 'unknown':
            out['reason'] = 'stage_time_limit' if remaining <= 0 else self.solver.reason_unknown()
        if status == 'sat':
            model = self.solver.model()
            key = [-1] * self.n
            for c, v in self.initial.items():
                key[model.eval(v).as_long()] = c
            missing = iter(c for c in range(self.n) if c not in key)
            key = [next(missing) if c < 0 else c for c in key]
            assert sorted(key) == list(range(self.n))
            pt = decode(self.ct, key, self.b)
            assert all(p != 0 for row in pt for p in row)
            for i, s, j, t, length in self.eq:
                count = max(0, min(length, level - s, level - t))
                assert pt[i][s:s + count] == pt[j][t:t + count]
            assert all(encrypt_physical(row, key, 1, self.b) == message for row, message in zip(pt, self.ct))
            out.update(initial_deck=key, plaintext_positions=[row[:level] for row in pt], exact_common_key_replay=True)
        return out


def verify():
    rng = np.random.default_rng(20261126)
    records = []
    key_checks = 0
    for n in [4, 5]:
        for trial in range(8):
            b = trial % (n - 1)
            key = rng.permutation(n)
            pt = [rng.integers(1, n, 10).tolist() for _ in range(2)]
            pt[0][6:9] = pt[0][1:4]
            pt[1][4:7] = pt[0][1:4]
            eq = [(0, 1, 0, 6, 3), (0, 1, 1, 4, 3), (0, 2, 1, 5, 2)]
            if trial >= 4:
                pt[1][1:4] = pt[0][1:4]
                eq.append((0, 1, 1, 1, 3))
            ct = [encrypt_physical(row, key, 1, b) for row in pt]
            if trial % 2:
                ct[1][5] = int(rng.integers(n))
            levels = [5, 7, 9, 10]
            possible = {level: False for level in levels}
            for k in itertools.permutations(range(n)):
                decoded = decode(ct, k, b)
                valid = all(p != 0 for row in decoded for p in row)
                for level in levels:
                    ok = valid
                    for i, s, j, t, length in eq:
                        count = max(0, min(length, level - s, level - t))
                        ok &= decoded[i][s:s + count] == decoded[j][t:t + count]
                    possible[level] |= ok
                    key_checks += 1
            for encoding in ['bv', 'fd', 'int']:
                for simplified in [False, True]:
                    for lazy in [False, True]:
                        problem = Problem(ct, eq, b, n, encoding, simplified, lazy)
                        for level in levels:
                            result = problem.check(level, 5000)
                            assert result['status'] in ['sat', 'unsat']
                            assert (result['status'] == 'sat') == possible[level]
                            records.append(dict(n=n, trial=trial, encoding=encoding, simplified=simplified, lazy=lazy, level=level, status=result['status']))
    return dict(exhaustive_key_cutoff_checks=key_checks, solver_checks=len(records), records=records)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--control', action='store_true')
    ap.add_argument('--encoding', choices=['bv', 'fd', 'int'], default='bv')
    ap.add_argument('--rotation', type=int, default=9)
    ap.add_argument('--levels', default='32,33,34,35,36,37,38,40')
    ap.add_argument('--timeout', type=int, default=30000)
    ap.add_argument('--output', required=True)
    ap.add_argument('--simplify-headers', action='store_true')
    ap.add_argument('--lazy-distinct', action='store_true')
    a = ap.parse_args()
    path = ROOT / a.output
    if a.verify:
        result = verify()
        path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\r\n')
        print({k: v for k, v in result.items() if k != 'records'})
    else:
        levels = sorted(set(map(int, a.levels.split(','))))
        target = max(levels)
        raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
        eq = [(i, s, j, t, min(length, target - s, target - t)) for i, s, j, t, length in assumptions(raw)
              if s < target and t < target]
        truept = None
        if a.control:
            from adaptive_equality_search import fixture
            ct, cl, key, truept = fixture()
        else:
            ct = raw
        ct = [row[:target] for row in ct]
        problem = Problem(ct, eq, a.rotation, encoding=a.encoding, simplify_headers=a.simplify_headers, lazy_distinct=a.lazy_distinct)
        result = dict(**problem.metadata, control=a.control, equalities=eq, stages=[],
                      scope='One common key, fixed rotation, unrestricted non-top plaintext positions. SAT is a conditional structural fit, not a decipherment. No candidate key is pinned.')
        for level in levels:
            stage = problem.check(level, a.timeout)
            if a.control:
                stage['exact_planted_plaintext_recovered'] = stage.get('plaintext_positions') == [row[:level] for row in truept]
            result['stages'].append(stage)
            path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\r\n')
            print({k: v for k, v in stage.items() if k not in ['initial_deck', 'plaintext_positions']}, flush=True)
            if stage['status'] != 'sat':
                break
