"""Independent certificate and exhaustive-small-cipher checks; stdlib only."""
from pathlib import Path
import hashlib
import itertools
import json

ROOT = Path(__file__).resolve().parent
corpus_bytes = (ROOT / 'ciphertext.json').read_bytes()
raw = list(json.loads(corpus_bytes).values())
saved = json.loads((ROOT / 'fixed_pivot_return_audit.json').read_text())
assert hashlib.sha256(corpus_bytes).hexdigest() == saved['corpus_sha256']


def gap_inventory(messages):
    intervals, lookup = [], {}
    for mi, row in enumerate(messages):
        for label in set(row):
            positions = [t for t, c in enumerate(row) if c == label]
            for a, b in zip(positions, positions[1:]):
                intervals.append((mi, a, b, label, b - a))
                lookup[mi, b] = b - a
    return intervals, lookup


intervals, lookup = gap_inventory(raw)
gaps = {r[-1] for r in intervals}
allowed = [L for L in range(1, 83) if L + 1 not in gaps]
assert allowed == [36, 68, 73] and 1 not in gaps
compact = saved['compact_W1_certificate']
assert compact['sole_plaintext_equality'] == [1, 38, 1, 68]
assert {e['gap'] for e in compact['first_return_events']} == set(range(2, 10))
assert len(compact['first_return_events']) == 8
for e in compact['first_return_events']:
    assert (e['message'], e['previous'], e['current'], e['label'], e['gap']) in intervals
assert lookup[1, 38] == 8 and lookup[1, 68] == 9
alphabet_certificate = saved['size_independent_alphabet_certificate']['first_return_events']
assert len(alphabet_certificate) == 35 and {e['gap'] for e in alphabet_certificate} == set(range(2, 37))
for e in alphabet_certificate:
    assert (e['message'], e['previous'], e['current'], e['label'], e['gap']) in intervals
checked = 0
for test in saved['tests']:
    i, s, j, t = test['sole_plaintext_equality']
    ga, gb = lookup[i, s], lookup[j, t]
    assert ga != gb
    assert {r['cycle_length'] for r in test['certificate']} == set(range(1, 83))
    assert len(test['certificate']) == 82
    for record in test['certificate']:
        L = record['cycle_length']
        if record['reason'] == 'forbidden_first_return':
            e = record['event']
            assert (e['message'], e['previous'], e['current'], e['label'], e['gap']) in intervals
            assert e['gap'] == L + 1
        else:
            assert record['reason'] == 'different_forced_selections'
            assert record['comparison']['positions'] == [[i, s], [j, t]]
            assert record['comparison']['gaps'] == [ga, gb]
            # Distinct exponents in [1,L-1] cannot name the same cycle position.
            assert 2 <= ga <= L and 2 <= gb <= L and (ga - gb) % L != 0
        checked += 1
header_results = []
for skip in [0, 1]:
    es, _ = gap_inventory([row[skip:] for row in raw])
    gs = {e[-1] for e in es}
    lengths = [L for L in range(1, 83) if L + 1 not in gs]
    counts = [len({g for g in gs if 2 <= g <= L}) for L in lengths]
    assert lengths == [36, 68, 73] and counts == [35, 66, 70]
    header_results.append(dict(first_marker_omitted=bool(skip), cycle_lengths=lengths, alphabet_lower_bounds=counts))

# Enumerate all output-fixing shuffles, pivot choices, and six-input words at
# n=3,4,5. Identity initial labels suffice because the theorem is label-invariant.
stream_checks = 0
return_checks = 0
by_size = {}
for n in [3, 4, 5]:
    size_count = 0
    for bottom in itertools.permutations(range(1, n)):
        q = [0] + list(bottom)  # source position -> destination position
        for pivot in range(1, n):
            orbit = [pivot]
            while q[orbit[-1]] != pivot:
                orbit.append(q[orbit[-1]])
            L = len(orbit)
            alphabet = [p for p in range(1, n) if p != pivot]
            updates = {}
            for p in alphabet:
                destinations = list(range(n))
                destinations[0], destinations[p], destinations[pivot] = pivot, 0, p
                updates[p] = [q[x] for x in destinations]
            for word in itertools.product(alphabet, repeat=6):
                deck = list(range(n))
                last = {}
                for t, selection in enumerate(word):
                    new = [None] * n
                    for source, dest in enumerate(updates[selection]):
                        new[dest] = deck[source]
                    deck = new
                    c = deck[0]
                    if c in last:
                        gap = t - last[c]
                        assert gap != 1 and gap != L + 1
                        if gap <= L:
                            assert selection == orbit[gap - 1]
                        return_checks += 1
                    last[c] = t
                stream_checks += 1
                size_count += 1
    by_size[str(n)] = size_count

out = dict(status='verified', cycle_length_exclusion_records_checked=checked,
           compact_certificate=dict(first_return_intervals=8, assumed_equal_input_pairs=1, all_cycle_lengths_excluded=True),
           size_independent_alphabet_certificate=dict(first_return_intervals=35, minimum_selection_alphabet=35),
           header_conventions=header_results,
           exhaustive_six_input_streams=stream_checks, exhaustive_streams_by_size=by_size,
           observed_returns_in_exhaustive_streams=return_checks,
           conclusion='The stated fixed-pivot model needs at least 35 selection values on ciphertext alone. Either one of the two separately stated plaintext equalities excludes all 82 possible pivot-cycle lengths.',
           limitations='This is not a full cipher exclusion outside the specified update family, and does not establish that any surviving large-alphabet model fits the full corpus.')
(ROOT / 'checked_fixed_pivot_returns.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')
print(json.dumps(out, indent=2))
