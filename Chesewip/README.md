# Chesewip - Noita eye cipher investigation

Owning GitHub account and contributor username: **Chesewip**. This snapshot contains the AI-assisted research developed with Codex in the owner's ongoing Noita investigation, published on **2026-09-07**.

**Unsolved: no authentic plaintext or full-corpus key recovered.** The complete history includes unsuccessful searches, artificial witnesses, corrected assumptions and conditional exclusions. Read the latest report before relying on an earlier result.

## Start here

- [Complete research index](outputs/README.md)
- [Latest phase-switch obstruction](outputs/phase-switch-findings.md): two explicit, trimmed repeated-plaintext alignments exclude the injective-tail three-card family with any common fixed bottom shuffle. Arbitrary keys and entry decks are allowed; the plaintext assumptions remain unverified.
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
