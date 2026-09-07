"""Bounded English homophonic search with no passage-equality assumptions.

Train tetragrams on Pride and Prejudice; generated controls use separate
Sherlock Holmes text. Unknown keys are initialized without planted-key hints.
This is heuristic calibration, never a cipher-family exclusion.
"""
from pathlib import Path
import hashlib
import json
import re
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent / 'work'
ALPHABET = ' abcdefghijklmnopqrstuvwxyz'
POWERS = np.array([27 ** 3, 27 ** 2, 27, 1], dtype=np.int64)


def clean(path):
    text = path.read_text(encoding='utf-8-sig')
    start = re.search(r'\*\*\* START OF .*?\*\*\*', text)
    end = re.search(r'\*\*\* END OF .*?\*\*\*', text)
    text = text[start.end() if start else 0:end.start() if end else len(text)]
    return re.sub('[^a-z]+', ' ', text.lower()).strip()


def encode(text):
    return np.array([ALPHABET.index(c) for c in text], dtype=np.int64)


def model():
    chars = encode(clean(WORK / 'pg1342.txt'))
    ids = sum(chars[k:len(chars) - 3 + k] * POWERS[k] for k in range(4))
    counts = np.bincount(ids, minlength=27 ** 4)
    logp = np.log((counts + 0.01) / (len(ids) + 0.01 * 27 ** 4))
    frequencies = np.bincount(chars, minlength=27).astype(float)
    frequencies /= frequencies.sum()
    return logp, frequencies


def attack(messages, logp, frequencies, seed, restarts=4, steps=6000):
    start = time.monotonic()
    grams = np.array([row[t:t + 4] for row in messages for t in range(len(row) - 3)], dtype=np.int64)
    effects = []
    for c in range(83):
        weights = ((grams == c) * POWERS[None, :]).sum(axis=1)
        indices = np.flatnonzero(weights)
        effects.append((indices, weights[indices]))
    rng = np.random.default_rng(seed)
    best, restart_results = None, []
    initial_probabilities = np.sqrt(frequencies)
    initial_probabilities /= initial_probabilities.sum()
    for restart in range(restarts):
        key = rng.choice(27, size=83, p=initial_probabilities)
        ids = (key[grams] * POWERS[None, :]).sum(axis=1)
        score = float(logp[ids].sum())
        local = dict(score=score, key=key.copy(), step=0)
        for step in range(steps + 83 * 6):
            c = int(rng.integers(83)) if step < steps else (step - steps) % 83
            positions, weights = effects[c]
            if not len(positions):
                continue
            old = int(key[c])
            candidates = ids[positions][None, :] + (np.arange(27) - old)[:, None] * weights[None, :]
            scores = logp[candidates].sum(axis=1)
            if step < steps:
                temperature = 0.25 + 9.75 * (1 - step / steps) ** 2
                chosen = int(np.argmax(scores + temperature * rng.gumbel(size=27)))
            else:
                chosen = int(np.argmax(scores))
            score += float(scores[chosen] - scores[old])
            ids[positions] = candidates[chosen]
            key[c] = chosen
            if score > local['score']:
                local = dict(score=score, key=key.copy(), step=step)
            if step % 1000 == 0:
                assert abs(score - float(logp[ids].sum())) < 1e-6
        assert abs(local['score'] - float(logp[(local['key'][grams] * POWERS[None, :]).sum(axis=1)].sum())) < 1e-6
        restart_results.append(dict(restart=restart, score=local['score'], best_step=local['step']))
        if best is None or local['score'] > best['score']:
            best = local
        print('seed', seed, 'restart', restart, 'best score', round(best['score'], 1), flush=True)
    decoded = [[int(best['key'][c]) for c in row] for row in messages]
    return dict(status='unverified_language_candidate', alphabet=ALPHABET, ciphertext_to_plaintext=best['key'].tolist(),
                plaintext_codes=decoded, candidate_text=[''.join(ALPHABET[x] for x in row) for row in decoded],
                score=best['score'], mean_tetragram_log_score=best['score'] / len(grams),
                scored_tetragrams=len(grams), seed=seed, restarts=restarts, steps_per_restart=steps,
                greedy_sweeps_per_restart=6, restart_results=restart_results, seconds=time.monotonic() - start)


def fixture(lengths, frequencies, seed):
    rng = np.random.default_rng(seed)
    text = clean(WORK / 'pg1661.txt')
    counts = np.ones(27, dtype=int)
    extra = frequencies * (83 - 27)
    counts += np.floor(extra).astype(int)
    for c in np.argsort(-(extra - np.floor(extra)))[:83 - counts.sum()]:
        counts[c] += 1
    shuffled = rng.permutation(83)
    groups, owner, offset = [], np.zeros(83, dtype=int), 0
    for p, count in enumerate(counts):
        group = shuffled[offset:offset + count].tolist()
        groups.append(group)
        for c in group:
            owner[c] = p
        offset += count
    cts, pts, starts = [], [], []
    for i, length in enumerate(lengths):
        start = 10000 + i * 20000 + (seed % 7000)
        assert start + length < len(text)
        pt = encode(text[start:start + length]).tolist()
        ct = []
        for p in pt:
            choices = [c for c in groups[p] if not ct or c != ct[-1]]
            if not choices:
                choices = groups[p]
            ct.append(int(rng.choice(choices)))
        pts.append(pt); cts.append(ct); starts.append(start)
    return cts, pts, owner, starts


if __name__ == '__main__':
    logp, frequencies = model()
    raw = list(json.loads((ROOT / 'ciphertext.json').read_text(encoding='utf-8')).values())
    body = [row[1:] for row in raw]
    out = dict(status='Bounded heuristic probe; no decipherment or exact exclusion.',
               training_source='Project Gutenberg 1342, Pride and Prejudice',
               training_sha256=hashlib.sha256((WORK / 'pg1342.txt').read_bytes()).hexdigest(),
               control_plaintext_source='Project Gutenberg 1661, The Adventures of Sherlock Holmes',
               control_source_sha256=hashlib.sha256((WORK / 'pg1661.txt').read_bytes()).hexdigest(),
               assumed_language='English letters and spaces, 27 symbols',
               calibration_gate='Each of three independent unknown-key controls must recover at least 95 percent of plaintext before interpreting a negative real search.',
               controls=[], real=None)
    path = ROOT / 'homophonic_language_probe.json'
    def save():
        path.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8', newline='\r\n')
    for index in range(3):
        ct, truth, key, starts = fixture(list(map(len, body)), frequencies, 9072050 + index)
        r = attack(ct, logp, frequencies, seed=9072060 + index)
        hits = sum(a == b for aa, bb in zip(truth, r['plaintext_codes']) for a, b in zip(aa, bb))
        r.update(ciphertext=ct, true_plaintext=truth, planted_key=key.tolist(), source_offsets=starts,
                 recovered_plaintext_symbols=hits, total_plaintext_symbols=sum(map(len, truth)),
                 recovery_fraction=hits / sum(map(len, truth)))
        out['controls'].append(r)
        print('Control recovery:', index, r['recovery_fraction'], flush=True)
        save()
    out['calibration_passed'] = all(r['recovery_fraction'] >= .95 for r in out['controls'])
    if out['calibration_passed']:
        out['real'] = attack(body, logp, frequencies, seed=9072070, restarts=8)
    else:
        out['real'] = dict(status='not_run_after_failed_calibration',
                           reason='The bounded unknown-key method failed its generated recovery gate. No real-cipher conclusion is inferred.')
    save()
    print('Calibration passed:', out['calibration_passed'], 'real status:', out['real']['status'], flush=True)
