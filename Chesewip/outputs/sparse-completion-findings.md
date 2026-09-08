# Completing partially recovered feedback keys

Executed 2026-09-08. **Unsolved: no authentic Eye plaintext or key recovered.**

The two-map method now recovers the correct feedback rule and an equivalent full key in the same three rich generated examples using 200 or 250 input-equality comparisons, instead of the previous 1,000. An independent exhaustive audit identifies why the nonlinear examples finish: the correct completion needs 27 input values, whereas the closest wrong completion needs at least 37 for squaring or 50 for inversion. This is a method calibration, not evidence that either rule generated the Eyes.

The repeated-passage budget is smaller, but the fitting corpus is unchanged: six generated messages supply 2,994 scored transitions. The Eye fitting set supplies 671. The generated examples were constructed to contain the assumed repeated inputs and all 27 input characters. These are three existing fixtures, not a random-seed success-rate study, and the block counts were selected after inspecting their ranks.

## Model and data boundaries

Continue the explicit family from [the preceding report](frozen-candidate-findings.md):

```text
rho(C[t]) = f(rho(C[t-1])) + code(P[t]) mod 83
f(x) = x, x^2, or inverse(x), with inverse(0) = 0
```

The output map rho is an unknown permutation of 0..82. The input codebook has at most 27 values. A raw message's first symbol is treated as metadata; its second symbol is an observed primer. Only raw positions t >= 2 are decoded. No numerical trigram labeling is assumed to be the internal key.

Discovery additionally requires the input codes to avoid `{x-f(x) : x in 0..82}`. This makes adjacent doubled outputs impossible for every input sequence, a stronger property than merely observing no doubles. The ablation below removes this additional restriction at the completion stage and obtains the same surviving keys.

Message order is E1, W1, E2, W2, E3, W3, E4, W4, E5. Only indices 0..5 enter candidate generation or selection; indices 6..8 and their late equalities are scored afterward. Earlier research has already inspected the later Eye messages, so this split is a model holdout rather than new unseen evidence.

Canonical ciphertext SHA-256: `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`. Corpus and passage hypotheses are unchanged. The Eye early comparisons are the four 15-position alignments in `state_memory_comparison.json` under `assumption_sets.early`; they are hypotheses about equal inputs, not established plaintext. No new guessed wording is introduced. Generated controls, true keys, initial states and codebooks are preserved in `lifted_feedback_recovery.json` (seeds 909850..909852); the Eye-length controls are in `frozen_candidate_search.json` (909800..909802). Each new result records its parent hashes.

## Partial linear recovery and completion

Represent equal-input comparisons by two independent maps r and s:

```text
r(Ca) - s(Ca-1) - r(Cb) + s(Cb-1) = 0 mod 83
```

Normalize two active output labels to 0 and 1 and one active feedback label to 0. Columns absent from these equations are temporarily fixed to zero solely to describe the active solution space; their actual label values are filled later. Save a particular solution and a complete basis of its free directions.

For at most two free parameters, enumerate every assignment over modulo 83, reject collisions among active output values, and test the three functions through all compatible scale/shift pairs. Addition has an affine key symmetry, so one representative is sufficient there. For a linked map with at most eight absent output labels, fill the missing values from unused residues. Feedback consistency, bijection, and residual codes on the fitting messages prune this completion search.

Candidates are sorted by rule name and key, with the first selected before held-out scoring. Neither the true key nor plaintext enters candidate generation. Known generated truth is used only in verification.

## Results on the richer fixtures

Each retained block contains a shared 10-input passage compared between message 0 and each of the other five fitting messages: 50 equality comparisons per block. Equality counts are not matrix ranks.

| Generated rule | Retained comparisons | Active free parameters | Output labels absent from equations | Parameter assignments enumerated | Complete candidates |
| --- | ---: | ---: | ---: | ---: | ---: |
| Addition | 250 | 0 | 2 | 1 | 1 affine representative |
| Squaring | 200 | 2 | 7 | 6,889 | 1 |
| Inversion | 200 | 1 | 7 | 83 | 2 sign-equivalent keys |

