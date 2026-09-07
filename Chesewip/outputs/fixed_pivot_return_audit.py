"""Key-independent first-return test for constant-pivot three-card updates.

Select p outside {top,pivot}; cycle selected->top, top->pivot, pivot->p;
apply one common fixed shuffle fixing top. The pivot's shuffle cycle has
length L. A first return at gap g <= L selects Q**(g-1)(pivot), and gap L+1
is impossible. This finite obstruction does not use a key-search failure.
"""
from pathlib import Path
import hashlib
import itertools
import json
import random

ROOT = Path(__file__).resolve().parent


def events(messages):
    result, gaps = [], []
    for mi, row in enumerate(messages):
        last, row_gaps = {}, []
        for t, c in enumerate(row):
            g = t - last[c] if c in last else None
            row_gaps.append(g)
            if g is not None:
                result.append(dict(message=mi, previous=last[c], current=t, label=c, gap=g))
            last[c] = t
        gaps.append(row_gaps)
    return result, gaps


def analyze(messages, equalities, n=83):
    returns, gaps = events(messages)
    by_gap = {}
    for event in returns:
        by_gap.setdefault(event['gap'], event)
    comparisons = []
    for i, s, j, t in equalities:
        a, b = gaps[i][s], gaps[j][t]
        if a is not None and b is not None and a != b:
            comparisons.append(dict(positions=[[i, s], [j, t]], gaps=[a, b], excluded_lengths_at_least=max(a, b)))
    certificate = []
    for length in range(1, n):
        if 1 in by_gap:
            certificate.append(dict(cycle_length=length, reason='forbidden_top_selection', event=by_gap[1]))
        elif length + 1 in by_gap:
            certificate.append(dict(cycle_length=length, reason='forbidden_first_return', event=by_gap[length + 1]))
        else:
            hit = next((c for c in comparisons if c['excluded_lengths_at_least'] <= length), None)
            certificate.append(dict(cycle_length=length, reason='different_forced_selections' if hit else 'not_excluded', comparison=hit))
    allowed = [L for L in range(1, n) if L + 1 not in by_gap and 1 not in by_gap]
    return dict(ciphertext_only_surviving_lengths=allowed,
                forced_alphabet_bounds=[dict(cycle_length=L, minimum_selection_alphabet=len([g for g in by_gap if g <= L]),
                                             distinct_forced_return_gaps=sorted(g for g in by_gap if g <= L)) for L in allowed],
                surviving_lengths=[r['cycle_length'] for r in certificate if r['reason'] == 'not_excluded'],
                certificate=certificate, return_events=len(returns), gap_comparisons=comparisons)


def physical(pt, key, pivot, shuffle):
    deck, ct = list(key), []
    for p in pt:
        assert p not in [0, pivot]
        deck[0], deck[p], deck[pivot] = deck[p], deck[pivot], deck[0]
        new = [None] * len(deck)
        for old, dest in enumerate(shuffle):
            new[dest] = deck[old]
        deck = new
        ct.append(deck[0])
    return ct


def controls():
    rng = random.Random(9072032)
    records = []
    short_checks = 0
    for n in [7, 19, 83]:
        for length in range(1, n):
            pivot = 1
            cycle = [pivot] + rng.sample(range(2, n), length - 1)
            remaining = sorted(set(range(1, n)) - set(cycle))
            shuffled = rng.sample(remaining, len(remaining))
            q = list(range(n))
            for x, y in zip(cycle, cycle[1:] + cycle[:1]):
                q[x] = y
            for x, y in zip(remaining, shuffled):
                q[x] = y
            pt = [[rng.randrange(2, n) for t in range(180)] for _ in range(3)]
            ct = [physical(row, rng.sample(range(n), n), pivot, q) for row in pt]
            returns, gaps = events(ct)
            for e in returns:
                assert e['gap'] != length + 1
                if e['gap'] <= length:
                    expected = pivot
                    for _ in range(e['gap'] - 1):
                        expected = q[expected]
                    assert pt[e['message']][e['current']] == expected
                    short_checks += 1
            groups = {}
            for mi, row in enumerate(pt):
                for t, p in enumerate(row):
                    groups.setdefault(p, []).append((mi, t))
            eq = [(*a, *b) for group in groups.values() for a, b in itertools.combinations(group, 2)]
            tested = analyze(ct, eq, n)
            assert length in tested['surviving_lengths']
            records.append(dict(n=n, planted_cycle_length=length, surviving_lengths=tested['surviving_lengths'],
                                return_events=len(returns)))
    return dict(generated_ciphers=len(records), messages_per_cipher=3, outputs_per_message=180,
                short_return_selection_checks=short_checks, records=records)


