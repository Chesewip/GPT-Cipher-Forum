"""Independent breadth-first verification; does not import discovery code.

Enumerate every distinct partial union smaller than the reported optimum.
Translations are constructed by explicit modular addition, not bit rotation.
An empty final layer proves the lower bound; a matching union proves tightness.
This verifier design follows the independently checked finite-union method in
Chesewip/outputs/verify_feedback_bounds.py, with source attribution in the report.
"""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from itertools import product
import json
import time

ROOT = Path(__file__).resolve().parents[1]


def verify(case, modulus):
    sets, bound = case['sets'], case['minimum']
    shifts = case['shifts']
    assert len(shifts) == len(sets) and shifts[0] == 0
    assert all(0 <= x < modulus for x in shifts)
    assert all(len(s) == len(set(s)) and all(0 <= x < modulus for x in s) for s in sets)
    witness = sorted({(value+shift) % modulus for row, shift in zip(sets, shifts) for value in row})
    assert witness == case['union'] and len(witness) == bound
    states = {sum(1 << value for value in sets[0])} if len(sets[0]) < bound else set()
    counts = [len(states)]
    for row in sets[1:]:
        translated = [sum(1 << ((value+shift) % modulus) for value in row) for shift in range(modulus)]
        states = {u | v for u in states for v in translated if (u | v).bit_count() < bound}
        counts.append(len(states))
    assert not states, 'A union smaller than the reported minimum exists.'
    return counts


def main():
    raw = (ROOT / 'data/ciphertext.json').read_bytes()
    messages = json.loads(raw)
    source = json.loads((ROOT / 'results/feedback.json').read_text())
    assert source['corpus_sha256'] == sha256(raw).hexdigest()
    sets, locations = defaultdict(set), defaultdict(list)
    for name, row in messages.items():
        body = list(enumerate(row))[1:]
        for (i, a), (j, b) in zip(body, body[1:]):
            sets[a].add(b)
            locations[a].append([name, i, j, b])
    keys = sorted(sets, key=lambda k: (-len(sets[k]), k))
    out = dict(executed_utc=datetime.now(timezone.utc).isoformat(), cases=[], controls=0,
               corpus_sha256=source['corpus_sha256'], status='Verified; no decipherment claimed.')
    for case in source['cases']:
        selected = keys[:len(case['contexts'])]
        assert selected == case['contexts']
        assert [sorted(sets[k]) for k in selected] == case['sets']
        assert [locations[k] for k in selected] == case['observations']
        start = time.perf_counter()
        counts = verify(case, 83)
        out['cases'].append(dict(context_count=len(selected), minimum=case['minimum'],
            feasible_partial_unions_below_minimum=counts, seconds=time.perf_counter()-start))
        print('Verified', len(selected), 'contexts:', case['minimum'], counts, flush=True)
    for control in source['controls']:
        modulus = control['modulus']
        verify(control, modulus)
        if control['kind'] == 'planted_full_alphabet':
            assert control['minimum'] == len(control['planted_alphabet']) == 27
            assert [sorted((x+s) % modulus for x in control['planted_alphabet'])
                    for s in control['planted_shifts']] == control['sets']
        else:
            brute = min(len(set().union(*({(x+s) % modulus for x in row}
                for row, s in zip(control['sets'], (0,)+tail))))
                for tail in product(range(modulus), repeat=len(control['sets'])-1))
            assert brute == control['minimum'] == control['brute_minimum']
        out['controls'] += 1
    assert [c['minimum'] for c in out['cases']] == [43, 46, 50, 52, 53]
    (ROOT / 'results/feedback_verification.json').write_text(json.dumps(out, indent=2)+'\n',
                                                           encoding='utf-8', newline='\r\n')
    print('All', out['controls'], 'controls independently verified.')


if __name__ == '__main__':
    main()
