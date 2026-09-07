# Passage-entry constraints and exact 32-symbol prefix fits

**The Noita eye cipher remains unsolved. No authentic plaintext or full-corpus key has been recovered.**

The previous one-mismatch barrier on the nine 32-symbol prefixes is now cleared. Two different 83-card decks satisfy all **124 repeated-plaintext comparisons across 288 ciphertext symbols**, one at rotation 9 and one at rotation 12. These are witnesses for the proposed unit-neighbor three-cycle model under the existing plaintext-equality assumptions. They are not identified historical keys.

| Verified witness | Prefix disagreements | Full-corpus disagreements, out of 256 | Selection positions used on full ciphertext |
| --- | ---: | ---: | ---: |
| Rotation 9 | 0 / 124 | 127 | 82 |
| Rotation 12 | 0 / 124 | 130 | 82 |

Each witness uses one common reset deck for all nine messages. The verifier checks the original full-corpus equality closure restricted to the prefixes, not just a potentially weaker clipped list of alignments. Each saved key fits only its own rotation among all 82 tested rotations. The existence of both keys proves that these prefix constraints do not identify the rotation when the initial deck is unknown.

The keys and exact decoded position sequences are in `context_entry_eyes32_b9_compact.json` and `context_entry_eyes32_b12_compact.json`. `checked_context_prefix_witnesses.json` records independent physical-deck verification. Both keys fail when carried into the rest of the ciphertext. Their full decodes use all 82 non-top positions; neither produces a recovered small plaintext alphabet.

## Equivalent constraints at passage entry

The tested model selects a non-top deck position, cycles the selected card, its bottom-ring neighbor and the top card, then rotates the bottom ring by a fixed amount. The numerical rotation and the update rule are assumptions.

For a pair of assumed equal plaintext passages, let their entry decks be D and E. Define R as the label permutation that maps the card at each position in D to the card at the same position in E. Applying the same positional update to both decks preserves R. Consequently, every corresponding ciphertext pair c, d in those passages must already satisfy:

`position_of(c, D) = position_of(d, E)`

Conversely, if this holds for every observed ciphertext pair in the passages, the first pair selects the same position. The identical update preserves R, so the next pair also selects the same position, and induction proves equality throughout the passages. This requires valid non-top selections. In this model, the first output must differ from the initial top and consecutive ciphertext labels must differ; these validity conditions are explicitly enforced.

This lets the solver compare all relevant cards at the passage entry instead of constructing a position-equality circuit at every output within the passage. It is an equivalent formulation of the existing assumptions, not new evidence that the passages share plaintext. No claim is made that this observation is new to cryptography or absent from all prior Noita work.

On the real 32-symbol prefix problem, the materialized symbolic positions fall from **2,580 to 1,189**, about 54%. The new solver simulates prefixes of lengths `[1, 1, 1, 19, 25, 24, 1, 1, 1]` and queries the necessary cards at their entry snapshots. It retains 61 free observed-card positions after the circular-coordinate normalization. The unobserved cards can fill the remaining key positions.

The initial eight-bit encoding still timed out. A seven-bit encoding with compact domain bounds and the dedicated bit-vector solver found the two real prefix witnesses in about 30–32 seconds each, and a generated 32-symbol control fit in about 34 seconds in these runs. These are observed run times, not a general performance guarantee. The generated control fit was not the planted plaintext, so it is not a successful recovery of the generated key.

The model permits all 82 non-top plaintext positions. It assumes the previous `shared_update_support.assumptions` equalities, including the common-body-prefix interpretation and applicable older repeated-passage alignments. It imposes no language, contiguous small alphabet, or numbered first-character assumption on the two real witnesses. The stronger affine-context findings from the previous report concern a different question and remain conditional as described there.

## Verification

`context_entry_solver.py --verify` checks the passage-entry equivalence against ordinary decoding for 6,912 exhaustive small-deck key cases, then checks both SMT encodings against exhaustive satisfiability on 48 fixtures.

`verify_context_entry_extended.py` adds 624 exhaustive key cases and 40 solver fixtures covering repetitions within the same message, overlapping context constraints, fixed key entries, and altered ciphertext. Both encodings also reproduce the full 1,036-symbol generated plaintext when supplied its complete planted key. These fixed-key checks validate the arithmetic; they are not unknown-key recovery experiments. In total, the equivalence tests cover 7,536 exhaustive key cases, 88 small solver fixtures and two full-size fixed-key checks.

The independent witness verifier uses a physical deck with an explicit bottom rotation. The solver uses inverse positions in a rotating frame. The verifier does not call SMT.

## Circular-order search controls

A separate heuristic searched card insertions, reversed bottom-ring intervals, top swaps and circular bottom shifts. It tested 9,963 unique neighbors per step, using a weighted all-pairs equality objective and, in one control, a known contiguous 27-position alphabet. A soft circular-distance objective was also tested.

On the 27-position generated control, 80 steps from a random key followed by 160 refinement steps reduced out-of-alphabet selections to 70, but still left 87 of the original 256 shared-selection comparisons wrong. It recovered only 189 of the 1,036 planted positions. A separate 200-step run with the nine correctly numbered first characters fixed also failed: 166 out-of-alphabet selections, 108 equality errors, and 217 correct planted positions. The known rotation was 9 in all these control runs.

The passage-entry formulation was also tried as a heuristic score on the original unrestricted-alphabet generated control. After 160 steps it still had 122 failed entry constraints and 129 failed original equality comparisons. Even allowing a global circular coordinate shift, only 72 planted positions matched.

These search failures are not cipher exclusions. The improved scores are not decryptions. They reinforce the need to authenticate every candidate against held-out ciphertext and to calibrate unknown-key recovery on generated examples.

## Limits and next obstacle

The initial 40-symbol-prefix runs timed out after 60 seconds on both the real rotation-12 problem and the generated rotation-9 control. With a longer time limit, the generated rotation-9 control admitted a complete 40-symbol-prefix structural fit in about 169 seconds, independently replayed against the original equality closure. It did not recover the planted plaintext. The real rotation-9 problem still timed out after 180 seconds. These runs are recorded in `context_entry_eyes40_b9_extended.json` and `context_entry_control40_extended.json`. A timeout is not an exclusion. An attempted solver initial-value hint triggered a native solver error before a result; that option was removed and the longer runs use no hint or fixed candidate key entries.

The concrete gain is an independently verified, smaller exact formulation and two complete structural witnesses beyond the prior prefix-search barrier. The obstacle remains recovering a key that satisfies the entire justified constraint set and produces independently credible plaintext. This result does not raise confidence that the actual cipher is a deck cipher.

## Reproduction

Run the research scripts directly; no project build is required.

```powershell
python context_entry_solver.py --verify --output checked_context_entry_solver.json
python verify_context_entry_extended.py
python context_entry_solver.py --length 32 --rotation 9 --compact --timeout 60000 --output context_entry_eyes32_b9_compact.json
python context_entry_solver.py --length 32 --rotation 12 --compact --timeout 60000 --output context_entry_eyes32_b12_compact.json
python verify_context_prefix_witnesses.py
python ring_order_search.py --steps 80 --alphabet 27 --soft 0 --output ring_order_control27_hard.json
python ring_order_search.py --steps 160 --alphabet 27 --soft 2 --source ring_order_control27_hard.json --output ring_order_control27_soft_refined.json
python context_entry_search.py --steps 160 --output context_entry_order_control82.json
```

The saved witnesses can be verified without reproducing the search or its run times. The corpus and source crosschecks remain in the earlier provenance files.
