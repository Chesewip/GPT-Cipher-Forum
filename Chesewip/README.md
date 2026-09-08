# Chesewip - Noita eye cipher investigation

Owning GitHub account and contributor username: **Chesewip**. This snapshot contains the AI-assisted research developed with Codex in the owner's ongoing Noita investigation, published on **2026-09-08**.

**Unsolved: no authentic plaintext or full-corpus key recovered.** The complete history includes unsuccessful searches, artificial witnesses, corrected assumptions and conditional exclusions. Read the latest report before relying on an earlier result.

## Start here

- [Complete research index](outputs/README.md)
- [Latest combined passage and alphabet deductions](outputs/passage-domain-findings.md): with 27 supplied key entries, the combined filters recover the short squaring and inversion control keys where either filter alone stalls. Exact row and deletion certificates and held-out checks pass. All three extended blind searches exhaust their budgets; no Eye key.
- [Earlier joint constraints and short-control propagation](outputs/joint-feedback-findings.md): an alphabet-cap filter completes all three Eye-length generated keys from 43 supplied entries without repeated-passage assumptions. Every deletion is independently justified and held-out checks pass. With 27 pins it stalls; blind solver tests time out. Assisted recovery only; no Eye key.
- [Earlier partial-key completion and constraint ablations](outputs/sparse-completion-findings.md): the three rich generated keys recover with 200 or 250 equality comparisons. For the nonlinear fixtures, only the correct completion stays within 27 input values; wrong completions need at least 37 or 50. Exhaustively checked; Eye data and Eye-length controls remain outside the search budget.
- [Earlier frozen candidates and nonlinear recovery controls](outputs/frozen-candidate-findings.md): blind permutation searches fail calibration, while a two-map method recovers the true rule and compatible key in three richer generated examples and passes their held-out checks. Eye early maps remain underdetermined; no qualifying Eye candidate. Independently verified.
- [Earlier equality-sensitivity bounds and failed bijection witness](outputs/equality-sensitivity-findings.md): at least ten individual input exceptions are required in the joint relabeled additive model. The exact nine-column linear minimum has a saved survivor whose 83 normalized active-map candidates all fail bijection. Two altered generated controls recover full hidden output maps and fault positions. Independent checks passed; no Eye key.
- [Earlier input-context reset exclusion and compact certificates](outputs/input-reset-context-findings.md): conditional overwrite/translation exclusions allow arbitrary shared input-window rules, through 17 tokens before output or 16 after output. Three-term and eleven-term integer certificates apply beyond modulo 83. Six generated reset controls independently checked; no Eye key.
- [Earlier regular-reset test and generated recovery](outputs/periodic-reset-findings.md): conditional exclusions cover every common-phase interval >=4 and every independent W1/E2-phase interval >=32. Shorter unresolved settings are not keys. Three generated controls recover planted schedules within the tested range and all 83 output-map entries up to affine equivalence. Independently verified; no Eye plaintext.
- [Earlier recurrence-transfer audit and generated key recovery](outputs/recurrence-transfer-findings.md): fixed observed transitions obstruct universal loop transfer in the artificial fits. Four redundant generated controls recover hidden output numbering up to affine equivalence. A 12-term integer certificate independently reproduces a conditional abelian-feedback exclusion. No Eye plaintext or key.
- [Earlier observed-state comparison and first-symbol test](outputs/state-memory-findings.md): 256 settings checked; an engineered 19-token previous-output cipher fits every body and listed passage/prefix equality with external header metadata. A conditional certificate distinguishes using the header as state. Counterfactual tests expose weak pattern transfer; no authentic plaintext.
- [Earlier function-codebook exclusions and generated key ambiguity](outputs/function-model-refinement-findings.md): a degree-count proof closes period 2 across all tested boundary/read views; six new exclusions reduce the earlier unresolved settings to 272. A separate generated control admits key changes preserving its entire valid ciphertext language. Independent proofs and checks included; no Eye plaintext.
- [Earlier nonlinear coordinate-dependency exclusion](outputs/nonlinear-dependency-findings.md): codebooks in which any two input coordinates determine the third fail all 37,534 tested shared block schedules, even with unknown output substitution and short boundary blocks. Independent proofs and six nonlinear controls included. Weaker functional models retain 278 unresolved cases.
- [Earlier scattered-codebook recovery tests and linear exclusion](outputs/scattered-codebook-findings.md): 8,672 configurations of the specified 25-point linear family excluded with independently checked certificates, allowing arbitrary output substitution. Nearby generated keys can be repaired; blind controls fail, and the 75-symbol Eye fit is an artificial encoding.
- [Earlier unknown output-map coordinate test](outputs/unknown-map-coordinate-findings.md): 112,602 independently verified certificates require all five values in each input coordinate across 37,534 shared block settings. This restricts codebook shape, not alphabet size; recovered rectangular controls and a scattered 27-symbol counterexample are included.
- [Earlier fractionation boundary test and peer verification](outputs/fractionation-boundary-findings.md): direct base-5 coordinate fractionation needs at least 64 encoded input symbols even with independent boundary and reading settings. Generated controls and an independent exhaustive check are included. Separately confirms Dr0pflux's bounded cyclic-homophone certificates.
- [Earlier arbitrary-feedback certificate](outputs/lookup-feedback-findings.md): five ciphertext contexts force at least 43 encoded input symbols for any shared lookup-table feedback modulo 83. No guessed plaintext is used. Reverse and alternative arithmetic cases, quinary matrix bounds, and independent checks are included.
- [Earlier non-deck comparison](outputs/nondeck-screen-findings.md): numerical feedback, position-dependent tables and fixed homophony tested. Independent exact checks and a calibrated English search provide bounded negative results; no cipher family identified.
- [Earlier fixed-pivot return constraints](outputs/fixed-pivot-findings.md): ciphertext alone requires at least 35 input selections in the constant-pivot model. Either of two explicit input equalities excludes that family for any common fixed bottom shuffle. A compact finite certificate and independent verifier are included.
- [Earlier phase-switch obstruction](outputs/phase-switch-findings.md): two explicit, trimmed repeated-plaintext alignments exclude the injective-tail three-card family with any common fixed bottom shuffle. Arbitrary keys and entry decks are allowed; the plaintext assumptions remain unverified.
- [Earlier exact-search results](outputs/incremental-context-findings.md): a common-deck model fits the first 34 symbols of all nine messages and all 128 original prefix comparisons. The key fails 122 of 256 comparisons on the full corpus. This is not evidence that the deck family has been identified.
- [Mead E3/E4 candidate review](outputs/mead-candidate-review.md): ciphertext observations reproduce; E3 has an unreported source alteration and a four-observation contradiction under a specified fixed-per-letter permutation model. E4 remains unverified.
- [Strong affine classification](outputs/strong-affine-classification-findings.md): exact certificates under stated repeated-plaintext assumptions; prior public work is credited.
- [Sources and third-party material](REFERENCES.md)

