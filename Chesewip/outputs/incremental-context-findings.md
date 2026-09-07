# Incremental extension to 34-symbol prefixes

**Unsolved. No authentic plaintext or full-corpus key has been recovered.**

The exact common-deck fit now extends to the first **34 symbols of all nine messages**: 306 ciphertext outputs and all 128 original repeated-plaintext comparisons pass. The saved 83-card key uses rotation 9. It fails 122 of the 256 comparisons when applied to the full corpus, and its full decode uses all 82 non-top selection positions. It is a conditional structural witness, not a recovered cipher key.

| Prefix length per message | Outputs covered | Original comparisons satisfied | Full-corpus comparison failures |
| --- | ---: | ---: | ---: |
| 32 | 288 | 124 / 124 | 129 / 256 |
| 33 | 297 | 126 / 126 | 127 / 256 |
| 34 | 306 | 128 / 128 | 122 / 256 |

These rows are different candidate keys from successive solver stages, not one key that was progressively revealed. They are saved in `incremental_eyes40_bv.json`. The longer-budget repeat, `incremental_eyes40_bv_extended.json`, reproduced these fits. Both stopped with a timeout at length 35: first after 45 seconds for that stage, then after 120 seconds. Neither timeout establishes impossibility.

## Incremental exact solving

The previous search rebuilt the position circuit for each prefix problem. The new solver builds one circuit for the intended target, orders passage-entry constraints by the earliest prefix that contains their observations, and adds them in stages. It retains the same solver and its learned information between stages. It does not pin the previous candidate key.

In the first run, the 32-symbol stage took about 33 seconds, the 33-symbol stage about 45 seconds, and the 34-symbol stage about 0.6 seconds. This is a useful improvement on this instance, not a general speed claim. A generated-control run using the same incremental strategy timed out at its first 32-symbol stage; the earlier nonincremental solver had found that control's prefix fit. Search performance remains sensitive to formulation, and full generated-key recovery has not succeeded.

The difficulty beyond 32 is concentrated in two older assumed matching passages: West 2 starting at zero-based position 19, aligned with East 3 starting at 25 and West 3 starting at 24. Moving from length 32 to length 40 adds 11 comparisons under the original full-corpus equality closure. Each of the earlier rotation-9 and rotation-12 32-symbol witnesses failed nine of those added comparisons.

## Exact restrictions from the shared beginnings

The earlier research already established the four/five-label relative support after different first selections in this model. Here that property is turned into explicit initial-key restrictions and an optional solver simplification. This is not claimed as a new discovery of a cipher mechanism or a globally novel theorem.

Let the initial top be O, the two distinct first-output cards be A and B, and their respective bottom-ring successors be S(A) and S(B). After the two first updates, the cards at different physical positions are exactly:

`{O, A, B, S(A), S(B)}`

The common bottom rotation does not change this set. Therefore, a later common ciphertext label C in an assumed equal plaintext prefix must lie outside this set. Its appearance excludes C as the initial top and as either first-output card's initial successor. The observed first-output cards themselves cannot initially be on top.

Applied to the existing shared-prefix assumptions, this leaves **44 possible initial top labels**, together with explicit forbidden-successor lists for the nine first-output cards. These are necessary restrictions within the common-reset unit-neighbor model, valid for every bottom rotation. They are not an unconditional property of the eye cipher. The restrictions do not assume numbered first characters.

`first_step_prefix_restrictions.json` records the allowed tops, forbidden successors and source observations. The statement about the relative support was checked directly on 2,298 deck/selection cases with deck sizes 3, 4, 5, 6 and 83, including adjacent selections and wraparound. The two earlier real 32-symbol witnesses satisfy the saved restrictions.

For the 40-symbol problem, 222 of the 246 unique passage-entry constraints can use these initial-key inequalities. This reduces materialized position variables from 1,454 to 1,340 and eliminates first-step state queries for six messages. The simplified encoding did not outperform the original in these runs: direct 40-symbol searches timed out, and its incremental run stopped at length 33.

## Other tested routes

- Integer and finite-domain encodings passed the exhaustive small-instance checks but timed out on their initial real 32-symbol stage.
- Lazy card uniqueness began with an overapproximation and added exact distinctness constraints whenever a tentative model assigned several cards to one position. It rejected three such collision models, adding 89 pair exclusions, then timed out on length 40. No collision model was accepted as a deck.
- Conflict-guided repair temporarily fixed candidate key assignments, used unsatisfiable cores to identify conflicting pins, and released assignments on conflicts or timeouts. Two release policies on the real 34-symbol candidate and one generated-control repair produced no complete 40-symbol fit. All candidate pins were eventually released. Their final solver calls remained inconclusive. A restricted-key UNSAT result was not treated as a cipher exclusion.

The repair method recovered valid solutions on 12 small generated problems. That validates its basic operation; it does not establish useful full-size recovery capability.

## Verification and reproduction

`checked_incremental_context.json` records **4,608 exhaustive key/cutoff comparisons and 768 solver checks**, covering three encodings, the shared-prefix simplification enabled and disabled, eager and lazy uniqueness, repetitions within a message, and staged constraints. All matched exhaustive satisfiability on the small fixtures.

`verify_incremental_witnesses.py` uses a physical deck and explicit rotations to replay saved real and generated fits. It checks against the original full-corpus plaintext-equality closure restricted to each prefix, not merely the solver's clipped passage list. `checked_incremental_witnesses.json` records the results and each candidate's failures on the remaining ciphertext.

All results retain the previous model assumptions: one common reset deck, the unit-neighbor three-cycle update, fixed rotation, all non-top plaintext positions allowed, and the listed repeated-plaintext interpretations. No language model or small-alphabet condition authenticates these witnesses. The extension to 34 symbols improves the search capability; it does not increase confidence that this is the actual cipher family.

Run scripts directly; no project build is required.

```powershell
python incremental_context_solver.py --verify --output checked_incremental_context.json
python first_step_fixed_points.py
python incremental_context_solver.py --encoding bv --timeout 120000 --output incremental_eyes40_bv_extended.json
python core_guided_context_repair.py --verify --output checked_core_guided_context.json
python verify_incremental_witnesses.py
```

The saved witnesses can be checked without repeating the searches. The remaining exact-search obstacle is the 35-symbol stage, followed by the rest of the corpus. The full cipher remains open.
