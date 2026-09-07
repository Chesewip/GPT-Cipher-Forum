"""Independent checks of finite scans, equality certificates, and saved scores."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
import re
import numpy as np

ROOT = Path(__file__).resolve().parent
raw_bytes = (ROOT / 'ciphertext.json').read_bytes()
raw = list(json.loads(raw_bytes).values())
saved = json.loads((ROOT / 'nondeck_screen.json').read_text(encoding='utf-8'))
assert hashlib.sha256(raw_bytes).hexdigest() == saved['corpus_sha256']
assumptions = saved['assumption_sets']
within, cross, late = [assumptions[k] for k in ['within_message', 'earlier_cross_message', 'late_family']]
stages = dict(within_only=within, earlier_contexts=within + cross, with_late_family=within + cross + late,
              without_short_E1=within[:2] + cross + late, late_only=late,
              all_registered=within + cross + late)
numeric_checks = 0
numeric_summary = []
for record in saved['numeric']:
    data = []
    for row in raw:
        if record['family'] == 'feedback2':
            data.extend((row[t], row[t - 1], row[t - 2]) for t in range(3, len(row)))
        else:
            assert record['family'] == 'drift_header'
            data.extend((row[t], t - 1, row[0]) for t in range(1, len(row)))
    data = np.array(data)
    y, x, z = data.T
    modulus = record['modulus']
    observed = []
    for a, b in itertools.product(range(modulus), repeat=2):
        values = np.unique((y - a * x - b * z) % modulus)
        observed.append(len(values))
        numeric_checks += 1
    assert observed == record['supports_in_a_major_b_minor_order']
    assert min(observed) == record['best']['selection_support']
    assert record['coefficient_pairs'] == modulus ** 2 and record['compared_outputs'] == len(y)
    numeric_summary.append(dict(family=record['family'], modulus=modulus, minimum_support=min(observed)))


def component_sets(nodes, edges):
    adjacency = defaultdict(set)
    for a, b in edges:
        adjacency[a].add(b); adjacency[b].add(a)
    unseen = set(nodes)
    result = []
    while unseen:
        todo = [unseen.pop()]
        component = set(todo)
        while todo:
            for y in adjacency[todo.pop()]:
                if y in unseen:
                    unseen.remove(y); component.add(y); todo.append(y)
        result.append(component)
    return result


table_checks = 0
certificate_paths = 0
for group in saved['periodic'] + [dict(stage=r['stage'], results=[r]) for r in saved['absolute_position']]:
    eq = stages[group['stage']]
    allowed_pairs = {tuple(sorted(((i, s + k), (j, t + k)))) for i, s, j, t, length in eq for k in range(length)}
    for record in group['results']:
        q = record['period']
        independent = record['independent_message_tables']
        def node(i, t):
            return (i if independent else -1, (t - 1) % q, raw[i][t])
        nodes = {node(i, t) for i, row in enumerate(raw) for t in range(1, len(row))}
        edges = [(node(i, s + k), node(j, t + k)) for i, s, j, t, length in eq for k in range(length)]
        components = component_sets(nodes, edges)
        conflict = any(len({x[:2] for x in c}) != len(c) for c in components)
        assert conflict == (record['status'] == 'inconsistent')
        assert max(Counter(x[:2] for x in nodes).values()) == record['maximum_observed_symbols_in_one_table']
        if conflict:
            start, end = map(tuple, record['collision_nodes'])
            assert start[:2] == end[:2] and start[2] != end[2]
            previous = start
            for step in record['equality_path']:
                a, b = tuple(step['from_node']), tuple(step['to_node'])
                assert a == previous
                positions = [tuple(p) for p in step['equal_input_positions']]
                assert tuple(sorted(positions)) in allowed_pairs
                assert {node(*p) for p in positions} == {a, b}
                previous = b
            assert previous == end
            certificate_paths += 1
        table_checks += 1

homophonic_summary = []
for record in saved['homophonic']:
    eq = stages[record['stage']]
    counts = Counter(c for row in raw for c in row[1:])
    edges = [(raw[i][s + k], raw[j][t + k]) for i, s, j, t, length in eq for k in range(length)]
    components = component_sets(counts, edges)
    assert {frozenset(c) for c in components} == {frozenset(r['ciphertext_labels']) for r in record['components']}
    largest = max(sum(counts[c] for c in group) for group in components)
    assert len(components) == record['maximum_distinct_plaintext_symbols']
    assert largest == record['largest_forced_symbol_count'] and sum(counts.values()) == record['body_outputs']
    homophonic_summary.append(dict(stage=record['stage'], maximum_plaintext_symbols=len(components),
                                  largest_forced_fraction=largest / sum(counts.values())))


def corpus_text(path):
    text = path.read_text(encoding='utf-8-sig')
    start = re.search(r'\*\*\* START OF .*?\*\*\*', text)
    end = re.search(r'\*\*\* END OF .*?\*\*\*', text)
    return ' '.join(re.findall('[a-z]+', text[start.end():end.start()].lower()))


alphabet = ' abcdefghijklmnopqrstuvwxyz'
training = corpus_text(ROOT.parent / 'work/pg1342.txt')
control_text = corpus_text(ROOT.parent / 'work/pg1661.txt')
ngram_counts = Counter(training[t:t + 4] for t in range(len(training) - 3))
denominator = len(training) - 3 + .01 * 27 ** 4
baseline = json.loads((ROOT / 'homophonic_language_probe.json').read_text(encoding='utf-8'))
extension = json.loads((ROOT / 'homophonic_language_extended.json').read_text(encoding='utf-8'))
candidate_checks = 0


def check_candidate(record, ct):
    global candidate_checks
    key = record['ciphertext_to_plaintext']
    assert len(key) == 83 and all(0 <= x < 27 for x in key)
    decoded = [[key[c] for c in row] for row in ct]
    assert decoded == record['plaintext_codes']
    text = [''.join(alphabet[x] for x in row) for row in decoded]
    assert text == record['candidate_text']
    score, terms = 0.0, 0
    for row in text:
        for t in range(len(row) - 3):
            score += math.log((ngram_counts[row[t:t + 4]] + .01) / denominator)
            terms += 1
    assert abs(score - record['score']) < 1e-5
    assert terms == record['scored_tetragrams']
    assert abs(score / terms - record['mean_tetragram_log_score']) < 1e-8
    assert abs(max(r['score'] for r in record['restart_results']) - score) < 1e-5
    candidate_checks += 1


recoveries = []
for index, base in enumerate(baseline['controls']):
    for start, truth in zip(base['source_offsets'], base['true_plaintext']):
        assert ''.join(alphabet[x] for x in truth) == control_text[start:start + len(truth)]
    assert [[base['planted_key'][c] for c in row] for row in base['ciphertext']] == base['true_plaintext']
    records = [base]
    extra = extension['controls'][index]['additional_search']
    if extra:
        records.append(extra)
    for record in records:
        check_candidate(record, base['ciphertext'])
        hits = sum(x == y for a, b in zip(record['plaintext_codes'], base['true_plaintext']) for x, y in zip(a, b))
        assert hits == record['recovered_plaintext_symbols']
        assert abs(hits / sum(map(len, base['true_plaintext'])) - record['recovery_fraction']) < 1e-12
    winner = max(records, key=lambda r: r['score'])
    assert winner['recovery_fraction'] == extension['controls'][index]['selected_recovery_fraction']
    recoveries.append(winner['recovery_fraction'])
assert extension['calibration_passed'] == all(r >= .95 for r in recoveries)
check_candidate(extension['real'], [row[1:] for row in raw])
out = dict(status='verified; cipher remains unsolved', numeric_coefficient_pairs_checked=numeric_checks,
           numeric_results=numeric_summary, table_closure_checks=table_checks, explicit_collision_paths_checked=certificate_paths,
           homophonic_components=homophonic_summary, saved_language_candidates_redecoded_and_rescored=candidate_checks,
           generated_plaintext_recoveries=recoveries, real_mean_tetragram_log_score=extension['real']['mean_tetragram_log_score'],
           scope='Exact finite-family exclusions remain within the stated representations and plaintext assumptions. The language search is a bounded English heuristic, not an impossibility proof.')
(ROOT / 'checked_nondeck_screen.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')
print(json.dumps(out, indent=2))
