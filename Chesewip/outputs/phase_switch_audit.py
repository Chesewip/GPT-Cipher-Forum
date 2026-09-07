"""Audit the published E4/E5 phase switch without assuming it is plaintext.

Minimum Hamming distance between completions of two partial bijections is
computed exactly. This is a local necessary test, not a full cipher solver.
"""
from pathlib import Path
import hashlib
import itertools
import json
import random
import numpy as np

ROOT = Path(__file__).resolve().parent
SOURCE = 'https://github.com/mvelzel/eye-vibe/blob/main/docs/thirty-second-synchronizing-bridge-results-2026-07-26.md'


def partial(a, b):
    forward, inverse = {}, {}
    for x, y in zip(a, b):
        if x in forward and forward[x] != y or y in inverse and inverse[y] != x:
            return None
        forward[x], inverse[y] = y, x
    return forward


def signature(seq):
    names = {}
    return [names.setdefault(x, len(names)) for x in seq]


def completion_distance(a, b, n=83):
    """Maximize agreement, then independently complete both permutations.

    A row specified in either map can agree only at its specified column.
    That column must be unoccupied elsewhere in the other map. All such
    eligible rows coexist. Rows unspecified in both can agree only in columns
    unused in both. Pair as many as possible; no other agreement is possible.
    """
    assert len(set(a.values())) == len(a) and len(set(b.values())) == len(b)
    shared = {}
    for x in sorted(a.keys() | b.keys()):
        values = {m[x] for m in [a, b] if x in m}
        if len(values) == 1:
            y = next(iter(values))
            if all(x in m or y not in m.values() for m in [a, b]):
                shared[x] = y
    free_rows = sorted(set(range(n)) - a.keys() - b.keys())
    free_columns = sorted(set(range(n)) - set(a.values()) - set(b.values()))
    shared.update(zip(free_rows, free_columns))
    completions = []
    for original in [a, b]:
        m = {**original, **shared}
        rows = sorted(set(range(n)) - m.keys())
        columns = sorted(set(range(n)) - set(m.values()))
        m.update(zip(rows, columns))
        p = [m[x] for x in range(n)]
        assert sorted(p) == list(range(n))
        assert all(p[x] == y for x, y in original.items())
        completions.append(p)
    distance = sum(x != y for x, y in zip(*completions))
    assert distance == n - len(shared)
    return dict(minimum_changed_entries=distance, maximum_agreements=len(shared),
                completions=completions)


def brute_controls():
    rng = random.Random(9072026)
    counts = {}
    for n in [3, 4, 5]:
        perms = np.array(list(itertools.permutations(range(n))))
        distances = np.count_nonzero(perms[:, None, :] != perms[None, :, :], axis=2)
        if n == 3:
            maps = {tuple((x, int(p[x])) for x in range(n) if mask >> x & 1)
                    for p in perms for mask in range(1 << n)}
            cases = itertools.product(sorted(maps), repeat=2)
        else:
            cases = []
            for _ in range(400):
                pair = []
                for __ in range(2):
                    p = rng.sample(range(n), n)
                    pair.append(tuple((x, p[x]) for x in range(n) if rng.randrange(2)))
                cases.append(pair)
        checked = 0
        for aa, bb in cases:
            a, b = dict(aa), dict(bb)
            selections = []
            for m in [a, b]:
                selections.append([i for i, p in enumerate(perms) if all(p[x] == y for x, y in m.items())])
            exact = int(distances[np.ix_(*selections)].min())
            assert completion_distance(a, b, n)['minimum_changed_entries'] == exact
            checked += 1
        counts[str(n)] = checked
    return counts


def generated_controls():
    # Explicit physical decks, arbitrary independent entry keys and rotations.
    rng = random.Random(9072027)
    count = 0
    for n in [7, 19, 83]:
        for changes in [1, 2]:
            for _ in range(40):
                rotation = rng.randrange(n - 1)
                pts = [[rng.randrange(1, n) for t in range(50)]]
                pts.append(pts[0].copy())
                for t in range(20, 20 + changes):
                    pts[1][t] = rng.choice([p for p in range(1, n) if p != pts[0][t]])
                traces, cts = [], []
                for pt in pts:
                    deck = rng.sample(range(n), n)
                    trace, ct = [], []
                    for p in pt:
                        q = 1 + p % (n - 1)
                        deck[0], deck[p], deck[q] = deck[p], deck[q], deck[0]
                        bottom = deck[1:]
                        if rotation:
                            bottom = bottom[-rotation:] + bottom[:-rotation]
                        deck = [deck[0]] + bottom
                        trace.append(deck.copy())
                        ct.append(deck[0])
                    traces.append(trace)
                    cts.append(ct)
                relations = [dict(zip(x, y)) for x, y in zip(*traces)]
                for t in range(1, 50):
                    d = sum(relations[t][x] != relations[t - 1][x] for x in range(n))
                    assert d <= (5 if pts[0][t] != pts[1][t] else 0)
                a = partial(cts[0][:20], cts[1][:20])
                b = partial(cts[0][20 + changes - 1:], cts[1][20 + changes - 1:])
                assert a is not None and b is not None
                assert completion_distance(a, b, n)['minimum_changed_entries'] <= 5 * changes
                count += 1
    return count


