# Frozen feedback candidates and nonlinear key-recovery controls

Executed: 2026-09-08. Contributor: Chesewip.

**No Eye plaintext or qualifying Eye candidate was found.** This pass moves from exclusions to generating explicit keys. A direct permutation search fails blind controls and therefore supplies no useful family exclusion. A second method, solving for separate output and feedback maps before linking them to an explicit rule, recovers the correct rule and compatible key in three richer generated examples. Their held-out messages pass the frozen codebooks and repeated-input checks.

The real early Eye assumptions leave that second method underdetermined: rank 45 in 166 map variables. This is a working recovery route on sufficiently informative controls, not evidence of an imminent Eye solution.

## Three explicit rules and a fixed split

Let rho be an unknown permutation from the 83 output labels to residues modulo 83. Test

```text
rho(C[t]) = f(rho(C[t-1])) + code(P[t])  (mod 83),
```

with f(x) equal to x, x squared, or the inverse of x modulo 83, defining f(0)=0 for the inverse case. These are three variants of one feedback architecture, not an exhaustive comparison of stateful ciphers. The community already documents ciphertext-autokey mechanisms and distinguishes arbitrary feedback tables from the usual running sum; see [Ciphertext-Autokey](https://github.com/Lymm37/eye-messages/wiki/Ciphertext%E2%80%90Autokey-%28CTAK%29), consulted 2026-09-08. No claim of inventing the architecture is made.

Each candidate uses at most 27 input-code values. For this pilot, require the stronger design property that adjacent outputs are impossible for every input sequence. A code value must therefore avoid `{x-f(x): x in Z/83Z}`. This leaves 82 allowed values for addition, 41 for squaring, and 42 for inversion. The observed absence of doubles does not prove this global property; it is an explicit restriction of the candidates tested here.

Retain the canonical three-eye grouping and treat the resulting labels as arbitrary identifiers. Fit only E1, W1, E2, W2, E3, and W3. Reserve E4, W4, and E5 for evaluation after selecting a key and codebook. The first raw symbol is ignored; the first body symbol supplies an observed predecessor for decoding at raw position 2 onward. There are 671 fitting transitions and 347 held-out transitions in the Eye corpus. This does not recover the first body input or an authentic initial state.

The early equality hypotheses are W1:37=W1:67, E2:42=E2:77, W1:37=E2:42, and W1:37=E2:77, each for 15 inputs. Held-out comparisons are E4:71=W4:74 and E4:71=E5:72, each for 27 inputs. Positions are zero-based raw indices. Equality of those real inputs remains unproved. All messages have been inspected in earlier research; this is a holdout from fitting, not newly obtained blind evidence.

## First method: bounded permutation search

For each rule, search an unknown 83-label permutation. A key determines input residues on the fitting transitions. Its codebook is the 27 most frequent allowed residues, with numeric order breaking frequency ties. Minimize

```text
number of fitting residues outside the codebook
  + weight * number of failed early input comparisons.
```

Run with weight 0, which does not use passage agreement to choose a key, and weight 3, which encourages agreement but allows errors. Each blind run has four random-permutation restarts, 6,000 annealed swap proposals per restart, and one deterministic pass over all 3,403 label swaps. Select the restart solely by fitting energy, keeping the earliest tied restart. The key and codebook are frozen before evaluating later messages. No language score or attractive quotation is used.

The three initial generated controls have the Eye lengths, 27 encoded characters from cleaned Sherlock Holmes text, and the same early/late equality layout. All 27 characters are explicitly placed in the fitting split so an unobserved rare character cannot cause a codebook failure. Their keys, input codes, and initial states are hidden from the blind search. A separate repair run starts from the true key damaged by two swaps; it must not be described as blind recovery.

| Generated rule / seed | Repair fitting energy | Repair held-out residues outside codebook | Blind fitting energy | Blind held-out residues outside codebook |
| --- | ---: | ---: | ---: | ---: |
| Addition / 909800 | 4 | 5 | 307 | 175 |
| Squaring / 909801 | 4 | 4 | 268 | 188 |
| Inversion / 909802 | 0 | 0 | 357 | 200 |

The two incomplete repair keys match 81 of the 83 planted entries; inversion repairs all 83. Every planted true key has fitting energy zero. All blind searches fail the generated controls. Thus poor Eye results from this optimizer cannot exclude the mechanisms.

| Eye rule | Equality weight | Fitting residues outside codebook / 671 | Held-out residues outside frozen codebook / 347 | Failed late comparisons / 54 |
| --- | ---: | ---: | ---: | ---: |
| Addition | 0 | 198 | 237 | 54 |
| Addition | 3 | 228 | 222 | 54 |
| Squaring | 0 | 217 | 215 | 54 |
| Squaring | 3 | 236 | 239 | 54 |
| Inversion | 0 | 201 | 228 | 51 |
| Inversion | 3 | 227 | 228 | 53 |

None passes even the fitting codebook requirement. The few agreeing late comparisons in the inversion runs are not a recovered passage or grounds for selecting that mechanism. All candidate permutations, initial permutations, restart results, codebooks, and decoded residue streams are retained.

## Second method: separate two unknown maps, then identify the rule

Introduce an output map r(label) and a feedback map s(label). Equal input tokens require

```text
r(C[a]) - s(C[a-1]) - r(C[b]) + s(C[b-1]) = 0.
```

These equations are linear in 166 unknown values, even when the true feedback rule is nonlinear. The relation `s(label)=f(r(label))` is deliberately postponed. If the linear system identifies both maps up to their shared scale and two independent origins, normalize output labels 0 and 1 to 0 and 1 and feedback label 0 to 0.

Then test all three rules against the normalized maps u,v. Enumerate nonzero scale A and shift B, requiring

```text
f(A*u(label)+B) - A*v(label) = f(B)
```

at every known feedback entry. There are 82*83=6,806 parameter pairs per rule. The smallest surviving pair in the fixed enumeration selects the key; held-out data is not used to choose it. The codebook is then read from the fitting transitions and frozen.

The richer controls contain six 500-input fitting messages and three 150-input held-out messages. Twenty separate ten-input words are shared across the fitting messages, with unrelated input between them. This supplies 1,000 training equality comparisons. The held-out messages share a different 27-input passage. These controls are substantially longer and more redundant than the real Eye evidence; that difference is essential to interpreting their success.

| True rule / seed | Linear rank | Surviving parameter pairs: add / square / inverse | Recovered map | Held-out outside codebook / 447 | Failed late comparisons / 54 |
| --- | ---: | --- | --- | ---: | ---: |
| Addition / 909850 | 163 | 6806 / 0 / 0 | True map up to affine scale/origin | 0 | 0 |
| Squaring / 909851 | 161 | 0 / 1 / 0 | Exact true map after the completion below | 0 | 0 |
| Inversion / 909852 | 163 | 0 / 0 / 2 | True map up to sign | 0 | 0 |

The corresponding frozen codebooks each contain 27 values. The equivalences in the table explain the multiple parameter pairs; they are not thousands of unrelated discoveries. The algorithm tests all three rules rather than receiving the true rule as a selector.

### Retained initial failure and one-label completion

The initial squaring control is underdetermined at rank 161 and is preserved that way in `lifted_feedback_recovery.json`. Its equality rows contain no information about output label 26 or the feedback-map entry for label 26. The remaining 164 active variables have exactly three dimensions of freedom.

Normalize the active maps as above. The 82 known output values are distinct, so bijectivity determines the single missing output value as the unused residue. Leave the missing feedback value unspecified while testing the three explicit rules. Squaring is the sole match and fixes that feedback value as well. `lifted_feedback_completion.json` records this follow-up, including the unchanged addition and inversion checks. This completion uses training information and the bijection requirement, not held-out observations.

The Eye early equations have rank 45 and nullity 121, so neither the direct unique-map solve nor this one-label completion applies. That underdetermination is not an exclusion of any of the three rules. The direct permutation search above was the bounded attempt to use the additional codebook restriction, and its calibration was inadequate.

## Independent checks and reproduction

`verify_frozen_candidates.py` imports no discovery implementation. It uses the standard library to recompute training scores and deterministic codebooks, check training-only restart selection, evaluate the frozen keys on held-out messages, independently compute linear ranks, check normalized map uniqueness, enumerate the linking-rule parameter pairs, and compare recovered keys with planted keys under their exact equivalences. It re-encrypts 13,431 generated body symbols across the six fixtures. All checks passed.

From this output directory:

```powershell
python frozen_candidate_search.py
python lifted_feedback_recovery.py
python lifted_feedback_recovery.py --complete
python verify_frozen_candidates.py
```

Discovery requires NumPy and the existing text-cleaning helper in `homophonic_language_probe.py`. Control text is the already archived Project Gutenberg Sherlock Holmes file, `../work/pg1661.txt`, with its original license and provenance retained. No additional language model is trained. Blind-search seeds are 909811, 909813, 909815 for the short controls and 909830 through 909835 for the Eyes; repair seeds are 909810, 909812, 909814. Fixture seeds are in the tables. No project build is run.

Files: the two discovery scripts and their three JSON results, `verify_frozen_candidates.py`, `checked_frozen_candidates.json`, and this report. The checked JSON records hashes of the canonical ciphertext, assumption parent, and all three result files. Each discovery result also records the control-text hash. The canonical ciphertext hash remains `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`.

The useful result is a calibrated way to generate nonlinear feedback keys when enough repeated-input information is available. The next challenge is making candidate recovery work with sparse or imperfect repetition, or finding a different source of constraints. These results do not justify promoting any of the three tested rules to a leading explanation of the Eye cipher.
