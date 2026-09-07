"""Bounded comparison of feedback, periodic substitution, and homophony.

Numeric scans use published trigram values as arithmetic coordinates. Table
and homophone tests use only symbol equality. No deck mechanisms are tested.
"""
from pathlib import Path
from collections import Counter, defaultdict, deque
import hashlib
import itertools
import json
import random
import numpy as np

ROOT = Path(__file__).resolve().parent
WITHIN = [(1, 37, 1, 67, 15), (2, 42, 2, 77, 15), (0, 43, 0, 71, 6)]
CROSS = [(1, 37, 2, 42, 15), (1, 37, 2, 77, 15)]
LATE = [(6, 71, 7, 74, 27), (6, 71, 8, 72, 27)]


def features(messages, family):
    y, x1, x2 = [], [], []
    for row in messages:
        if family == 'feedback2':
            # Header and two body initialization symbols impose no constraints.
            for t in range(3, len(row)):
                y.append(row[t]); x1.append(row[t - 1]); x2.append(row[t - 2])
        elif family == 'drift_header':
            for t in range(1, len(row)):
                y.append(row[t]); x1.append(t - 1); x2.append(row[0])
        else:
            raise ValueError(family)
    return tuple(np.asarray(v, dtype=np.int64) for v in [y, x1, x2])


def numeric(messages, family, modulus):
    y, x1, x2 = features(messages, family)
    supports = []
    best = None
    for a in range(modulus):
        b = np.arange(modulus, dtype=np.int64)
        decoded = (y[None, :] - a * x1[None, :] - b[:, None] * x2[None, :]) % modulus
        histogram = np.bincount((decoded + modulus * b[:, None]).ravel(),
                                minlength=modulus * modulus).reshape(modulus, modulus)
        row = (histogram > 0).sum(axis=1).tolist()
        supports.extend(row)
        choice = int(np.argmin(row))
        if best is None or row[choice] < best['selection_support']:
            best = dict(a=a, b=choice, selection_support=row[choice],
                        residual_counts=histogram[choice].tolist())
    return dict(family=family, modulus=modulus, compared_outputs=len(y),
                coefficient_pairs=modulus * modulus, best=best,
                support_histogram=dict(sorted(Counter(supports).items())),
                supports_in_a_major_b_minor_order=supports,
                scope='Arbitrary fixed plaintext-to-residue substitution and common additive offset allowed. Arbitrary nonlinear ciphertext relabeling and message-specific persistent offsets are not covered.')