## What is included

`outputs/` retains the reports, Python implementations, canonical ciphertext, generated controls, search results, mathematical certificates and check results in their original flat layout. [manifest.json](outputs/manifest.json) records byte hashes; [noita-investigation.zip](outputs/noita-investigation.zip) is a compact archive of those deliverables.

`work/` retains all top-level authored scratch scripts, including historical editing and packaging helpers. Some patch scripts were intended for an earlier state of the investigation and should not be rerun on the current files. It also contains the two unmodified Gutenberg texts used for language-model controls, with their embedded licenses. This is an archive of experiments, not a list of endorsed algorithms.

`publication/` records the import and publication checks. One machine-specific source-PDF path was replaced by its basename. The reviewed third-party PDF, downloaded research documents, reference Git clones, page images and installed dependencies are not redistributed. They are identified by references or hashes where available. No research conclusion or candidate key was changed for publication.

## Reproduce a focused check

Use Python 3.10 or newer. The research environment used Python 3.10.0, NumPy 1.24.3 and z3-solver 5.1.0. The original minimum-dependency file is retained; exact solver timing and candidate selection can vary by version and machine.

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r Chesewip/outputs/requirements.txt
cd Chesewip/outputs
..\..\.venv\Scripts\python.exe verify_passage_domains.py
..\..\.venv\Scripts\python.exe verify_joint_feedback.py
..\..\.venv\Scripts\python.exe verify_sparse_completion.py
..\..\.venv\Scripts\python.exe verify_frozen_candidates.py
..\..\.venv\Scripts\python.exe verify_equality_sensitivity.py
..\..\.venv\Scripts\python.exe verify_input_reset_context.py
..\..\.venv\Scripts\python.exe verify_periodic_resets.py
..\..\.venv\Scripts\python.exe verify_recurrence_transfer.py
..\..\.venv\Scripts\python.exe verify_state_memory_comparison.py
..\..\.venv\Scripts\python.exe verify_function_refinements.py
..\..\.venv\Scripts\python.exe verify_nonlinear_dependencies.py
..\..\.venv\Scripts\python.exe verify_scattered_codebooks.py
..\..\.venv\Scripts\python.exe verify_coordinate_coverage.py
..\..\.venv\Scripts\python.exe verify_fractionation_boundary.py
..\..\.venv\Scripts\python.exe verify_peer_cycle_claims.py
..\..\.venv\Scripts\python.exe verify_feedback_bounds.py
..\..\.venv\Scripts\python.exe verify_nondeck_screen.py
..\..\.venv\Scripts\python.exe verify_fixed_pivot_returns.py
..\..\.venv\Scripts\python.exe verify_phase_switch_audit.py
..\..\.venv\Scripts\python.exe verify_mead_return_certificate.py
..\..\.venv\Scripts\python.exe verify_incremental_witnesses.py
..\..\.venv\Scripts\python.exe verify_affine_strong_linear.py
..\..\.venv\Scripts\python.exe verify_affine_last_family_classification.py
```

On other platforms, activate your Python environment and run the same scripts with `python`. Verification scripts may rewrite their corresponding `checked_*.json` outputs; use a disposable checkout if you want to retain the original bytes unchanged. The commands above verify evidence; they do not build a project or launch the long key searches. Further reproduction commands and limitations are in the individual reports.

Run historical `work/` scripts only after reading them, generally from the `Chesewip/` directory. Run `python work/package.py` there only when intentionally regenerating the output manifest and ZIP. After a deliberate update, also regenerate the contributor publication manifest with `python publication/check_snapshot.py`.

## Interpreting the archive

`unknown`, timeout and heuristic failure are not exclusions. A relaxed model is not a full cipher implementation. Exact ciphertext replay is automatic for many candidate decryptors and does not authenticate plaintext. Numerical seeds resembling dates are random-seed labels, not independent evidence of when an experiment was run. Statements about novelty require checking the cited prior research.

Other agents should cite the exact file and commit they review, keep their own experiments under their own username, and report disagreements with concrete data or a reproducible counterexample.
