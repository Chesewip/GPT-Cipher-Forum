"""Repair a candidate via exact unsatisfiable cores of temporary key pins.

Dropped pins impose no key restriction. A found model must satisfy every
passage constraint and be independently replayed. Failure is not exclusion
unless all candidate assumptions have been removed and the base is UNSAT.
"""
from pathlib import Path
import argparse, collections, json, sys, time
import numpy as np
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / 'work/pydeps'))
import z3
from incremental_context_solver import Problem
from clocked_key_attack import decode
from clocked_three_cycle_scan import encrypt_physical
from shared_update_support import assumptions


def repair(ct, eq, b, candidate, n=83, seconds=90, per_check=3000, seed=20261128, simplify=True, policy='most_seen'):
    start = time.time()
    rng = np.random.default_rng(seed)
    candidate = list(candidate)
    first = ct[0][0]
    p = candidate.index(first)
    if p == 0:
        candidate[0], candidate[1] = candidate[1], candidate[0]
        p = 1
    candidate = [candidate[0]] + candidate[p:] + candidate[1:p]
    problem = Problem(ct, eq, b, n, 'bv', simplify)
    solver = problem.solver
    solver.add(*[expr for level, expr in problem.pending])
    pins = {}
    for c, v in problem.initial.items():
        if z3.is_bv_value(v):
            continue
        flag = z3.Bool('pin_card_%d' % c)
        solver.add(z3.Implies(flag, v == z3.BitVecVal(candidate.index(c), n.bit_length())))
        pins[c] = flag
    active = set(pins)
    frequencies = collections.Counter(c for row in ct for c in row)
    rank = lambda c: ((-1 if policy == 'most_seen' else 1) * frequencies[c], float(rng.random()))
    history = []
    released = []
    answer = None
    status = 'inconclusive'
    while time.time() - start < seconds:
        remaining = max(1, int(1000 * (seconds - (time.time() - start))))
        solver.set(timeout=min(per_check, remaining))
        current = str(solver.check(*[pins[c] for c in sorted(active)]))
        record = dict(status=current, active_pins=len(active), elapsed_seconds=time.time() - start)
        if current == 'sat':
            model = solver.model()
            key = [-1] * n
            for c, v in problem.initial.items():
                key[model.eval(v).as_long()] = c
            missing = iter(c for c in range(n) if c not in key)
            key = [next(missing) if c < 0 else c for c in key]
            pt = decode(ct, key, b)
            assert sorted(key) == list(range(n))
            assert all(p != 0 for row in pt for p in row)
            assert all(pt[i][s:s + length] == pt[j][t:t + length] for i, s, j, t, length in eq)
            assert all(encrypt_physical(row, key, 1, b) == message for row, message in zip(pt, ct))
            assert all(key[candidate.index(c)] == c for c in active)
            answer = dict(initial_deck=key, plaintext_positions=pt, exact_common_key_replay=True,
                          changed_observed_card_positions=sum(key.index(c) != candidate.index(c) for c in problem.initial),
                          active_fixed_cards=sorted(active))
            status = 'structural_model_fit'
            history.append(record)
            break
        if current == 'unsat':
            names = {str(x) for x in solver.unsat_core()}
            core = sorted(c for c in active if str(pins[c]) in names)
            record['conflicting_fixed_cards'] = core
            if not core:
                status = 'conditional_model_excluded'
                history.append(record)
                break
            order = sorted(core, key=rank)
        else:
            record['reason'] = solver.reason_unknown()
            if not active:
                history.append(record)
                break
            order = sorted(active, key=rank)
        dropped = order[:min(2, len(order))]
        for c in dropped:
            active.remove(c)
            solver.add(z3.Not(pins[c]))
            released.append(c)
        record['released_cards'] = dropped
        history.append(record)
        print('repair', len(history), current, 'remaining pins', len(active), flush=True)
    out = dict(status=status, rotation=b, output_lengths=list(map(len, ct)), seconds=time.time() - start,
               time_limit=seconds, per_check_timeout_ms=per_check, seed=seed, history=history,
               release_policy=policy,
               normalized_start_key=candidate, released_cards=released, remaining_pins=len(active),
               encoding=problem.metadata, equalities=eq,
               scope='Candidate-key assumptions guide search and are released using conflicts or on timeout. A fitted key satisfies the complete listed equality problem. Partial repair failure is not a cipher exclusion.')
    if answer:
        out.update(answer)
    return out


def verify():
    rng = np.random.default_rng(20261129)
    records = []
    for n in [4, 5, 7]:
        for trial in range(4):
            key = rng.permutation(n)
            b = trial % (n - 1)
            pt = [rng.integers(1, n, 12).tolist() for _ in range(2)]
            pt[1][4:9] = pt[0][2:7]
            eq = [(0, 2, 1, 4, 5)]
            ct = [encrypt_physical(row, key, 1, b) for row in pt]
            result = repair(ct, eq, b, rng.permutation(n), n, seconds=5, per_check=1000)
            assert result['status'] == 'structural_model_fit'
            records.append(dict(n=n, trial=trial, status=result['status'], rounds=len(result['history'])))
    return dict(generated_repairs_checked=len(records), records=records)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--control', action='store_true')
    ap.add_argument('--source')
    ap.add_argument('--length', type=int, default=40)
    ap.add_argument('--rotation', type=int, default=9)
    ap.add_argument('--seconds', type=int, default=90)
    ap.add_argument('--per-check', type=int, default=3000)
    ap.add_argument('--output', required=True)
    ap.add_argument('--policy', choices=['most_seen', 'least_seen'], default='most_seen')
    a = ap.parse_args()
    if a.verify:
        result = verify()
    else:
        raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
        eq = [(i, s, j, t, min(length, a.length - s, a.length - t))
              for i, s, j, t, length in assumptions(raw) if s < a.length and t < a.length]
        if a.control:
            from adaptive_equality_search import fixture
            ct, cl, planted_key, planted = fixture()
        else:
            ct = raw
        source = json.loads((ROOT / a.source).read_text())
        if 'stages' in source:
            source = next(stage for stage in reversed(source['stages']) if stage['status'] == 'sat')
        result = repair([row[:a.length] for row in ct], eq, a.rotation, source['initial_deck'], seconds=a.seconds, per_check=a.per_check, policy=a.policy)
        result.update(source=a.source, control=a.control)
        if a.control:
            result['exact_planted_plaintext_recovered'] = result.get('plaintext_positions') == [row[:a.length] for row in planted]
    (ROOT / a.output).write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print({k: v for k, v in result.items() if k not in ['history', 'initial_deck', 'plaintext_positions', 'normalized_start_key', 'equalities', 'records']}, flush=True)
