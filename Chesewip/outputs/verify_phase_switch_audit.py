"""Independent finite checks of the local phase-switch certificate.

Does not import the discovery analyzer or run a key-search solver.
"""
from pathlib import Path
import itertools
import json
import random

ROOT = Path(__file__).resolve().parent
raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
saved = json.loads((ROOT / 'phase_switch_audit.json').read_text())


def mapping(start_a, start_b, count):
    pairs = list(zip(raw[6][start_a:start_a + count], raw[8][start_b:start_b + count]))
    d = dict(pairs)
    assert all(d[x] == y for x, y in pairs) and len(set(d.values())) == len(d)
    return d


def forced_inverse_changes(a, b):
    # Inverse value y must change if its possible source sets are disjoint.
    ia, ib = {y: x for x, y in a.items()}, {y: x for x, y in b.items()}
    domains = []
    for m in [ia, ib]:
        free = set(range(83)) - set(m.values())
        domains.append([{m[y]} if y in m else free for y in range(83)])
    return [y for y in range(83) if not (domains[0][y] & domains[1][y])]


a, b = mapping(48, 49, 20), mapping(68, 69, 30)
forced = forced_inverse_changes(a, b)
assert forced == [8, 9, 19, 42, 48, 54, 70, 73, 75]
p, q = saved['exact_distance']['completions']
assert sorted(p) == sorted(q) == list(range(83))
assert all(p[x] == y for x, y in a.items()) and all(q[x] == y for x, y in b.items())
assert sum(x != y for x, y in zip(p, q)) == len(forced) == 9
for record in saved['six_observation_certificate']:
    i, j = record['bridge_positions_zero_based']
    k, l = record['late_positions_zero_based']
    assert raw[6][i] == raw[6][k] == record['source_label']
    assert raw[8][j] == record['old_target'] and raw[8][l] == record['new_target']
assert len({record[field] for record in saved['six_observation_certificate']
            for field in ['old_target', 'new_target']}) == 6


def update(deck, position, rotation):
    d = list(deck)
    tail = position + 1 if position + 1 < len(deck) else 1
    old_top, selected, neighbor = d[0], d[position], d[tail]
    d[0], d[position], d[tail] = selected, neighbor, old_top
    bottom = d[1:]
    if rotation:
        bottom = bottom[-rotation:] + bottom[:-rotation]
    return [d[0]] + bottom


# Check all 82^2 selection pairs, with independent shuffled decks and a
# selection-dependent rotation. Also exhaust small sizes and every rotation.
rng = random.Random(9072028)
checks = 0
different_supports = set()
for n in [3, 4, 5, 6, 83]:
    da, db = rng.sample(range(n), n), rng.sample(range(n), n)
    before = dict(zip(da, db))
    for x, y in itertools.product(range(1, n), repeat=2):
        rotations = range(n - 1) if n < 83 else [(x + 7 * y) % (n - 1)]
        for rotation in rotations:
            na, nb = update(da, x, rotation), update(db, y, rotation)
            after = dict(zip(na, nb))
            changed = sum(before[c] != after[c] for c in range(n))
            assert changed <= 5
            # Old tops occupy successor(x) and successor(y) after the update.
            # The successor function is injective, so this condition is iff.
            assert (after[da[0]] == db[0]) == (x == y)
            if x == y:
                assert before == after
            if n == 83 and x != y:
                different_supports.add(changed)
            checks += 1
assert different_supports == {4, 5}

# Broader family: arbitrary injective third-position rule and arbitrary fixed
# bottom shuffle. No cyclic geometry is needed for the backward argument.
broader_checks = 0
for n in [7, 19, 83]:
    for trial in range(8):
        while True:
            tail = [0] + rng.sample(range(1, n), n - 1)
            if all(tail[x] != x for x in range(1, n)):
                break
        shuffle = [0] + rng.sample(range(1, n), n - 1)
        da, db = rng.sample(range(n), n), rng.sample(range(n), n)
        before = dict(zip(da, db))
        for _ in range(80):
            x, y = rng.randrange(1, n), rng.randrange(1, n)
            after_decks = []
            for deck, position in [(da, x), (db, y)]:
                d = list(deck)
                q = tail[position]
                d[0], d[position], d[q] = d[position], d[q], d[0]
                after_decks.append([d[shuffle[i]] for i in range(n)])
            after = dict(zip(*after_decks))
            assert sum(before[c] != after[c] for c in range(n)) <= 5
            assert (after[da[0]] == db[0]) == (x == y)
            assert x != y or before == after
            broader_checks += 1

# Equal plaintext at raw 51..67 forces a stable map on outputs 50..67.
# Equal plaintext at raw 71..97 forces a stable map on outputs 70..97.
early, late = mapping(50, 51, 18), mapping(70, 71, 28)
current = 70
backward = []
while current > 68:
    previous_pair = [raw[6][current - 1], raw[8][current]]
    assert late[previous_pair[0]] == previous_pair[1]
    later_matches = [t for t in range(70, 98)
                     if [raw[6][t], raw[8][t + 1]] == previous_pair]
    assert later_matches
    backward.append(dict(from_E4_raw=current, to_E4_raw=current - 1,
                         previous_top_pair=previous_pair, later_E4_raw_observations=later_matches))
    current -= 1
trimmed_forced = forced_inverse_changes(early, late)
assert trimmed_forced == [8, 9, 19, 54, 70, 73, 75]
assert len(trimmed_forced) > 5
# A six-label subcertificate survives the conservative input trimming.
targets = []
for x in [79, 26, 78]:
    targets.extend([early[x], late[x]])
assert len(set(targets)) == 6
# Scope counterexample: a noninjective tail can preserve the old-top pair
# after different selections while changing the relation. Do not apply the
# backward implication to that wider family.
noninjective_decks = []
for selection in [1, 2]:
    d = list(range(5))
    d[0], d[selection], d[3] = d[selection], d[3], d[0]
    noninjective_decks.append(d)
noninjective_relation = dict(zip(*noninjective_decks))
assert noninjective_relation[0] == 0
assert sum(noninjective_relation[x] != x for x in range(5)) == 3
out = dict(status='verified', full_phase_exact_minimum=9,
           full_phase_forced_inverse_rows=forced,
           trimmed_phase_forced_inverse_rows=trimmed_forced,
           backward_steps=backward,
           physical_update_pair_checks=checks,
           arbitrary_injective_tail_and_bottom_shuffle_checks=broader_checks,
           noninjective_scope_counterexample=dict(initial_decks=[list(range(5))] * 2,
                                                  selections=[1, 2], common_third_position=3,
                                                  final_decks=noninjective_decks,
                                                  old_top_pair_preserved=True, changed_relative_entries=3),
           unit_neighbor_83_card_distinct_input_supports=sorted(different_supports),
           conclusion='The two specified repeated-plaintext alignments cannot both hold for anchored three-cycles with a common injective third-position rule and a common output-fixing shuffle. This includes all fixed nonzero cyclic neighbor offsets and every fixed bottom shuffle. Arbitrary keys and independent entry decks are allowed.',
           limitation='No authentic plaintext recovered; noninjective third-position rules, other deck updates, and different plaintext alignments remain unexcluded.')
(ROOT / 'checked_phase_switch_audit.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')
print(json.dumps(out, indent=2))
