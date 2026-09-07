# Noita eye cipher research bundle

**Unsolved. No real plaintext or key recovered.**

Latest: see `unknown-map-coordinate-findings.md`. Even allowing an arbitrary shared output-symbol substitution, 112,602 independently checked certificates across 37,534 block configurations require every input coordinate to use all five digit values. This restricts the shape of the codebook, not its number of symbols: a generated scattered 27-symbol counterexample makes that limit explicit. Three rectangular unknown-map controls recover their planted settings.

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
