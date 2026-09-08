# Noita eye cipher research bundle

**Unsolved. No real plaintext or key recovered.**

Latest: see `passage-domain-findings.md`. Combining passage equations with alphabet-cap deductions completes the short generated squaring and inversion keys from the same 27 supplied entries where either filter alone stalls. Exact row and deletion certificates and held-out checks pass. All three extended blind searches exhaust their budgets without a key; no Eye search or decipherment.

Previous: see `joint-feedback-findings.md`. A local alphabet-cap filter recovers all three Eye-length generated keys when 43 key entries are supplied, starting with only 24 or 25 known input values and using no repeated-passage assumptions. Independent deletion certificates and held-out checks pass. With 27 supplied entries it stalls; all blind simultaneous-solver controls time out. Assisted recovery only; no Eye key.

Previous: see `sparse-completion-findings.md`. Partial two-map recovery now completes the three rich generated keys with 200 or 250 equality comparisons instead of 1,000. In the nonlinear fixtures, the correct missing-label completion uses 27 input values; every wrong feedback-consistent completion needs at least 37 or 50. Independent exhaustive verification and ablations passed. Eye data and Eye-length controls remain outside the search budget; no Eye key.

Previous: see `frozen-candidate-findings.md`. Candidate generation now tests three explicit unknown-map feedback rules with later messages withheld from fitting. Blind permutation searches fail controls; a separate two-map method recovers the correct rule and compatible key in three richer generated examples, all passing frozen held-out codebooks. The Eye early maps remain underdetermined (rank 45 of 166); no qualifying Eye candidate. Independent verification passed.

Previous: see `equality-sensitivity-findings.md`. The relabeled additive model requires at least ten individual exceptions among 141 compared input positions; exact separate minima are three early and four late. The joint whole-column minimum is nine, but the saved nine-column linear survivor has no bijective completion across all 83 normalized active-map candidates. Two generated controls recover their altered positions and full hidden output maps up to affine equivalence. Independently checked; no Eye key.

Previous: see `input-reset-context-findings.md`. Shared input-context overwrites cannot rescue the stated translation-feedback model under the passage assumptions: windows through 17 tokens before output, or 16 after output, are conditionally excluded. A three-equation early certificate and an eleven-term late certificate cancel over integers, extending these bounds to abelian groups beyond modulo 83. Six generated reset controls pass the correct filter and fail an intentionally unfiltered analysis. No Eye key.

Previous: see `periodic-reset-findings.md`. Under the stated repeated-input assumptions, arbitrary regular resets cannot rescue relabeled additive feedback with a common phase at intervals >=4; an exhaustive independent W1/E2 phase test excludes intervals >=32. Shorter unresolved cases are not keys. Three redundant generated controls isolate their planted nontrivial schedules within the tested range and recover all 83 output-map entries up to affine equivalence. Independent verification passed; no Eye plaintext.

Previous: see `recurrence-transfer-findings.md`. Observed transitions prevent the prior artificial token fits from universally preserving their fitted return loops. Four redundant generated cyclic controls recover the true hidden output numbering up to affine equivalence; controls using the Eye hypothesis layout remain underdetermined. A 12-term integer certificate independently reproduces a conditional commutative-feedback exclusion with arbitrary injective output labeling. No Eye plaintext or key.

Previous: see `state-memory-findings.md`. A comparison of 256 observed-state table settings separates ciphertext facts from passage assumptions. An engineered 19-token cipher remembering only the previous output reproduces all 1,027 body symbols and the listed passage/prefix equalities if the first raw symbol is metadata. Treating it as the previous-symbol state yields a compact conditional contradiction. Counterfactual starts expose weak pattern transfer; no authentic plaintext.

Previous: see `function-model-refinement-findings.md`. An independently checked degree-count proof excludes period 2 for any one-coordinate function codebook and every tested boundary/read view. Two further equality certificates bring the full-first-block unresolved count to 272. A separate generated control has intrinsic key ambiguities preserving every structurally valid ciphertext message; this is not an Eye key. Solver witnesses, timeouts and independent checks are included.

