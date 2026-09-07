# A six-edge affine obstruction

**Unsolved. No meaningful plaintext or historical key recovered.**

This round produced a compact, independently checked obstruction to an affine context action on the 83 ciphertext symbols. It is conditional on two passage alignments representing repeated plaintext. Public research already reports affine exclusions, so this is an independent short certificate, not a claim to have first excluded the family.

## The certificate

Let A be the symbol correspondence between the documented West 2 / West 3 passage pair, and B the correspondence between the long East 4 / West 4 passage pair. Six observed correspondences give:

| Starting symbol | After A | After B |
|---|---|---|
| 47 | 18 | 47 |
| 54 | 42 | 54 |
| 21 | 43 | 34 |

Therefore B composed with A fixes two distinct symbols, 47 and 54, but moves 21 to 34.

Suppose there were a secret, arbitrary relabeling of the 83 symbols under which both context maps were affine transformations over the field with 83 elements. Their composition would also be affine, of the form `z -> a*z + b (mod 83)`.

Fixing two different coordinates x and y gives:

`(a - 1)*x + b = 0`

`(a - 1)*y + b = 0`

Subtracting forces `a = 1`, because x and y are distinct in a field. Then `b = 0`. The composition must fix every symbol. But the observed composition moves 21 to 34. Contradiction.

The numbers are symbol names here. No arithmetic meaning is assigned to their published numeric labels. Arbitrarily renaming all symbols preserves the proof.

## Exact locations

Positions in this table count from **1** in the published trigram corpus.

| Map | Source | Source symbol | Target | Target symbol |
|---|---|---:|---|---:|
| A | West 2, position 21 | 47 | West 3, position 26 | 18 |
| A | West 2, position 26 | 54 | West 3, position 31 | 42 |
| A | West 2, position 23 | 21 | West 3, position 28 | 43 |
| B | East 4, position 75 | 18 | West 4, position 78 | 47 |
| B | East 4, position 82 | 42 | West 4, position 85 | 54 |
| B | East 4, position 77 | 43 | West 4, position 80 | 34 |

A comes from the 14-symbol ciphertext alignment starting at West 2 position 19 and West 3 position 24. B comes from the 33-symbol alignment starting at East 4 position 69 and West 4 position 72. Every certificate edge remains after deleting the first two ciphertext positions of both alignments.

The labels and positions were independently reread from the separately stored [published trigram CSV](https://github.com/ngraham20/NoitaCryptographyResearch/blob/901123781c8af9a164bd71bda082391933611162/eye/reference/noita_eye_data_trigrams.csv). This is a published-transcription crosscheck, not a new extraction from the game.

## What is assumed, and what follows

The mathematical statement about these two partial maps is unconditional: they cannot both extend to permutations in one common relabeling of AGL(1,83).

Applying that statement to the unknown cipher assumes that the selected passage pairs actually share plaintext and therefore induce the stated context maps. A matching ciphertext equality pattern does not prove this. In particular, the short West 2 / West 3 alignment remains a substantive assumption.

Under that assumption, the certificate excludes the standard affine GAK action on 83 symbols, including its subgroup C83:C41. It allows arbitrary secret symbol coordinates, arbitrary affine parameters for the two contexts, and different initial affine states for different messages. It does not rely on numbered headers, English or Finnish plaintext, a small plaintext alphabet, or a particular initial deck.

It does not establish that the real cipher is a deck cipher. It also does not exclude general permutation actions, the unit-neighbor three-card mechanism, layered constructions outside this action, or an affine interpretation in which the assumed plaintext repetitions are wrong.

## Verification and prior work

`verify_affine_six_edges.py` independently checks the six corpus locations and the three composed paths. It also enumerates all **6,806** invertible affine maps over F83: the identity fixes 83 points, 82 translations fix none, and 6,723 other maps fix exactly one. There is no nonidentity affine map with two fixed points.

The search passed 100 randomly relabeled, partially observed affine controls without a false obstruction. Another 100 arbitrary relabelings preserved the real certificate.

The certificate is minimal with respect to these six isolated edges: deleting any one edge admits an explicit affine embedding of the other five. `affine_six_edge_minimality.json` stores all six embeddings, with direct arithmetic verification. This is not a claim that removing an edge repairs all the other passage constraints.

The community already documents [chaining conflicts](https://github.com/Lymm37/eye-messages/wiki/Chaining-Conflicts). More recent public work includes an [affine subgroup certificate](https://github.com/mvelzel/eye-vibe/blob/main/scripts/prove_c41_last_contexts.py) and a [combined-context affine exclusion](https://github.com/mvelzel/eye-vibe/blob/main/scripts/prove_c82_combined_contexts.py). Those are prior exclusion claims; their complete pipelines were not rerun here. The contribution of this pass is the small six-edge proof and its direct checks.

A separate observed-path scan using three strong contexts specified by that public work found no fixed-point obstruction. This is a limitation of the observed-path test, not a contradiction of the stronger public algebraic search or evidence for an affine key.

## What happened to the deck-key searches

The earlier 32-symbol-prefix candidate still has one failed equality. This pass checked every three-card cycle and every exchange of two separated bottom-deck blocks around that candidate, scoring all 82 rotations: **2,021,382 candidate transformations** in total. None removed the failure. An additional 91,881 adjacent-block exchanges at rotation 12 also failed to improve it. These are specified local neighborhoods, not an exhaustive key search.

A separate exact solver excluded a recorded nine-slot neighborhood and a recorded twenty-slot neighborhood. The smaller exclusion was independently verified by replaying all **362,880** permutations of its nine slots; the minimum remained one disagreement. Fixing the other key entries is essential to both conclusions.

Adaptive weighting reached 95 equality disagreements on a generated full-corpus control with known rotation, and four exact restricted improvement attempts timed out. The planted solution was not recovered. These failures provide no exclusion of the real cipher family.

The useful implementation advance is an inverse-position solver: observed ciphertext directly selects the card-position expression to update. It found exact 12-symbol and 24-symbol common-key prefix fits in seconds. Removing unobserved labels and irrelevant suffixes reduces the 32-symbol problem from 288 encoded outputs to 229, with 61 unknown initial positions after a cyclic-coordinate normalization. The hard 32-symbol search still timed out, including a generated control with numbered headers. No new complete prefix or full-corpus fit was obtained.

The formulations passed 30 initial independent checks plus 120 comparisons across 36 further exhaustive small-deck fixtures. These include symbolic rotation, allowed error budgets, omitted observations, and materialized state variables. An early unreduced full-corpus trial was stopped during expensive expression construction; explicitly naming intermediate positions fixed that construction bottleneck, but not the key-recovery problem.

## Reproduction

From the bundle directory, with Python and the listed dependencies installed:

```powershell
python verify_affine_six_edges.py
python affine_six_edge_minimality.py
python affine_fixed_point_scan.py --trim 3
python verify_inverse_positions.py
python verify_inverse_reductions.py
python verify_nine_slot_exclusion.py
```

The main certificate is `checked_affine_six_edge_certificate.json`. `affine_six_edge_minimality.json` contains the six deletion witnesses. The broader search results retain their nonzero error counts and limited scopes. No project build was performed.