All selected candidates recover the correct rule and true key up to its stated symmetry. Each frozen codebook contains 27 values. All 447 held-out transitions per fixture remain inside it, and all 54 held-out pair comparisons agree. This recovers an internal rule and numbering on generated data; assigning code values to language characters is a separate step.

With only three blocks (150 comparisons), the normalized active dimensions are 7, 12 and 4 respectively. Those runs are outside the two-parameter budget; they were not excluded and no claim of a minimum sufficient passage count is made.

## What actually resolves the missing labels

The independent verifier enumerates every permutation of the missing values, rather than reproducing discovery's incremental pruning. After the active maps have been linked to a rule:

| Rule | Missing-value permutations | Survive feedback consistency | Survive only the <=27 cap | Survive only the global no-doubles code restriction | Survive both |
| --- | ---: | ---: | ---: | ---: | ---: |
| Addition | 2 | 1 | 1 | 1 | 1 |
| Squaring | 5,040 | 720 | 1 | 1 | 1 |
| Inversion, per sign | 5,040 | 5,040 | 1 | 1 | 1 |

Both last filters are applied to the feedback-consistent candidates. For addition, the final alphabet restriction adds nothing in this fixture. For the two nonlinear fixtures, either filter independently isolates the correct completion. Squaring's 719 wrong feedback-consistent completions need 37..77 residual values; inversion's 5,039 wrong completions per sign need 50..83. The correct completions need 27. Full size histograms are saved.

This shows that an alphabet bound can supply information missing from repeated-passage equations once most of the map is recovered. It does not establish that 27 is the correct Eye alphabet size, that the global no-doubles property holds for the historical cipher, or that the method scales to arbitrary unknown maps.

## Actual Eye data and short controls

The early Eye equation matrix still has rank 45 among 166 variables. It has 46 inactive output columns and 47 inactive feedback columns. Removing those inactive coordinates and fixing the three normalization freedoms leaves 25 active parameters, well beyond the current limit; the 46 missing output labels also exceed the completion budget of eight.

The earlier total nullity of 121 and the current active dimension of 25 describe the same equations: `121 - 93 inactive columns - 3 normalization freedoms = 25`. No new Eye information has reduced that nullity. The generated Eye-length controls likewise remain outside the limit, at dimensions 36, 36 and 42. There is no qualifying Eye candidate, and these skipped searches cannot reject any cipher family.

The next useful algorithmic step is to apply collision and residual-alphabet constraints before fully enumerating the active parameter space, with recovery on the short known-key controls as the acceptance test. Simply enlarging brute-force enumeration is not a practical route through this gap.

## Reproduction and scope of verification

From this directory, using Python 3.10 or newer:

```powershell
python sparse_map_completion.py
python verify_sparse_completion.py
```

Discovery requires NumPy. The verifier uses the standard library and independently written helpers in `verify_frozen_candidates.py`; it does not import the sparse discovery implementation. It reconstructs the equations, recomputes rank, checks that every saved affine basis is complete, exhaustively enumerates the bounded parameter spaces, verifies the exact lists of injective assignments and function links, and exhaustively checks every missing-label permutation. It reproduces all candidate records and held-out scores, confirms true-key equivalence, and re-encrypts 13,431 generated body symbols across the six source fixtures.

Artifacts: `sparse_map_completion.py`, `sparse_map_completion.json`, `verify_sparse_completion.py`, `checked_sparse_completion.json`. The latter contains the independent ablation counts and histograms. All checks passed. No project build was run.

This extends our preceding two-map experiment. Ciphertext feedback is already discussed in the community's [CTAK notes](https://github.com/Lymm37/eye-messages/wiki/Ciphertext%E2%80%90Autokey-%28CTAK%29); no claim of worldwide novelty is made for the family or general small-alphabet technique. The new contribution here is the reproducible bounded completion experiment and the measured separation between its true and wrong generated keys.