Previous: see `nonlinear-dependency-findings.md`. Every tested shared fractionation schedule fails for an input codebook where any two coordinates determine the third, with no assumed equation and an arbitrary output substitution. All 37,534 settings, including short first blocks, have independently replayed proofs. A weaker one-coordinate function model retains 278 unresolved settings; arbitrary scattered codebooks remain open.

Previous: see `scattered-codebook-findings.md`. Independent checks exclude the specified 25-point linear codebooks behind arbitrary output substitutions across 8,672 shared-period configurations. A scattered-codebook search repairs nearby generated keys but fails blind controls; its 75-symbol Eye fit is artificial and supplies no plaintext. Exact certificates, failed pilots and all candidate mappings are retained.

Previous: see `unknown-map-coordinate-findings.md`. Even allowing an arbitrary shared output-symbol substitution, 112,602 independently checked certificates across 37,534 block configurations require every input coordinate to use all five digit values. This restricts the shape of the codebook, not its number of symbols: a generated scattered 27-symbol counterexample makes that limit explicit. Three rectangular unknown-map controls recover their planted settings.

Previous: see `fractionation-boundary-findings.md`. Direct base-5 coordinate fractionation requires at least 64 encoded input symbols despite independently variable message periods, short boundary blocks and reading conventions. Generated prime-length controls recover their planted settings up to reversal; the decisive bound is independently exhaustive-checked. A separate implementation confirms Dr0pflux's bounded cyclic-homophone certificates, with attribution. No plaintext recovered.

Previous: see `lookup-feedback-findings.md`. Five observed predecessor contexts force at least 43 encoded input symbols for arbitrary shared lookup-table feedback modulo 83, with no guessed plaintext. Reverse reading and other translation groups also need more than 40. All quinary linear feedback matrices require at least 72; independent verification included.

Previous: see `nondeck-screen-findings.md`. A bounded comparison tests numerical feedback, position-dependent substitution and fixed homophony. Exact support bounds and conditional table contradictions are independently checked; an assumption-free English homophonic search recovers over 99% on three generated controls but no coherent text from the eyes. No replacement family is identified.

Previous: see `fixed-pivot-findings.md`. The constant-pivot three-card escape requires at least 35 input selections from ciphertext alone; either of two separately stated plaintext equalities excludes it for every common fixed bottom shuffle. Exact first-return certificates and independent checks are included. Nonconstant, noninjective third-position rules remain open.

Previous: see `phase-switch-findings.md`. Two explicitly stated, conservatively trimmed E4/E5 plaintext alignments exclude the unit-neighbor three-card route, and more generally any injective third-position rule with a common fixed bottom shuffle. This key-independent contradiction is conditional on those plaintext alignments; it does not identify the actual cipher. The earlier prefix fits remain valid under their older constraints.

For the user-supplied Hermetic plaintext proposal, see `mead-candidate-review.md`: the ciphertext tables and lengths reproduce, but E3 has an unreported source alteration and a four-observation contradiction within the fixed-per-letter positional permutation model. E4 remains unverified.

