"""Independent exhaustive checks for same-message, overlapping and fixed-key cases."""
from pathlib import Path
import itertools, json
import numpy as np
from context_entry_solver import solve, entry_test
from clocked_key_attack import decode
from clocked_three_cycle_scan import encrypt_physical
ROOT = Path(__file__).resolve().parent
rng = np.random.default_rng(20261125)
checks = 0
records = []
for n in [4, 5]:
    for trial in range(10):
        b = trial % (n - 1)
        key = rng.permutation(n).tolist()
        pt = [rng.integers(1, n, 14).tolist() for _ in range(2)]
        pt[0][7:11] = pt[0][2:6]
        pt[1][3:7] = pt[0][2:6]
        eq = [(0, 2, 0, 7, 4), (0, 7, 1, 3, 4), (0, 3, 1, 4, 2)]
        ct = [encrypt_physical(row, key, 1, b) for row in pt]
        if trial % 2:
            ct[trial % 2][trial % 14] = int(rng.integers(n))
        fixed = {key[p]: p for p in range(min(2, n))} if trial % 3 else None
        possible = False
        for candidate in itertools.permutations(range(n)):
            if fixed and any(candidate[p] != c for c, p in fixed.items()):
                continue
            decoded = decode(ct, candidate, b)
            expected = all(p != 0 for row in decoded for p in row) and all(
                decoded[i][s:s + length] == decoded[j][t:t + length] for i, s, j, t, length in eq)
            assert entry_test(ct, candidate, b, eq) == expected
            possible |= expected
            checks += 1
        for compact in [False, True]:
            result = solve(ct, eq, b, n, timeout=5000, fixed=fixed, compact=compact)
            assert result['status'] in ['sat', 'unsat']
            assert (result['status'] == 'sat') == possible
            records.append(dict(n=n, trial=trial, fixed=fixed, compact=compact, has_key=possible, status=result['status']))
# A full-size fixed planted key checks the 83-card arithmetic in both encodings.
from adaptive_equality_search import fixture
from shared_update_support import assumptions
ct, cl, key, pt = fixture()
raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
for compact in [False, True]:
    result = solve(ct, assumptions(raw), 9, fixed={int(c): p for p, c in enumerate(key)}, compact=compact)
    assert result['status'] == 'sat' and result['plaintext_positions'] == pt
out = dict(exhaustive_key_equivalence_checks=checks, solver_fixtures=len(records), full_size_fixed_key_checks=2, fixtures=records)
(ROOT / 'checked_context_entry_extended.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')
print({k: v for k, v in out.items() if k != 'fixtures'})
