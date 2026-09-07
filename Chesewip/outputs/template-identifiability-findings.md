# Exact difference templates and the limits of unrestricted deck fits

**The Noita eye cipher remains unsolved. No meaningful plaintext, historical key, or predictive decoder has been recovered.**

This continuation strengthens the previous plaintext-difference results and checks the repeated-passage assumptions against a broader permutation model. Its strongest new local result is an exact classification of the minimum-difference templates for the first 50 East1/West1 symbols. Novelty across the entire community has not been established.

## 1. Exactly 18 minimum-difference templates

Use the published 83-symbol transcription, align East1 and West1 by symbol index, and assume:

- both messages start from the same deck;
- each plaintext symbol selects one fixed permutation of deck positions;
- the output is the card at one fixed position after that update;
- outputs identify the plaintext symbol uniquely when the current deck is known.

The last requirement means different plaintext symbols must draw their output cards from different positions of the preceding deck. The first ciphertext symbol is treated as an encrypted input, rather than external metadata.

The earlier interval argument proves that the first 50 plaintext positions must differ at least three times. If they differ **exactly three times**, the complete set of possible placements is:

| Difference | Position in the message, counting from 1 |
|---|---|
| First | 1 |
| Second | 24, 25, or 26 |
| Third | 29, 30, 31, 32, 33, or 34 |

Every combination in this table is realizable: 3 times 6 gives exactly **18 templates**. These are possible positions under a minimum-difference assumption, not recovered edits in the actual plaintext.

### Why one previously possible position disappears

While the plaintext updates agree, the correspondence between the two decks' card labels stays fixed. Suppose a proposed difference occurs at a ciphertext pair already seen during that interval. The two output cards then occupy the same source position in the preceding decks. Reversibility requires the same plaintext symbol at that position, contradicting the proposed difference.

This eliminates position 23 as the second difference. The earlier conflict-interval bound alone did not eliminate it.

### Sufficiency, rather than just a necessary filter

For every surviving template, `compact_template_witnesses.py` constructs an explicit common key and one fixed permutation per artificial plaintext symbol. Each construction reproduces the two real 50-symbol prefixes exactly with **22 or 23 symbols**. All output source positions are distinct and non-top, ensuring reversibility and forbidding adjacent output repeats for any input.

The independent verifier enumerates all 1,176 pairs of possible body cuts, finds exactly these 18, and replays every witness using a separate permutation implementation. The hidden decks remain different at every observed position.

These plaintexts are artificial token runs. An ordinary-sized alphabet does not make them meaningful language.

## 2. The nine-difference bound is also attainable over 99 symbols

A second construction reproduces all 99 East1 symbols and the first 99 of West1's 103 symbols. It uses **30 artificial plaintext symbols** and differs at exactly these nine positions, counting from 1:

`1, 26, 34, 51, 60, 69, 74, 79, 90`

The preceding general interval bound was nine. This explicit witness proves that bound is sharp for this pair and length in the unrestricted model above, with an alphabet of at most 30. It does not establish the smallest possible alphabet.

`verify_compact_99.py` independently checks the common key, every permutation, distinct non-top output sources, all 198 outputs, and the nine differences. The longest repeated artificial token run has length 13. The hidden decks differ at every position; their minimum difference in occupied card positions is 59.

That last observation is deliberately constructed, not a probability calculation. Even widely differing decks can emit matching runs when their operations and inputs are selected to fit the observations.

**Interpretation:** exact replay, a modest alphabet, and few plaintext differences are insufficient evidence for a decryption when the letter permutations are unrestricted. These constructions are mathematical counterexamples, not proposed Noita keys. They do not use the constrained common-shuffle/three-cycle mechanism previously investigated, and they do not fit all nine messages.

## 3. A broader consistency test for the repeated passages

I implemented an inverse-prefix permutation graph test. For each observed card, reverse the plaintext update sequence and trace the inverse updates from the output position into the initial deck. Repeated ciphertext labels require the same endpoint. Each plaintext operation must be an invertible function, so coinciding path sources force coinciding targets and vice versa. Repeatedly merge these forced coincidences. A merger of endpoints carrying different observed card labels is an exact contradiction.

This is a partial permutation graph method, not a newly identified cipher. The community documentation already connects GAK chaining graphs with Schreier coset graphs: [Noita research document](https://docs.google.com/document/d/1XMNXktCoSabnFWZf9rJFoaKMzsA1bbv7x1Xh9tXkKYk/edit).

I tested the ten previously listed repeated-passage hypotheses, trimming the first one, two, or three positions, both with and without the shared-prefix hypothesis. **All six variants survive this necessary test.** Adding the reversible-output implication forces no further plaintext equalities in the three shared-prefix variants.

This is an inconclusive result for an 83-card cipher. For example, the one-position-trimmed, shared-prefix case leaves 36,435 graph vertices and 780 unconsolidated plaintext classes. Those vertices are not proved to require distinct deck positions, and those classes are not proved to be distinct letters. A finite 83-position realization would require further identifications; this test neither finds nor excludes them.

Validation includes 150 generated valid permutation-cipher fixtures, 60 partially masked reversible fixtures, and 300 comparisons with an independently implemented slow partition-refinement algorithm. The latter agrees on 242 contradictions and 58 surviving relaxations.

## 4. Waite quotation lead checked and closed for this model

The public eye-vibe research already rejects its exact 81-character Waite/East2 alignment under fixed-output GAK through a short fixed-point contradiction. I independently reproduced that contradiction from our transcription and also detected it with the new graph test. This is confirmation of their result, not a new exclusion. Their separate variable-output-position model admits the quotation but also admits a deliberately wrong continuation, so that fit supplies no authenticated plaintext. Sources: [fixed-output result](https://github.com/mvelzel/eye-vibe/blob/main/docs/waite-sparse-gak-results-2026-07-27.md), [variable-output result](https://github.com/mvelzel/eye-vibe/blob/main/docs/waite-sparse-xgak-results-2026-07-27.md).

## Reproduction and next discriminating test

No build step is used. From the extracted bundle directory:

```powershell
python compact_template_witnesses.py
python verify_compact_templates.py
python compact_99_witness.py
python verify_compact_99.py
python permutation_action_fold.py
python reversible_action_fold.py
python verify_action_fold.py
```

The useful next target is a constrained operation family or independently justified crib that predicts observations excluded from fitting. The current artificial witnesses make that requirement concrete: unrestricted permutations have enough freedom to imitate substantial real structure. The small-shuffle hypothesis remains open, and the previous stronger difference bounds for that family still apply.