Start with `incremental-context-findings.md`: exact common-deck fits now extend to all nine 34-symbol prefixes, with all 128 original comparisons verified. The 35-symbol stage remains unresolved; the saved key fails on the full corpus. The report also gives exact shared-prefix restrictions and tested alternative encodings. `context-entry-search-findings.md` covers the preceding work: an equivalent passage-entry formulation reduces the exact key-search circuit and finds two independently verified common-deck fits for all nine 32-symbol prefixes, at rotations 9 and 12. Both fail on the full corpus; no plaintext is recovered. `strong-affine-classification-findings.md` covers the preceding work: affine exclusion independently verified using three stronger contexts, and a complete three-pair classification for the two last-family maps. General deck tests still pass only necessary conditions; no key is recovered. `affine-obstruction-findings.md` covers the previous result: an independently checked six-edge obstruction to a common affine context action, conditional on two repeated-plaintext alignments; prior public affine exclusions are credited. It also records the improved inverse-position solver and the unsuccessful wider key searches. `common-deck-search-findings.md` covers the preceding work: the saved return-only assignments fail forbidden-return checks; a revised search fits all nine 24-symbol prefixes with one common deck, but no full-corpus key satisfies the plaintext-equality assumptions. `return-path-search-findings.md` records the earlier partial-return results: decomposed exact return constraints now have independently replayed assignments for 195 intervals at rotation 9, with no initial key or plaintext recovered. The stronger ciphertext-only bounds remain in `small-update-difference-findings.md`: ciphertext-only entry-change bounds now require at least 18 East1/West1 plaintext differences over 99 positions for anchored three-card updates with a common initial deck, or 11 with arbitrary different initial decks. `template-identifiability-findings.md` covers the preceding results: exactly 18 minimum-difference templates for the first 50 East1/West1 symbols, small-alphabet engineered witnesses, a sharp nine-difference construction over 99 symbols, and broader consistency checks. `plaintext-difference-findings.md` develops the preceding results: key-independent bounds on aligned plaintext differences, stronger bounds for small shuffles, and an engineered exact-prefix counterexample separating output agreement from state agreement. `shared-pattern-testing.md` covers transition-preserving pattern audits and inconclusive searches using shared passages. `key-recovery-and-headers.md` covers known-phrase controls and alphabet exclusions allowing arbitrary first symbols. The preceding reports retain earlier exclusions, scans, provenance, and assumption corrections.

Important evidence:

- `affine_family_certificate.json`: all affine common shuffles excluded at selection alphabet <=40, arbitrary initial key, within the stated one-swap model.
- `checked_trimmed_isomorph_3.json`: conditional exclusion of every common shuffle in that model, using the documented repeated-plaintext interpretation and discarding early comparisons.
- `checked_synchronized_bound_*.json`: finite certificates for the seven two-cycle cases.
- `checked_multicycle_bound_1_41_41_40.json`: independently checked two-residual-cycle exclusion.
- `ciphertext.json` and `provenance.json`: corpus and published-source crosscheck.

Install NumPy and z3-solver in the Python environment if needed. The scripts also recognize this workspace's optional `../work/pydeps` directory. Research scripts are run directly; there is no build step.

Tested here with Python 3.10.0, NumPy 1.24.3, and z3-solver 5.1.0. `requirements.txt` lists the two dependencies.

Key reproduction commands, from the extracted bundle directory:

```powershell
python verify_passage_domains.py
python verify_joint_feedback.py
python verify_sparse_completion.py
python verify_frozen_candidates.py
python verify_equality_sensitivity.py
python verify_input_reset_context.py
python verify_periodic_resets.py
python verify_recurrence_transfer.py
python verify_state_memory_comparison.py
python verify_function_refinements.py
python verify_nonlinear_dependencies.py
python verify_scattered_codebooks.py
python verify_coordinate_coverage.py
python verify_fractionation_boundary.py
python verify_peer_cycle_claims.py
python verify_feedback_bounds.py
python verify_nondeck_screen.py
python verify_cycle_bounds.py
python check_single_cycle_certificate.py
python check_multicycle_certificate.py multicycle_bound_1_41_41_40.json
python affine_family_certificate.py
python verify_synchronized_isomorph.py --skip 3
python verify_multicycle_controls.py
python variable_three_cycle.py --verify
python clocked_three_cycle_scan.py --control
python verify_block_system.py
python full_rotation_three_cycle.py --control
python pattern_assumption_audit.py
python verify_header_reachability.py
python verify_context2_enumeration.py
python verify_plaintext_change_bounds.py
python verify_weight_dp.py
python verify_compact_templates.py
python verify_compact_99.py
python verify_action_fold.py
python verify_entry_change_bounds.py
python verify_entry_change_timing.py
python verify_return_methods.py
python verify_component_assignments.py
python verify_nonreturn_refinement.py
python verify_common_deck_array.py
python verify_direct_key_search.py
```

For each L from 2 through 8:

```powershell
python check_synchronized_certificate.py synchronized_bound_L_40.json
```

Replace `L` with the number. The discovery runs can be more expensive than verification. `unknown`, `solver_unknown`, `time_limit`, `inconclusive`, and `relaxation_survives` are not exclusions. An `exact_replay` flag is only an implementation check; it does not authenticate plaintext.
