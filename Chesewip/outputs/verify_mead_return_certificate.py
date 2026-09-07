"""Check the E3 NO return contradiction without graph folding or SMT.

Each character has a fixed position permutation U_p. A plaintext word w has
one fixed composite U_w. Reading position zero before and after w in an
arbitrary bijective deck D yields equal labels iff U_w(0)=0. The equality
therefore cannot depend on the surrounding plaintext or starting deck.
"""
from pathlib import Path
import itertools, json
import numpy as np
ROOT = Path(__file__).resolve().parent


def repeated_word_returns(pt, ct, max_length=10):
    seen = {}
    contradictions = []
    for length in range(1, max_length + 1):
        for start in range(1, len(pt) - length + 1):
            word = pt[start:start + length]
            returned = ct[start - 1] == ct[start + length - 1]
            observation = (start, start + length - 1, returned)
            if word in seen and seen[word][2] != returned:
                contradictions.append(dict(word=word, first=seen[word], second=observation))
            else:
                seen.setdefault(word, observation)
    return contradictions


audit = json.loads((ROOT / 'mead_candidate_audit.json').read_text())
raw = list(json.loads((ROOT / 'ciphertext.json').read_text()).values())
pt, ct = audit['candidate_texts']['E3'], raw[4][1:]
pairs = [(6,8),(26,28)]
assert pt[7:9] == pt[27:29] == 'NO'
assert [ct[i] for pair in pairs for i in pair] == [60,40,13,13]
assert ct[6] != ct[8] and ct[26] == ct[28]
certificate = dict(plaintext_block='NO', body_positions_one_based_before_after=[[7,9],[27,29]],
                   ciphertext_before_after=[[60,40],[13,13]],
                   outcome='Impossible under fixed per-character permutations of positions and a fixed output position.',
                   invariance='The contradiction uses only label equality, so arbitrary ciphertext relabeling cannot remove it.',
                   scope='Arbitrary initial state and arbitrary bijective per-character updates. Does not cover every cipher described as stateful, deck-based, feedback-based or time-dependent.')
# Exhaustive small controls: all pairs of update permutations and all possible
# starting decks. A given two-character word must have a constant return flag.
checks = 0
for n in [3,4]:
    permutations = list(itertools.permutations(range(n)))
    for u, v in itertools.product(permutations, repeat=2):
        flags = set()
        for deck in permutations:
            after_u = [deck[u[i]] for i in range(n)]
            after_v = [after_u[v[i]] for i in range(n)]
            flags.add(deck[0] == after_v[0])
            checks += 1
        assert len(flags) == 1
# Full-size generated permutations test the observed-return rule on streams.
rng = np.random.default_rng(20261130)
full_size_checks = 0
for _ in range(100):
    alphabet = 'ABCDE'
    updates = {letter:rng.permutation(83).tolist() for letter in alphabet}
    plaintext = ''.join(rng.choice(list(alphabet), size=160))
    deck = rng.permutation(83).tolist()
    ciphertext = []
    for letter in plaintext:
        deck = [deck[i] for i in updates[letter]]
        ciphertext.append(deck[0])
    assert not repeated_word_returns(plaintext, ciphertext, 6)
    full_size_checks += 1
out = dict(certificate=certificate, exhaustive_two_update_deck_checks=checks,
           generated_83_card_stream_checks=full_size_checks,
           E3_return_contradictions=repeated_word_returns(pt,ct),
           E4_return_contradictions=repeated_word_returns(audit['candidate_texts']['E4'],raw[6][1:]))
assert out['E3_return_contradictions'] and not out['E4_return_contradictions']
(ROOT / 'checked_mead_return_certificate.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['E3_return_contradictions','E4_return_contradictions']},indent=2))
