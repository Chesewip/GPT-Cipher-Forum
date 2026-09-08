# Combining passage and alphabet deductions

Executed 2026-09-08. **Unsolved: no Eye key or plaintext recovered.**

The combined method recovers the complete squaring and inversion keys on the existing short generated examples with 27 supplied key entries. At that same starting point, alphabet-only propagation stalled at 27 fixed entries; passage-only propagation reaches 47 and 56 respectively. Together they reach all 83 entries and pass every held-out check. The additive fixture still stalls.

Blind recovery remains unsuccessful. The combined root propagation makes no useful deductions without key pins beyond additive symmetry normalization. Three extended depth-first searches, each limited to 30 seconds or 20,000 nodes, find no key. This is a stronger completion method on controlled partial-key examples, not evidence that a historical Eye key has been found or that the real cipher uses these rules.

## Exact scope

The tested functions and equation remain:

```text
rho(C[t]) = f(rho(C[t-1])) + code(P[t]) mod 83
f(x) = x, x^2, or inverse(x), with inverse(0) = 0
```

The function is supplied correctly for each control. The output map rho is a permutation of 0..82. At most 27 input code values may occur. No global no-doubles code restriction, language score or guessed word is used. Addition alone permits the affine normalization rho(0)=0, rho(1)=1. These two fixed values are symmetry choices, not supplied key knowledge; no corresponding normalization is imposed on the nonlinear rules.

Use the unchanged Eye-length fixtures in `frozen_candidate_search.json`, seeds 909800..909802. Only the first six messages and the four early 15-position input-equality alignments enter fitting: 671 scored transitions and 60 pair comparisons. The remaining three messages supply 347 held-out transitions and 54 late comparisons. Raw position 0 is treated as metadata, position 1 as an observed primer, and decoding starts at position 2. The late messages do not enter the search, branching order or candidate selection.

The generated early equalities are true by construction. Their analogues in the real Eyes remain hypotheses about plaintext. The canonical corpus is unchanged, SHA-256 `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`. New files hash their exact source and parent artifacts. This round does not run an Eye search because blind calibration still fails.

## How the combination works

An equal-input comparison yields a linear row in separate output and feedback values:

```text
r(Ca) - s(Ca-1) - r(Cb) + s(Cb-1) = 0 mod 83
```

Compute a reduced row basis, saving a modular linear-combination certificate for each derived row. For addition, substitute s=r before elimination. For the nonlinear rules, keep the two maps during elimination and then impose s(j)=f(r(j)) in each row's domain test.

Every row becomes a sum of terms `a_j*x_j + b_j*f(x_j) = 0 mod 83`. For each possible value of one label, compute the possible contribution sums of the other labels. Delete the value if no sum can complete the row. Combining both coefficients for a repeated label avoids treating its occurrences as independent variables.

Alternate these row deductions with permutation constraints and the local alphabet-cap deduction from [the previous experiment](joint-feedback-findings.md): trying a label value determines residues on edges to already fixed neighbors, and it is impossible if those residues require more than 27 input values. Each deletion in the saved root and assisted runs carries a replayable reason. All these deductions are necessary conditions; a stalled domain state is not a complete cipher solution.

This implementation uses the permutation and alphabet-cap filters that sufficed in the earlier successful partial-key runs. It does not include the earlier optional edge-support filter. Modular sums use 83-bit sets for speed, with independent verification using ordinary sets of residues.

## Blind runs

The search starts with no true-key pins. It propagates, branches on the smallest remaining domain, breaks ties by equation/transition degree and then label, and tries values in increasing order. The function is still supplied. Every branch propagates the combined constraints anew.

| Supplied function | Fixed entries after root propagation | Initial 120-node pilot | Extended nodes visited | Extended result |
| --- | ---: | --- | ---: | --- |
| Addition | 2, from normalization | Budget exhausted | 17,342 | 30-second budget exhausted |
| Squaring | 0 | Budget exhausted | 1,979 | 30-second budget exhausted |
| Inversion | 0 | Budget exhausted | 3,094 | 30-second budget exhausted |

