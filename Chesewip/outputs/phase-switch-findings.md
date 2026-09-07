# A local obstruction to the three-card deck route

**Unsolved. No authentic plaintext or full-corpus key recovered.**

The unit-neighbor three-card model cannot satisfy two specified East 4 / East 5 repeated-plaintext alignments simultaneously. The result allows arbitrary keys, arbitrary independent deck states on entering the passages, every rotation, and unconstrained plaintext outside the two alignments. It also extends to an arbitrary injective rule for choosing the third position and an arbitrary common fixed bottom shuffle.

This is a conditional exclusion, not an unconditional elimination of deck ciphers. The additional assumption is that the documented bridge and late isomorph both represent repeated plaintext, after leaving their first three input positions unconstrained. Equality patterns alone do not establish that assumption.

The consequence for our research is concrete: if we accept these two plaintext interpretations, we should stop extending the unit-neighbor key search. If we retain that model, at least one of these local plaintext interpretations must change. Its earlier 34-symbol prefix fits remain valid for their older constraints and do not resolve this conflict.

## Inputs and prior work

The adjacent bridge and late-phase patterns are previously reported in [mvelzel/eye-vibe's synchronizing-bridge analysis](https://github.com/mvelzel/eye-vibe/blob/main/docs/thirty-second-synchronizing-bridge-results-2026-07-26.md). This pass independently reconstructs their maps from our existing ciphertext, then applies our earlier relative-entry-change method and a backward implication specific to this update family. It does not claim discovery of the bridge, globally novel mathematics, or independent replication of the source's statistical controls and broader interpretation.

All positions below are **zero-based raw ciphertext**, including the initial marker in the indexing. Ranges are end-exclusive. An output at raw position t is emitted by input t.

| Region | East 4 outputs | East 5 outputs | Paired outputs | Distinct map entries |
| --- | --- | --- | ---: | ---: |
| Bridge | [48,68) | [49,69) | 20 | 16 |
| Late passage | [68,98) | [69,99) | 30 | 25 |

Both windows have matching equality signatures. Their concatenation does not: the first late pair conflicts with the bridge's map. Among all 49 possible single cuts in this 50-output window, only the cut at 20 leaves valid partial bijections on both sides.

The precise plaintext assumptions used for the stronger exclusion are only:

| Assumed equal input selections | East 4 | East 5 | Length |
| --- | --- | --- | ---: |
| Bridge interior | [51,68) | [52,69) | 17 |
| Late interior | [71,98) | [72,99) | 27 |

These are input relations, not direct readings of the ciphertext. No other message, common reset, numbered header, language, or alphabet-size assumption is used.

## The relative map and the five-entry limit

For two decks D and E, let R map the label at each position of D to the label at that same position of E. R is a permutation of the 83 labels. The paired top outputs force one observed entry of R.

Equal input selections apply identical positional updates to both decks and leave R unchanged. For the tested family, selecting non-top position p cycles the top, p, and a third position f(p). The third-position rule is fixed, avoids p, and is injective on the permitted selections. A common fixed shuffle of the bottom positions may follow.

Different selections touch at most five positions between them: the top plus two selected/third-position pairs. Therefore one differing input changes at most five entries of R. Unknown keys and the common shuffle cannot increase this support.

For the full bridge and late maps, every pair of complete permutation extensions differs on at least **nine** entries. The bound is exact: the result file includes two full permutation extensions differing on exactly nine entries. Those extensions are mathematical map witnesses, not cipher keys or proven reachable states.

A small subcertificate already exceeds five. In the bridge and late maps respectively:

| East 4 source label | Bridge East 5 target | Late East 5 target |
| ---: | ---: | ---: |
| 75 | 48 | 42 |
| 79 | 19 | 9 |
| 26 | 54 | 73 |

For example, changing the image of source 75 from 48 to 42 forces both inverse-map entries 48 and 42 to change. The six target labels in this table are distinct, so at least six inverse entries change. A permutation and its inverse have the same Hamming distance. Six paired observations already rule out a single five-entry transition; the complete maps require nine.

## Why leaving the first three inputs free does not save this model

The trimmed input assumptions force R to be constant on bridge outputs [50,68) and late outputs [70,98). These reduced maps still require **seven** changed entries. At first glance there are three available transitions between them, so a five-entry-per-transition bound alone would not exclude the model.

The old top card goes to position f(p), then through the common bottom shuffle. Because both functions are injective, the previous two top cards occupy corresponding positions after an update **if and only if the two selections were equal**. In that case, the relative map is unchanged. This lets an already established map propagate backward when it contains the preceding output pair.

Apply this twice to the late map:

1. At East 4 raw output 70, the previous output pair is `(57,6)`. That pair appears again at East 4 raw 95 / East 5 raw 96, so it belongs to the established late map. The input selections at raw 70 / 71 must therefore be equal, extending the same map back to raw 69 / 70.
2. The preceding pair is `(79,9)`, repeated at East 4 raw 86 / East 5 raw 87. The same argument extends the map back to raw 68 / 69.

Only one transition now remains between the bridge's final map and the forced late map: East 4 raw 67 to 68, paired with East 5 raw 68 to 69. That transition can change at most five entries, but the maps force seven. Contradiction.

Even the shortened maps contain three disjoint source-image changes, using source labels **79, 26, and 78**, with targets `(19,9)`, `(54,73)`, and `(75,70)`. These supply a six-entry subcertificate that survives the trimming.

If three or more leading **outputs** of each phase are discarded, this backward argument no longer closes the gap: the next preceding pair is not fixed by a later repetition. Those looser assumptions remain unresolved by this proof. Discarding two leading outputs corresponds here to leaving three leading inputs unconstrained; keeping input/output indexing distinct matters.

## What remains possible

The exclusion includes every fixed nonzero cyclic neighbor offset, not just offset 1, and every common fixed bottom permutation, not just rotations. It does not cover noninjective third-position rules, larger updates, differing per-message update rules, moving-output models, or different plaintext relationships.

Within the fixed anchored-three-cycle class, dropping injectivity gives a more specific escape condition: at least one of the two backward steps must use different selections that send the old top to the same third position. Otherwise both backward implications still hold and the contradiction returns. This is a necessary condition for that alternative, not an identified mechanism.

Separately, the prior ciphertext-only row-bound method requires at least two differing inputs somewhere among the 49 internal transitions of this 50-output window for any model whose relative map changes at most five entries per differing input. That weaker bound assumes neither passage is repeated plaintext. It does not prove two differences are sufficient.

All five saved prefix witnesses audited here disagree at every one of these 50 aligned selections. They fit their recorded prefix constraints but supply no positive prediction for this region.

## Verification and reproduction

- Exact completion distances matched exhaustive permutation-completion searches on all 1,156 pairs of partial bijections at size 3, plus 400 sampled partial-map pairs each at sizes 4 and 5.
- 240 generated physical-deck message pairs with one or two changed inputs, arbitrary independent entry decks and rotations passed the change bounds.
- A separate verifier checked 6,948 physical update-pair cases, including all 82 squared selection pairs at size 83 and all rotations at the tested smaller sizes.
- Another 1,920 checks used arbitrary injective third-position rules and arbitrary common bottom shuffles.
- The verifier reconstructs the seven- and nine-entry certificates directly, checks the full permutation completions, and verifies the exact repeated output pairs used in the backward argument. It does not import the discovery analyzer or use SMT.

Run directly, with NumPy available for the discovery checks:

```powershell
python phase_switch_audit.py
python verify_phase_switch_audit.py
```

The second command uses only the Python standard library. Results are saved in `phase_switch_audit.json` and `checked_phase_switch_audit.json`. No project build was run. This is an independently checked local obstruction and a reason to revise the next search, not a decipherment.
