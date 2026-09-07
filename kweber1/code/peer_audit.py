"""Independent targeted checks of Dr0pflux and ChatGPT-Sol research claims.

No imported peer code. Numeric certificate labels are attributed in data.
Exact replay witnesses below demonstrate model capacity, not readable plaintext.
"""
from pathlib import Path
from itertools import combinations, product, permutations
from functools import lru_cache
from datetime import datetime, timezone
from hashlib import sha256
import json
import random
import time

ROOT = Path(__file__).resolve().parents[1]


def periodic_checker(limit):
    # Every linear binary period with between 1 and limit copies of each bit.
    # No necklace canonicalization or graph optimizer is used here.
    words = []
    for length in range(2, 2*limit+1):
        for bits in product('01', repeat=length):
            ones = bits.count('1')
            if 1 <= ones <= limit and 1 <= length-ones <= limit:
                words.append(''.join(bits))

    @lru_cache(maxsize=None)
    def allowed(sequence):
        mask = 0
        for i, word in enumerate(words):
            if sequence in word * (len(sequence)//len(word)+2):
                mask |= 1 << i
        return mask

    def compatible(sequences):
        mask = (1 << len(words))-1
        for sequence in sorted(sequences, key=len, reverse=True):
            mask &= allowed(sequence)
            if not mask:
                return False
        return True

    return compatible, len(words)


def homophone_audit(messages):
    reference = json.loads((ROOT / 'data/peer_certificates.json').read_text())
    labels = sorted(set().union(*(set(r) for r in messages.values())))
    projections = {(a, b): [''.join('0' if x == a else '1' for x in row if x in (a, b))
                            for row in messages.values()] for a, b in combinations(labels, 2)}
    rows = []
    first_edges = None
    for case in reference['bounds']:
        limit = case['multiplicity']
        check, word_count = periodic_checker(limit)
        word = '0'*limit+'1'*limit
        controls = [(word*12)[phase:phase+8*len(word)+1] for phase in (0, limit, len(word)-1)]
        assert check(controls)
        assert not check(['0'*(limit+1)+'1'+'0'*(limit+1)+'1'])
        edges = {pair for pair, sequences in projections.items() if check(sequences)}
        assert len(edges) == case['compatible_pair_count']
        certificate = case['certificate']
        assert len(certificate) == len(set(certificate)) and set(certificate) <= set(labels)
        assert all(tuple(sorted(pair)) not in edges for pair in combinations(certificate, 2))
        rows.append(dict(multiplicity=limit, linear_period_words=word_count,
                         compatible_pair_count=len(edges), lower_bound=len(certificate),
                         certificate_pairs_checked=len(certificate)*(len(certificate)-1)//2,
                         generated_positive_and_negative_controls=True))
        if limit == 1:
            first_edges = edges
        print('Peer cycle audit', limit, 'passed:', len(edges), 'compatible pairs', flush=True)

    # Complete the multiplicity-one lower bound by constructing a 79-class model.
    matching = [(0, 35), (15, 70), (27, 76), (53, 82)]
    assert all(pair in first_edges for pair in matching)
    used = [x for pair in matching for x in pair]
    assert len(used) == len(set(used))
    cycles = [list(pair) for pair in matching] + [[x] for x in labels if x not in used]
    assert len(cycles) == 79
    owner = {x: i for i, cycle in enumerate(cycles) for x in cycle}
    witnesses = {}
    for name, row in messages.items():
        phases = [0]*len(cycles)
        for i, cycle in enumerate(cycles):
            first = next((x for x in row if x in cycle), None)
            if first is not None:
                phases[i] = cycle.index(first)
        plaintext = [owner[x] for x in row]
        positions = phases.copy()
        replay = []
        for p in plaintext:
            replay.append(cycles[p][positions[p]])
            positions[p] = (positions[p]+1) % len(cycles[p])
        assert replay == row
        witnesses[name] = dict(class_stream=plaintext, initial_phases=phases,
                               replayed_symbols=len(replay), exact_replay=True)
    return dict(source_commit=reference['source_commit'], bounds=rows,
        total_certificate_pairs_checked=sum(r['certificate_pairs_checked'] for r in rows),
        multiplicity_one=dict(exact_minimum_unrestricted_classes=79, cycles=cycles,
                             matching=matching, messages=witnesses,
                             interpretation='Capacity witness; class IDs are not recovered linguistic plaintext.'))


def lag_capacity_audit(messages):
    modulus = 83
    rng = random.Random(20260908)
    permutation = list(range(modulus))
    rng.shuffle(permutation)
    inverse = {c: p for p, c in enumerate(permutation)}
    result = []
    for lag in range(1, 41):
        history = [rng.randrange(modulus) for _ in range(lag)]
        for row in messages.values():
            state = history.copy()
            for c in row:
                state.append((inverse[c]-state[-lag]) % modulus)
            plain = state[lag:]
            emitted, previous = [], None
            repairs = 0
            for i, p in enumerate(plain):
                r = (p+state[i]) % modulus
                if previous is not None and r == previous:
                    r = (r+1) % modulus
                    repairs += 1
                emitted.append(permutation[r])
                previous = r
            assert emitted == row and repairs == 0
        result.append(dict(lag=lag, exact_messages=len(messages), repairs=0))

    # Small exhaustive image check covers arbitrary ciphertext, including repeats.
    # Identity output labels suffice: bijective relabeling preserves adjacency.
    tiny = []
    q = 3
    length = 4
    expected_all = set(product(range(q), repeat=length))
    expected_fixed = {c for c in expected_all if all(a != b for a, b in zip(c, c[1:]))}
    for lag in range(1, 4):
        for history in product(range(q), repeat=lag):
            raw_image, fixed_image = set(), set()
            for plaintext in product(range(q), repeat=length):
                state = history+plaintext
                raw, fixed = [], []
                for i, p in enumerate(plaintext):
                    r = (p+state[i]) % q
                    raw.append(r)
                    fixed.append((r+1) % q if fixed and r == fixed[-1] else r)
                raw_image.add(tuple(raw))
                fixed_image.add(tuple(fixed))
            assert raw_image == expected_all and fixed_image == expected_fixed
        tiny.append(dict(lag=lag, histories=q**lag, raw_image_size=len(expected_all),
                         repaired_image_size=len(expected_fixed)))
    return dict(source_commit='5975dcff2cfe329d800dd903ef91a938b520e442', random_seed=20260908,
                finite_lag_checks=result, exhaustive_modulus_3_length_4=tiny,
                observation='All bodies have zero adjacent repeats.',
                caveat='Previous emitted state is None at each message start; plaintext alphabet unrestricted.')


def main():
    start = time.perf_counter()
    raw = (ROOT / 'data/ciphertext.json').read_bytes()
    messages = {k: v[1:] for k, v in json.loads(raw).items()}
    assert all(a != b for row in messages.values() for a, b in zip(row, row[1:]))
    result = dict(executed_utc=datetime.now(timezone.utc).isoformat(),
                  corpus_sha256=sha256(raw).hexdigest(),
                  status='Targeted independent replications and a model-capacity completion; cipher unsolved.',
                  homophone=homophone_audit(messages), lag_capacity=lag_capacity_audit(messages),
                  seconds=time.perf_counter()-start)
    (ROOT / 'results').mkdir(exist_ok=True)
    (ROOT / 'results/peer_audit.json').write_text(json.dumps(result, indent=2)+'\n',
                                               encoding='utf-8', newline='\r\n')
    print('Peer checks passed; saved reproducible 79-class capacity witness.')


if __name__ == '__main__':
    main()