class Union:
    def __init__(self, nodes):
        self.parent = {x: x for x in nodes}
        self.adj = defaultdict(list)

    def root(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def merge(self, a, b, evidence):
        self.adj[a].append((b, evidence))
        self.adj[b].append((a, evidence))
        ra, rb = self.root(a), self.root(b)
        if ra != rb:
            self.parent[ra] = rb

    def path(self, start, finish):
        queue, seen = deque([start]), {start: None}
        while queue:
            x = queue.popleft()
            if x == finish:
                break
            for y, evidence in self.adj[x]:
                if y not in seen:
                    seen[y] = (x, evidence)
                    queue.append(y)
        assert finish in seen
        result = []
        x = finish
        while seen[x] is not None:
            previous, evidence = seen[x]
            result.append(dict(from_node=previous, to_node=x, equal_input_positions=evidence))
            x = previous
        return result[::-1]


def periodic(messages, equalities, period, independent_tables=False):
    def node(i, t):
        phase = (t - 1) % period
        return (i if independent_tables else -1, phase, messages[i][t])
    nodes = {node(i, t) for i, row in enumerate(messages) for t in range(1, len(row))}
    u = Union(nodes)
    for i, s, j, t, length in equalities:
        for k in range(length):
            u.merge(node(i, s + k), node(j, t + k), [[i, s + k], [j, t + k]])
    seen = {}
    collision = None
    for x in sorted(nodes):
        key = (u.root(x), x[:2])
        if key in seen and seen[key] != x:
            collision = (seen[key], x)
            break
        seen[key] = x
    per_table = Counter(x[:2] for x in nodes)
    out = dict(period=period, independent_message_tables=independent_tables,
               observed_nodes=len(nodes), maximum_observed_symbols_in_one_table=max(per_table.values()),
               status='inconsistent' if collision else 'closure_survives')
    if collision:
        out['collision_nodes'] = collision
        out['equality_path'] = u.path(*collision)
    else:
        out['equality_components'] = len({u.root(x) for x in nodes})
    return out


def homophonic(messages, equalities):
    nodes = set(c for row in messages for c in row[1:])
    u = Union(nodes)
    for i, s, j, t, length in equalities:
        for k in range(length):
            u.merge(messages[i][s + k], messages[j][t + k], [[i, s + k], [j, t + k]])
    groups = defaultdict(list)
    for c in sorted(nodes):
        groups[u.root(c)].append(c)
    frequency = Counter(c for row in messages for c in row[1:])
    components = sorted([dict(ciphertext_labels=v, output_count=sum(frequency[c] for c in v))
                         for v in groups.values()], key=lambda x: (-x['output_count'], x['ciphertext_labels']))
    return dict(maximum_distinct_plaintext_symbols=len(components),
                largest_forced_symbol_count=components[0]['output_count'],
                body_outputs=sum(frequency.values()), components=components,
                scope='Fixed deterministic ciphertext-label-to-plaintext-symbol map; multiple ciphertext labels per plaintext symbol allowed. Components may merge further; no actual letters are assigned.')


def plaintext_fixture(messages, equalities, alphabet, rng):
    nodes = [(i, t) for i, row in enumerate(messages) for t in range(len(row))]
    u = Union(nodes)
    for i, s, j, t, length in equalities:
        for k in range(length):
            u.merge((i, s + k), (j, t + k), None)
    values = {r: rng.randrange(alphabet) for r in sorted({u.root(x) for x in nodes})}
    return [[values[u.root((i, t))] for t in range(len(row))] for i, row in enumerate(messages)]


def controls(raw):
    rng = random.Random(9072040)
    arithmetic = []
    for modulus in [83, 125]:
        for family in ['feedback2', 'drift_header']:
            a, b = (17, 29) if family == 'feedback2' else (7, 11)
            alphabet = rng.sample(range(modulus), 27)
            ct, truth = [], []
            for _ in range(5):
                header = rng.randrange(modulus)
                if family == 'feedback2':
                    row = [header, rng.randrange(modulus), rng.randrange(modulus)]
                    pt = [rng.choice(alphabet) for t in range(118)]
                    for p in pt:
                        row.append((p + a * row[-1] + b * row[-2]) % modulus)
                else:
                    pt = [rng.choice(alphabet) for t in range(120)]
                    row = [header] + [(p + a * t + b * header) % modulus for t, p in enumerate(pt)]
                ct.append(row); truth.extend(pt)
            result = numeric(ct, family, modulus)
            y, x1, x2 = features(ct, family)
            assert ((y - a * x1 - b * x2) % modulus).tolist() == truth
            assert result['supports_in_a_major_b_minor_order'][a * modulus + b] == 27
            assert result['best']['selection_support'] <= 27
            arithmetic.append(dict(family=family, modulus=modulus, planted_coefficients=[a, b],
                                   planted_residuals_exactly_recovered=True, minimum_support=result['best']['selection_support']))
    table_checks = []
    eq = WITHIN + CROSS + LATE
    for period in [1, 2, 7, 13, 31, 47, max(map(len, raw))]:
        pt = plaintext_fixture(raw, eq, 27, rng)
        tables = [rng.sample(range(83), 27) for _ in range(period)]
        ct = [[rng.randrange(83)] + [tables[(t - 1) % period][p] for t, p in enumerate(row) if t > 0] for row in pt]
        for independent in [False, True]:
            tested = periodic(ct, eq, period, independent)
            assert tested['status'] == 'closure_survives'
            assert tested['maximum_observed_symbols_in_one_table'] <= 27
            table_checks.append(dict(period=period, independent_message_tables=independent, planted_period_survives=True))
    homophone_checks = []
    for trial in range(10):
        pt = plaintext_fixture(raw, eq, 27, rng)
        symbols = rng.sample(range(83), 83)
        groups = [symbols[k::27] for k in range(27)]
        owner = {c: p for p, cs in enumerate(groups) for c in cs}
        ct = [[rng.choice(groups[p]) for p in row] for row in pt]
        tested = homophonic(ct, eq)
        assert all(len({owner[c] for c in component['ciphertext_labels']}) == 1 for component in tested['components'])
        assert tested['maximum_distinct_plaintext_symbols'] >= 27
        homophone_checks.append(dict(trial=trial, no_distinct_plaintext_symbols_forced_together=True))
    return dict(arithmetic=arithmetic, periodic_tables=table_checks, homophonic=homophone_checks)


if __name__ == '__main__':
    source = (ROOT / 'ciphertext.json').read_bytes()
    raw = list(json.loads(source).values())
    out = dict(status='Non-deck family screening; no plaintext recovered.', corpus_sha256=hashlib.sha256(source).hexdigest(),
               numeric=[], periodic=[], homophonic=[],
               assumption_sets=dict(within_message=WITHIN, earlier_cross_message=CROSS, late_family=LATE),
               caveat='Late-family constraints are withheld from earlier fitting stages, but were already known to the investigator. This is a model holdout, not fresh blind data.')
    for family, modulus in itertools.product(['feedback2', 'drift_header'], [83, 125]):
        r = numeric(raw, family, modulus)
        out['numeric'].append(r)
        print('Numeric:', family, modulus, r['best'], flush=True)
    stages = [('within_only', WITHIN), ('earlier_contexts', WITHIN + CROSS), ('with_late_family', WITHIN + CROSS + LATE),
              ('without_short_E1', WITHIN[:2] + CROSS + LATE), ('late_only', LATE)]
    for name, eq in stages:
        h = homophonic(raw, eq)
        h['stage'] = name
        out['homophonic'].append(h)
        print('Homophonic:', name, h['maximum_distinct_plaintext_symbols'], h['largest_forced_symbol_count'], flush=True)
        for independent in [False, True]:
            results = [periodic(raw, eq, period, independent) for period in range(1, 65)]
            out['periodic'].append(dict(stage=name, independent_message_tables=independent, results=results))
            print('Periodic:', name, independent, 'survivors', [r['period'] for r in results if r['status'] == 'closure_survives'], flush=True)
    out['controls'] = controls(raw)
    out['absolute_position'] = []
    for name, eq in [('all_registered', WITHIN + CROSS + LATE), ('without_short_E1', WITHIN[:2] + CROSS + LATE)]:
        result = periodic(raw, eq, max(map(len, raw)))
        result.update(stage=name, interpretation='An independent bijective table at every absolute body position, shared across messages; no periodicity restriction.')
        out['absolute_position'].append(result)
    assert out['absolute_position'][0]['status'] == 'inconsistent'
    assert out['absolute_position'][1]['status'] == 'closure_survives'
    (ROOT / 'nondeck_screen.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    print('Controls passed; saved nondeck_screen.json', flush=True)