def run():
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
    return_events, _ = events(raw)
    compact = []
    for gap in range(2, 10):
        candidates = [e for e in return_events if e['gap'] == gap]
        if gap in [8, 9]:
            candidates = [e for e in candidates if e['message'] == 1 and e['current'] == (38 if gap == 8 else 68)]
        compact.append(candidates[0])
    tests = []
    for name, equality in [('E4_E5_bridge', [6, 64, 8, 65]), ('W1_repetition', [1, 38, 1, 68])]:
        result = analyze(raw, [equality])
        assert result['ciphertext_only_surviving_lengths'] == [36, 68, 73]
        assert result['surviving_lengths'] == []
        result.update(name=name, sole_plaintext_equality=equality)
        tests.append(result)
    header_audits = []
    for skip in [0, 1]:
        observed = analyze([row[skip:] for row in raw], [])
        assert observed['ciphertext_only_surviving_lengths'] == [36, 68, 73]
        assert [r['minimum_selection_alphabet'] for r in observed['forced_alphabet_bounds']] == [35, 66, 70]
        header_audits.append(dict(first_marker_omitted=bool(skip), surviving_cycle_lengths=observed['ciphertext_only_surviving_lengths'],
                                 forced_alphabet_bounds=observed['forced_alphabet_bounds']))
    # This is deliberately weaker than a physical-deck test. Record survival,
    # rather than promoting the necessary return relations to a decipherment.
    from permutation_action_fold import solve as fold
    _, gaps = events(raw)
    action_checks = []
    for length in [36, 68, 73]:
        pts = [[('gap', g) if g is not None and g <= length else ('fresh', mi, t)
                for t, g in enumerate(row)] for mi, row in enumerate(gaps)]
        for mi in list(range(9)) + [None]:
            result = fold(pts if mi is None else [pts[mi]], raw if mi is None else [raw[mi]], include_forced=True)
            groups = result.pop('forced_equal_operations', [])
            result['distinct_gap_operation_collision'] = any(sum(x[0] == 'gap' for x in group) > 1 for group in groups)
            result.update(cycle_length=length, message=mi, common_reset_assumed=mi is None)
            assert result['status'] == 'relaxation_survives' and not result['distinct_gap_operation_collision']
            action_checks.append(result)
    return dict(status='Fixed-pivot family needs at least 35 selection symbols from ciphertext alone; either stated plaintext equality excludes it entirely.',
                corpus_sha256=hashlib.sha256((ROOT / 'ciphertext.json').read_bytes()).hexdigest(),
                message_order=list(json.loads((ROOT / 'ciphertext.json').read_text())),
                indexing='Zero-based raw ciphertext; a gap is the distance from the immediately preceding occurrence of the same label in the same message.',
                tests=tests, controls=controls(), header_audits=header_audits, necessary_action_checks=action_checks,
                compact_W1_certificate=dict(first_return_events=compact, sole_plaintext_equality=[1, 38, 1, 68],
                                            explanation='Gaps 2..9 exclude cycle lengths 1..8; equal input selections at gaps 8 and 9 exclude every cycle length >=9.'),
                size_independent_alphabet_certificate=dict(
                    first_return_events=[next(e for e in return_events if e['gap'] == g) for g in range(2, 37)],
                    explanation='Gaps 2..36 exclude pivot cycles of lengths 1..35. Every longer pivot cycle forces 35 distinct input selections for these same gaps. This needs no upper bound on the number of distinctly labeled cards.'),
                scope='One common fixed pivot position and output-fixing shuffle; selections exclude top and pivot; arbitrary independent starting decks and any selection alphabet subset. Each test needs only its one stated plaintext-selection equality.',
                limitations=['Does not exclude nonconstant third-position rules, a special pivot-selection operation, moving output, message-specific shuffles, or different plaintext relationships.',
                             'The three candidate cycle lengths assume 83 cards. The compact W1 exclusion and 35-symbol lower bound extend to every finite distinctly labeled deck size.',
                             'The local relative-map SAT result is not contradicted: it omitted the long first-return histories.',
                             'No plaintext or historical key recovered.'])


if __name__ == '__main__':
    r = run()
    (ROOT / 'fixed_pivot_return_audit.json').write_text(json.dumps(r, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print(json.dumps(dict(status=r['status'], ciphertext_only_cycle_lengths=r['tests'][0]['ciphertext_only_surviving_lengths'],
                          exclusions=[dict(name=t['name'], comparison=t['gap_comparisons'], survivors=t['surviving_lengths']) for t in r['tests']],
                          generated_ciphers=r['controls']['generated_ciphers'], short_return_checks=r['controls']['short_return_selection_checks']), indent=2))
