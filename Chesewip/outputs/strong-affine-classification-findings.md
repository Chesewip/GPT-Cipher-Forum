# Affine exclusion with stronger passage assumptions

**Unsolved. No plaintext or full cipher key recovered.**

The previous six-edge obstruction used a short West 2 / West 3 alignment. This continuation independently reproduces an affine exclusion using only three stronger, previously published context maps. It also resolves the difference between four apparent linear survivors and three actual injective embeddings for the two last-family maps.

The staged affine-exclusion strategy is prior work, published in [mvelzel/eye-vibe](https://github.com/mvelzel/eye-vibe/blob/main/scripts/prove_c82_combined_contexts.py). This pass supplies an independent implementation, directly verifiable row-combination certificates, and an explicit classification of the remaining two-context cases. It does not claim the first affine-family exclusion.

## The stronger inputs

These contexts are specified in the public [isomorph-embedding test](https://github.com/mvelzel/eye-vibe/blob/main/scripts/test_affine_isomorph_embedding.py). We discard the first two ciphertext positions of each alignment before constructing the maps.

| Context | Retained source ciphertext | Retained target ciphertext | Retained symbols |
|---|---|---|---:|
| A | East 4, positions 71–98 | West 4, positions 74–101 | 28 |
| B | East 4, positions 71–98 | East 5, positions 72–99 | 28 |
| C | West 1, positions 37–52 | West 1, positions 67–82 | 16 |

Positions count from **1**. Each row is assumed to induce one context permutation. Under the affine GAK interpretation, this follows if the inputs between those observed outputs are repeated plaintext. These plaintext assumptions remain unverified. No common body prefix, numbered header, short West 2 / West 3 passage, language, or small alphabet is used in this proof.

## Exact arithmetic, with arbitrary secret symbol coordinates

Let f assign the 83 ciphertext labels bijectively to coordinates in F83. For each context, require:

`f(target) = multiplier * f(source) + offset (mod 83)`.

Multipliers range over 1 through 82. Both offsets and all symbol coordinates are unknown. A common affine change of coordinates permits normalization to `f(3)=0` and `f(22)=1`, without changing the multipliers or losing any valid embedding.

For fixed multipliers, these are linear equations over F83. A case is rejected only when the equations are inconsistent or force two distinct ciphertext labels to share a coordinate. Every rejection has a stored modular linear combination of the original equations proving the contradiction.

The two last-family maps A and B give:

| Outcome | Multiplier pairs |
|---|---:|
| Inconsistent linear equations | 6,565 |
| Forced collision of two symbol coordinates | 155 |
| Not excluded by the linear test | 4 |
| Total | 6,724 |

The four remaining pairs are `(4,24)`, `(42,30)`, `(45,7)`, and `(52,32)`.

This stage alone does not certify a one-to-one coordinate assignment. A linear solution can still collide for every possible value of its free parameters.

## Four linear survivors become three actual embeddings

For each surviving pair, elimination leaves five independent coordinate components. Instead of continuing an SMT search, each component's 83 possible parameter values can be enumerated directly. The resulting sets of occupied coordinates must be disjoint from the fixed coordinates and from one another.

This produces the complete classification:

| Multipliers for A and B | Actual bijective embedding? | Offsets under the stated normalization |
|---|---|---|
| `(4,24)` | Yes; explicit 83-label coordinate permutation saved | `(1,22)` |
| `(42,30)` | Yes; explicit 83-label coordinate permutation saved | `(1,63)` |
| `(45,7)` | Yes; explicit 83-label coordinate permutation saved | `(1,55)` |
| `(52,32)` | No; all 83 values of one component force a collision | — |

The first three are real embeddings of the **two partial context maps**. They are not full-message cipher keys or plaintexts.

For `(52,32)`, write `q=f(57)`. The equations force:

```text
f(5)  = 52q + 1
f(6)  = 32q + 25
f(7)  =  7q + 26
f(10) = 58q + 27
f(19) = 43q + 45
f(56) = 12q + 20
f(57) = q
```

All arithmetic is modulo 83. There are also 31 fixed symbol coordinates. For every possible q, two different symbols among these fixed and moving coordinates collide. The certificate contains all 83 collisions and modular row proofs for the 38 coordinate equations used. Thus this fourth case is excluded without assuming that the free coordinates are generic or relying on a timeout.

## The West 1 repetition rejects the remaining cases

Add context C. For each of the three genuinely viable A/B pairs, 81 possible C multipliers are inconsistent. The one remaining multiplier forces a coordinate collision:

| A multiplier | B multiplier | Remaining C multiplier | Forced contradiction |
|---:|---:|---:|---|
| 4 | 24 | 67 | `f(31) = f(20)` |
| 42 | 30 | 5 | `f(38) = f(10)` |
| 45 | 7 | 45 | `f(36) = f(34)` |

Different ciphertext labels must have different coordinates. None of these is an affine embedding.

The original staged linear certificate also rejects all extensions of the fourth A/B pair, so the full three-context exclusion has two consistent verification routes. There are 7,048 directly checked exclusion certificates, collectively covering all **551,368 multiplier triples**.

Therefore the affine state family cannot explain these three context maps under a common arbitrary relabeling. Unlike the preceding short proof, this result does not require the 14-symbol West 2 / West 3 alignment. It remains conditional on the stronger passages actually being repeated plaintext.

## Independent checks

`verify_affine_strong_linear.py` does not run elimination to check the exclusions. It reconstructs the equations and directly sums each stored row combination modulo 83. It also verifies complete coverage of all multiplier cases and independently re-extracts the context maps from the corpus. The discovery analyzer passed 150 randomly relabeled, known-affine control cases without a false exclusion.

`verify_affine_last_family_classification.py` directly checks the three full coordinate permutations, the row proofs for the fourth case, and its exhaustive 83-value collision cover. Together with the stage-one certificates, these establish exactly three admissible multiplier pairs for A and B under the specified normalization.

The initial SMT attempts to complete those four cases all timed out at ten seconds. Direct finite-domain component enumeration resolved them in milliseconds. This was an improvement to the method, not evidence that a timed-out case was impossible.

## What the deck checks say

The stronger published passage relations were also tested separately from the older assumption set:

- Using only the stronger passages, general permutation-action folding remained consistent, the relative-update support lower bound reached 2, and all 82 rotations passed the return-displacement relaxation.
- Adding the stronger passages to the older assumptions gave the same outcomes. This adds the long East 4 / East 5 alignment that was absent from the older RUNS list.

These are necessary tests, not complete deck realizations. They do not identify a rotation, a common initial key, or plaintext. The unit-neighbor three-card model remains open.

An exact inverse-position search was additionally given a generated control with a contiguous 27-position plaintext alphabet. At 32 symbols per message, with the true rotation supplied and the initial key unknown, it still timed out. The search therefore has not passed recovery calibration. Its failure is not evidence against the real cipher.

The new alphabet constraint disables cyclic key normalization and suffix omission, since those reductions would otherwise change or remove the fixed alphabet restriction. It passed 24 exhaustive small-deck fixtures and 48 formulation comparisons. The existing 120 reduction comparisons also passed after the change.

## Files and reproduction

Run from the bundle directory with the listed Python dependencies:

```powershell
python verify_affine_strong_linear.py
python verify_affine_last_family_classification.py
python verify_inverse_alphabet.py
```

To reproduce the discovery and component completion:

```powershell
python affine_linear_certificate.py --trim 3
python affine_last_family_packing.py
python affine_collision_cover.py
python strong_passage_deck_audit.py
```

Main records:

- `affine_strong_linear_trim3.json`: all staged exclusions and their row weights.
- `checked_affine_strong_linear.json`: independent verification and coverage.
- `affine_last_family_packing.json`: the three embeddings and the failed fourth component.
- `affine_pair_52_32_collision_certificate.json`: coordinate equations and all 83 collision witnesses.
- `checked_affine_last_family_classification.json`: classification verification.
- `strong_passage_deck_audit.json`: the two explicitly separated deck assumption sets.

No project build was performed. Authored deliverables use CRLF line endings.