The nonlinear root domains remain entirely unrestricted. The additive root only removes its two normalized values from other labels. Thus this local propagation provides no initial numerical foothold in these blind fixtures. The extended searches visit 22,415 nodes in total but find no complete candidate. Node and time limits are both explicit; the older 120-node results are retained separately.

These are bounded failures, not exclusions, impossibility proofs or a fair benchmark against every alternative encoding. Search metadata includes maximum singleton counts encountered, including contradictory nodes; those counts are not partial keys or evidence of proximity to the planted key.

## Assisted comparison at exactly the old 27-pin masks

For diagnosis, take precisely the nested hiding orders saved in `joint_feedback_constraints.json`, seeds 909880..909882. Hide their first 56 labels and supply the remaining 27 entries of canonical generated truth. No new favorable mask is selected. These are explicitly truth-assisted runs, separate from the blind searches.

| Function | Entries fixed initially | Alphabet only, previous round | Passages only | Passages plus alphabet |
| --- | ---: | ---: | ---: | ---: |
| Addition | 29, including normalization | 29 | 29 | 29 |
| Squaring | 27 | 27 | 47 | **83** |
| Inversion | 27 | 27 | 56 | **83** |

The final nonlinear keys match their planted truth exactly. Each inferred fitting codebook contains 27 values. All 347 held-out transitions remain in the frozen codebook, and all 54 held-out pair comparisons agree. These are recoveries of generated internal keys and residues; mapping residues to language is not being claimed as a new decipherment.

The independently replayed deletion counts make the interaction visible:

| Combined run | Permutation deletions | Passage-row deletions | Alphabet-cap deletions |
| --- | ---: | ---: | ---: |
| Addition | 1,566 | 93 | 163 |
| Squaring | 1,940 | 869 | 1,783 |
| Inversion | 1,808 | 744 | 2,040 |

The two nonlinear runs remove all 4,592 initially possible wrong values on their 56 unpinned labels. The passage-only and combined passes have different deduction orders, so these counts are not additive measures of independent information. Twenty-seven pins is a tested sufficient point for these two masks, not a claimed minimum or a success rate across random masks.

## What this changes

The requested combination works as an assisted completion mechanism: each constraint source supplies deductions the other can use. It has not yet established a blind starting point, even with the correct function supplied. A future attack needs stronger deductions or a better search over the initially broad maps; merely treating a large number of branch assignments as progress toward a key would be misleading.

The original Eye cipher remains unclassified by this round. In particular, success on constructed squaring and inversion examples is not a reason to favor either as the historical mechanism. No global novelty is claimed for modular constraint propagation or alphabet bounds; the contribution is the reproducible combination and its calibrated limits on these fixtures.

## Reproduction and independent checks

All new scripts use Python 3.10+ and the standard library. From this directory:

```powershell
python passage_domain_search.py
python passage_domain_search.py --extend
python verify_passage_domains.py
```

The extension hashes the first result file; run the commands in that order. Actual timed-search node counts vary across machines, so preserve this dated output when rerunning. Discovery never reads true keys for its blind search; truth is used later only for the explicitly marked assisted diagnostic and verification.

The independent verifier imports none of the new search code. It reconstructs the original rows, verifies every saved linear-combination certificate, independently recomputes ranks, and replays every saved domain deletion using ordinary modular sets. It confirms that no true key value is deleted in the positive controls, checks recovered keys directly, reproduces held-out scores and re-encrypts all 3,081 generated body symbols. Ranks are 37 for the additive single-map system and 28 and 45 for the two nonlinear lifted systems. Failed-search metadata is consistency-checked, not turned into an independent exclusion certificate.

All checks passed. Artifacts: `passage_domain_search.py`, `passage_domain_search.json`, `passage_domain_extended.json`, `verify_passage_domains.py`, `checked_passage_domains.json`. Earlier unsuccessful and assisted results remain intact. No project build was run.
