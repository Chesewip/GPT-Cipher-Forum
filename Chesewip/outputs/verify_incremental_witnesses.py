"""Independent physical replay of all saved fits from this incremental search batch."""
from pathlib import Path
import json
from shared_update_support import assumptions
from permutation_action_fold import make_plaintexts
ROOT = Path(__file__).resolve().parent


def physical_decode(ct, key, b):
    result = []
    for message in ct:
        deck = key.copy()
        plaintext = []
        for c in message:
            position = deck.index(c)
            assert position > 0
            plaintext.append(position)
            neighbor = position + 1 if position < 82 else 1
            a, selected, tail = deck[0], deck[position], deck[neighbor]
            deck[0], deck[position], deck[neighbor] = selected, tail, a
            if b:
                bottom = deck[1:]
                deck[1:] = bottom[-b:] + bottom[:-b]
        result.append(plaintext)
    return result


def count_errors(pt, classes, limit=None):
    seen = {}
    errors = 0
    comparisons = 0
    for row, labels in zip(pt, classes):
        for p, label in zip(row[:limit], labels[:limit]):
            if label in seen:
                comparisons += 1
                errors += p != seen[label]
            else:
                seen[label] = p
    return comparisons, errors


raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
classes = make_plaintexts(raw, assumptions(raw))
sources = ['incremental_eyes40_bv.json', 'incremental_eyes40_fd.json', 'incremental_eyes40_int.json',
           'incremental_eyes40_simplified_bv.json', 'direct_eyes40_simplified_bv.json',
           'direct_eyes40_simplified_fd.json', 'core_repair_eyes40.json',
           'core_repair_eyes40_least_seen.json', 'incremental_eyes40_bv_extended.json',
           'direct_eyes40_lazy.json', 'core_repair_control40.json', 'incremental_control40_bv.json']
records = []
for name in sources:
    path = ROOT / name
    if not path.exists():
        continue
    source = json.loads(path.read_text())
    if source.get('control'):
        from adaptive_equality_search import fixture
        ct, cls, key, truept = fixture()
    else:
        ct, cls, truept = raw, classes, None
    stages = source.get('stages', [source])
    for index, stage in enumerate(stages):
        if stage['status'] not in ['sat', 'structural_model_fit']:
            continue
        length = stage.get('prefix_length', stage.get('output_lengths', [0])[0])
        key = stage['initial_deck']
        assert sorted(key) == list(range(83))
        b = source['rotation']
        pt = physical_decode(ct, key, b)
        assert [row[:length] for row in pt] == stage['plaintext_positions']
        comparisons, errors = count_errors(pt, cls, length)
        assert errors == 0, (name, length, errors)
        full_count, full_errors = count_errors(pt, cls)
        assert full_count == 256
        records.append(dict(source=name, stage=index, control=bool(source.get('control')),
                            prefix_length=length, ciphertext_outputs=9 * length,
                            original_equality_comparisons=comparisons, prefix_errors=errors,
                            full_corpus_errors=full_errors, full_corpus_comparisons=full_count,
                            full_plaintext_support=len(set(p for row in pt for p in row)),
                            exact_planted_prefix_recovered=[row[:length] for row in pt] == [row[:length] for row in truept] if truept else None))
out = dict(status='verified', witnesses=records,
           warning='Exact structural fits under the stated equality assumptions. Full-corpus failures and generated controls are reported separately. No authenticated plaintext.')
(ROOT / 'checked_incremental_witnesses.json').write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')
print(json.dumps(out, indent=2))