def run():
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
    a, b = raw[6][48:98], raw[8][49:99]
    bridge, late = partial(a[:20], b[:20]), partial(a[20:], b[20:])
    assert bridge is not None and late is not None
    assert partial(a[:21], b[:21]) is None
    assert signature(raw[7][50:67]) == signature(a[:17]) == signature(b[:17])
    assert signature(raw[7][50:68]) != signature(a[:18])
    exact = completion_distance(bridge, late)
    assert exact['minimum_changed_entries'] == 9
    # Three disjoint forced moves already require six moved target labels.
    # Each record is one paired ciphertext observation in each phase.
    six = []
    for x in [75, 79, 26]:
        i = a[:20].index(x)
        j = 20 + a[20:].index(x)
        six.append(dict(source_label=x, old_target=b[i], new_target=b[j],
                        bridge_positions_zero_based=[48 + i, 49 + i],
                        late_positions_zero_based=[48 + j, 49 + j]))
    targets = [r[k] for r in six for k in ['old_target', 'new_target']]
    assert len(set(targets)) == 6
    trims = []
    for trim in range(6):
        p = partial(a[trim:20], b[trim:20])
        q = partial(a[20 + trim:], b[20 + trim:])
        entry = 20 + trim
        steps = []
        while entry > 20 and q.get(a[entry - 1]) == b[entry - 1]:
            steps.append(dict(current_local_output=entry, previous_output_pair=[a[entry - 1], b[entry - 1]],
                              repeated_at_local_outputs=[t for t in range(20 + trim, 50)
                                                         if (a[t], b[t]) == (a[entry - 1], b[entry - 1])]))
            entry -= 1
        trims.append(dict(trim=trim, minimum_changed_entries=completion_distance(p, q)['minimum_changed_entries'],
                          transitions_between_retained_phases=trim + 1,
                          unit_neighbor_backward_steps=steps, earliest_forced_late_relation=entry,
                          remaining_transition_budget=entry - 19,
                          unit_neighbor_excluded=completion_distance(p, q)['minimum_changed_entries'] > 5 * (entry - 19),
                          note='Backward propagation uses the injective neighbor function; it is not valid for arbitrary positional updates.'))
    cuts = []
    for split in range(1, 50):
        p, q = partial(a[:split], b[:split]), partial(a[split:], b[split:])
        if p is not None and q is not None:
            cuts.append(dict(split=split, minimum_changed_entries=completion_distance(p, q)['minimum_changed_entries']))
    assert cuts == [dict(split=20, minimum_changed_entries=9)]
    assert [r['unit_neighbor_excluded'] for r in trims] == [True, True, True, False, False, False]
    from clocked_key_attack import decode
    witnesses = []
    for name in ['incremental_eyes40_bv.json', 'context_entry_eyes32_b9_compact.json', 'context_entry_eyes32_b12_compact.json']:
        saved = json.loads((ROOT / name).read_text())
        stages = saved.get('stages', [saved])
        for stage in stages:
            if stage['status'] != 'sat':
                continue
            pt = decode(raw, stage['initial_deck'], saved['rotation'])
            mismatch = [t for t, (x, y) in enumerate(zip(pt[6][48:98], pt[8][49:99])) if x != y]
            witnesses.append(dict(source=name, fitted_prefix=stage.get('prefix_length', len(stage['plaintext_positions'][0])),
                                  rotation=saved['rotation'], window_plaintext_disagreements=len(mismatch),
                                  local_disagreement_positions=mismatch))
    from entry_change_bounds import bound
    rows = bound(a, b, common_initial=False)
    return dict(status='Conditional injective-tail three-card exclusion from two trimmed phase alignments; cipher unsolved.', source=SOURCE,
                corpus_sha256=hashlib.sha256((ROOT / 'ciphertext.json').read_bytes()).hexdigest(),
                coordinates='Zero-based raw ciphertext; first marker included in raw indexing. Ranges end-exclusive.',
                windows=dict(E4=[48, 98], E5=[49, 99], split=20),
                bridge=dict(edges=sorted(bridge.items()), signature=signature(a[:20])),
                late=dict(edges=sorted(late.items()), signature=signature(a[20:])),
                exact_distance=exact, six_observation_certificate=six, valid_single_change_cuts=cuts,
                trimming_sensitivity=trims, saved_key_checks=witnesses,
                trimmed_unit_neighbor_exclusion=dict(
                    assumed_plaintext_equalities=[[6, 51, 8, 52, 17], [6, 71, 8, 72, 27]],
                    equality_format='message_index, raw_start, message_index, raw_start, length',
                    initial_observed_relations=[[6, 50, 8, 51, 18], [6, 70, 8, 71, 28]],
                    late_relation_forced_back_to_raw=[68, 69],
                    minimum_relation_changes=7, maximum_changes_in_remaining_transition=5,
                    scope='Unit-neighbor three-cycle followed by any common fixed bottom rotation; arbitrary independent entry decks. First three input positions of each full phase are initially unconstrained.'),
                broader_proven_scope='The same proof applies to any fixed injective third-position rule with no self-neighbor, followed by any common fixed permutation of the bottom positions. See the independent verifier.',
                ciphertext_only_row_bound=dict(forward=rows['forward_entry_change_bound'],
                                              inverse=rows['inverse_entry_change_bound'],
                                              minimum_differences_for_support_5=rows['minimum_plaintext_differences_by_relative_support']['5']),
                controls=dict(exhaustive_completion_checks=brute_controls(), generated_physical_deck_pairs=generated_controls()),
                limitations=['Pattern isomorphism does not establish equal plaintext.',
                             'No full deck family is excluded without the stated one-boundary plaintext assumption.',
                             'Two arbitrary permutation completions are not a cipher key or reachable deck states.',
                             'At least two input differences is a lower bound, not proof that two suffice.',
                             'Phase observation is prior work; this applies our existing entry-change method to it.'])


if __name__ == '__main__':
    result = run()
    (ROOT / 'phase_switch_audit.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print(json.dumps({k: result[k] for k in ['status', 'valid_single_change_cuts', 'ciphertext_only_row_bound', 'controls']}, indent=2))
