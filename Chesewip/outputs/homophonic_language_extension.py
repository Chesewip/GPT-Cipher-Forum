"""One bounded restart extension after the initial language calibration.

Keep the original failed run. Each failed control receives 16 new random
restarts, for 20 total. If all controls pass, use the same total budget on
the eyes. No key hints or passage equalities are supplied.
"""
from pathlib import Path
import json
from homophonic_language_probe import attack, model

ROOT = Path(__file__).resolve().parent
baseline = json.loads((ROOT / 'homophonic_language_probe.json').read_text(encoding='utf-8'))
logp, frequencies = model()
out = dict(status='One bounded calibration extension; no exact exclusion.',
           baseline='homophonic_language_probe.json', additional_restarts_for_failed_controls=16,
           total_restart_budget=20, steps_per_restart=6000, controls=[], real=None,
           caveat='Restart budget was increased after seeing initial control failures. These reused controls are not a fresh blind validation set.')
path = ROOT / 'homophonic_language_extended.json'


def save():
    path.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')


for index, original in enumerate(baseline['controls']):
    entry = dict(index=index, baseline_recovery=original['recovery_fraction'], additional_search=None)
    if original['recovery_fraction'] < .95:
        r = attack(original['ciphertext'], logp, frequencies, seed=9072160 + index, restarts=16)
        truth = original['true_plaintext']
        hits = sum(a == b for aa, bb in zip(truth, r['plaintext_codes']) for a, b in zip(aa, bb))
        r.update(recovered_plaintext_symbols=hits, total_plaintext_symbols=sum(map(len, truth)),
                 recovery_fraction=hits / sum(map(len, truth)))
        entry['additional_search'] = r
        # Select by language score only; never pick a candidate by truth accuracy.
        winner = r if r['score'] > original['score'] else original
    else:
        winner = original
    entry['selected_recovery_fraction'] = winner['recovery_fraction']
    entry['selected_score'] = winner['score']
    out['controls'].append(entry)
    print('Selected control recovery:', index, entry['selected_recovery_fraction'], flush=True)
    save()
out['calibration_passed'] = all(r['selected_recovery_fraction'] >= .95 for r in out['controls'])
if out['calibration_passed']:
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text(encoding='utf-8')).values())
    out['real'] = attack([row[1:] for row in raw], logp, frequencies, seed=9072170, restarts=20)
else:
    out['real'] = dict(status='not_run_after_failed_calibration', reason='No further restart expansion is attempted in this bounded pass.')
save()
print('Final calibration:', out['calibration_passed'], 'real:', out['real']['status'], flush=True)
