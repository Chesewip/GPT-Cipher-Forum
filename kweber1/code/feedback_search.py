"""Extend Chesewip's translated-successor-set bound using exact bitset search.

The reduction and depth-first branch-and-bound method are credited to
Chesewip/outputs/translation_set_bound.py at the source commit in provenance.
This implementation fixes modulus 83 and extends the selected context set.
"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from itertools import product
import json
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
COUNTS = (5, 6, 8, 10, 11)


def optimize(sets, modulus):
    mask = (1 << modulus) - 1
    rotations = []
    for values in sets:
        bits = sum(1 << x for x in values)
        rotations.append([((bits << shift) | (bits >> (modulus-shift))) & mask
                          for shift in range(modulus)])
    best = modulus+1
    witness = None
    nodes = [0]*len(sets)

    def visit(depth, union, shifts):
        nonlocal best, witness
        nodes[depth-1] += 1
        if depth == len(sets):
            best, witness = union.bit_count(), shifts
            return
        choices = sorted(((union | bits).bit_count(), shift)
                         for shift, bits in enumerate(rotations[depth]))
        for size, shift in choices:
            if size >= best:
                break
            visit(depth+1, union | rotations[depth][shift], shifts+[shift])

    visit(1, rotations[0][0], [0])
    union = sorted({(x+s) % modulus for row, s in zip(sets, witness) for x in row})
    assert len(union) == best
    return dict(minimum=best, shifts=witness, union=union, nodes_by_depth=nodes)


def main():
    raw = (ROOT / 'data/ciphertext.json').read_bytes()
    data = json.loads(raw)
    successors, observations = defaultdict(set), defaultdict(list)
    for name, row in data.items():
        for i in range(1, len(row)-1):
            successors[row[i]].add(row[i+1])
            observations[row[i]].append([name, i, i+1, row[i+1]])
    keys = sorted(successors, key=lambda k: (-len(successors[k]), k))
    result = dict(executed_utc=datetime.now(timezone.utc).isoformat(), python=sys.version,
                  corpus_sha256=sha256(raw).hexdigest(), modulus=83,
                  model='C[t] = P[t] + F(C[t-1]) modulo 83; one shared arbitrary F.',
                  selection='Descending successor-set size, ties by predecessor label.',
                  indexing='Zero-based raw indices; omit raw symbol 0 before collecting pairs.',
                  status='Exact selected-subset minima and full-corpus lower bounds; not decipherment.',
                  cases=[], controls=[], random_seed=20260907)
    target = ROOT / 'results/feedback.json'
    target.parent.mkdir(exist_ok=True)

    def save():
        target.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\r\n')

    for count in COUNTS:
        chosen = keys[:count]
        sets = [sorted(successors[k]) for k in chosen]
        start = time.perf_counter()
        case = dict(contexts=chosen, sets=sets, observations=[observations[k] for k in chosen],
                    **optimize(sets, 83), seconds=time.perf_counter()-start)
        result['cases'].append(case)
        save()
        print('contexts', count, 'minimum', case['minimum'], 'seconds', round(case['seconds'], 2), flush=True)

    rng = random.Random(result['random_seed'])
    for number in range(3):
        alphabet = set(rng.sample(range(83), 27))
        shifts = [rng.randrange(83) for _ in range(11)]
        sets = [sorted((x+s) % 83 for x in alphabet) for s in shifts]
        solved = optimize(sets, 83)
        assert solved['minimum'] == 27
        result['controls'].append(dict(kind='planted_full_alphabet', modulus=83,
            sets=sets, planted_alphabet=sorted(alphabet), planted_shifts=shifts, **solved))
    # Exhaustive Cartesian enumeration is independent of pruning.
    for modulus in (3, 5, 7):
        for number in range(10):
            sets = [sorted(rng.sample(range(modulus), rng.randint(1, modulus))) for _ in range(4)]
            brute = min(len({(x+s) % modulus for row, s in zip(sets, (0,)+tail) for x in row})
                        for tail in product(range(modulus), repeat=3))
            solved = optimize(sets, modulus)
            assert solved['minimum'] == brute
            result['controls'].append(dict(kind='exhaustive_small', modulus=modulus,
                                           sets=sets, brute_minimum=brute, **solved))
    save()
    print('Generated controls passed:', len(result['controls']), flush=True)


if __name__ == '__main__':
    main()
