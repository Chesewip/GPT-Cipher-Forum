"""Verify saved 32-prefix witnesses by physical deck replay, without SMT."""
from pathlib import Path
import json
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
ROOT = Path(__file__).resolve().parent


def physical_decode(messages, key, rotation):
    decoded = []
    for row in messages:
        deck = key.copy()
        pt = []
        for label in row:
            selected = deck.index(label)
            assert selected != 0
            pt.append(selected)
            neighbor = 1 + selected % 82
            old_top, old_selected, old_neighbor = deck[0], deck[selected], deck[neighbor]
            deck[0], deck[selected], deck[neighbor] = old_selected, old_neighbor, old_top
            if rotation:
                deck = [deck[0]] + deck[-rotation:] + deck[1:-rotation]
        decoded.append(pt)
    return decoded


def comparisons(pt, classes):
    seen = {}
    count = 0
    errors = 0
    for row, labels in zip(pt, classes):
        for p, label in zip(row, labels):
            if label in seen:
                count += 1
                errors += p != seen[label]
            else:
                seen[label] = p
    return count, errors


raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
classes = make_plaintexts(raw, assumptions(raw))
records = []
for name in ['context_entry_eyes32_b12_compact.json', 'context_entry_eyes32_b9_compact.json']:
    path = ROOT / name
    if not path.exists():
        continue
    result = json.loads(path.read_text())
    if result['status'] != 'sat':
        continue
    key, b = result['initial_deck'], result['rotation']
    assert sorted(key) == list(range(83))
    pt = physical_decode(raw, key, b)
    assert [row[:32] for row in pt] == result['plaintext_positions']
    prefix_count, prefix_errors = comparisons([row[:32] for row in pt], [row[:32] for row in classes])
    assert prefix_count == 124 and prefix_errors == 0
    full_count, full_errors = comparisons(pt, classes)
    assert full_count == 256
    compatible = []
    for rotation in range(82):
        decoded = physical_decode([row[:32] for row in raw], key, rotation)
        if comparisons(decoded, [row[:32] for row in classes])[1] == 0:
            compatible.append(rotation)
    records.append(dict(source=name, prefix_ciphertext_outputs=288, prefix_equalities_checked=prefix_count,
                        prefix_equality_errors=prefix_errors, full_corpus_equality_errors=full_errors,
                        full_corpus_equalities=full_count, compatible_rotations_for_this_key=compatible,
                        selected_positions_in_full_decode=len(set(p for row in pt for p in row))))
control_records = []
from adaptive_equality_search import fixture
control_ct, control_classes, planted_key, planted_pt = fixture()
for name in ['context_entry_control32_compact.json', 'context_entry_control40_extended.json']:
    path = ROOT / name
    if not path.exists():
        continue
    result = json.loads(path.read_text())
    if result['status'] != 'sat':
        continue
    length = result['output_lengths'][0]
    pt = physical_decode([row[:length] for row in control_ct], result['initial_deck'], result['rotation'])
    assert pt == result['plaintext_positions']
    count, errors = comparisons(pt, [row[:length] for row in control_classes])
    assert errors == 0
    control_records.append(dict(source=name, prefix_length=length, original_prefix_comparisons=count,
                                equality_errors=errors, exact_planted_plaintext_recovered=pt == [row[:length] for row in planted_pt]))
out = dict(status='verified_structural_prefix_witnesses', witnesses=records, generated_controls=control_records,
           scope='Verifies all 124 prefix comparisons from the original full-corpus equality closure, not merely the clipped passage list. The original plaintext assumptions remain conditional. These keys fail on the full corpus.')
(ROOT / 'checked_context_prefix_witnesses.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')
print(json.dumps(out, indent=2))
