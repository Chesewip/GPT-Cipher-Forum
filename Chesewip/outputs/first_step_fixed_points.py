"""Exact fixed-label set after two different first selections in the deck model."""
from pathlib import Path
import collections, itertools, json
import numpy as np
ROOT = Path(__file__).resolve().parent


def step(deck, p, b):
    deck = list(deck)
    r = 1 + p % (len(deck) - 1)
    deck[0], deck[p], deck[r] = deck[p], deck[r], deck[0]
    if b:
        deck = [deck[0]] + deck[-b:] + deck[1:-b]
    return deck


def verify():
    rng = np.random.default_rng(20261127)
    checks = 0
    for n in [3, 4, 5, 6, 83]:
        keys = list(itertools.permutations(range(n))) if n <= 5 else [rng.permutation(n).tolist() for _ in range(30)]
        for key in keys:
            pairs = list(itertools.combinations(range(1, n), 2)) if n <= 6 else [rng.choice(np.arange(1, n), 2, replace=False).tolist() for _ in range(40)]
            for p, q in pairs:
                b = int(rng.integers(n - 1))
                a, d = step(key, p, b), step(key, q, b)
                moved = {key[0], key[p], key[q], key[1 + p % (n - 1)], key[1 + q % (n - 1)]}
                actual = {c for c in key if a.index(c) != d.index(c)}
                assert actual == moved
                checks += 1
    return dict(exact_support_checks=checks, deck_sizes=[3, 4, 5, 6, 83],
                theorem='After distinct first non-top selections p and q, the labels at differing physical positions are exactly the initial top, the two selected cards and their two bottom-ring successors. The following common rotation does not change the set.')


if __name__ == '__main__':
    out = verify()
    (ROOT / 'checked_first_step_fixed_points.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print(out)
    from shared_update_support import assumptions
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
    forbidden_top = set(row[0] for row in raw)
    forbidden_successors = collections.defaultdict(set)
    source_pairs = []
    for i, s, j, t, length in assumptions(raw):
        if s != 1 or t != 1 or raw[i][0] == raw[j][0]:
            continue
        for k, (c, d) in enumerate(zip(raw[i][s:s + length], raw[j][t:t + length])):
            if c != d:
                continue
            assert c not in [raw[i][0], raw[j][0]]
            forbidden_top.add(c)
            forbidden_successors[raw[i][0]].add(c)
            forbidden_successors[raw[j][0]].add(c)
            source_pairs.append([i, s + k, j, t + k, c])
    allowed_top = sorted(set(range(83)) - forbidden_top)
    certificate = dict(allowed_initial_top_labels=allowed_top, allowed_top_count=len(allowed_top),
                       forbidden_successors={c: sorted(v) for c, v in sorted(forbidden_successors.items())},
                       allowed_successor_counts_before_excluding_unknown_top={c: 83 - len(v | {c}) for c, v in sorted(forbidden_successors.items())},
                       observed_shared_prefix_pairs=source_pairs,
                       scope='Conditional on the common-reset unit-neighbor deck update and the existing repeated-plaintext prefix assumptions. Applies to every common bottom rotation. This is a consequence of the already studied four/five-label relative support, not a cipher identification.')
    for source in ['context_entry_eyes32_b9_compact.json', 'context_entry_eyes32_b12_compact.json']:
        result = json.loads((ROOT / source).read_text())
        key = result['initial_deck']
        assert key[0] in allowed_top
        for c, banned in forbidden_successors.items():
            p = key.index(c)
            assert p > 0 and key[1 + p % 82] not in banned
    certificate['saved_witness_checks'] = 2
    (ROOT / 'first_step_prefix_restrictions.json').write_text(json.dumps(certificate, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print('Allowed initial tops:', len(allowed_top), 'first-card successor restrictions:', len(forbidden_successors))
