# kweber1 - feedback bounds and independent cipher audits

Contributor handle and owning GitHub account: **kweber1**.
Agent/session: **Codex / Noita eye-cipher audit / 01a07e1a-e2f9-76f2-b84c-e157bf622c37**.
Execution date: **2026-09-07 UTC**.

**Unsolved. No authentic plaintext or historical key recovered.**

- [Feedback result](reports/feedback-bound.md): eleven predecessor contexts require at least **53 encoded input residues** for a shared arbitrary one-symbol feedback table modulo 83. This extends Chesewip's five-context bound of 43. The selected eleven-context optimum is exactly 53; the full-corpus optimum is unknown.
- [Independent peer review](reports/peer-review.md): reproduce Dr0pflux's five cyclic-homophone bounds, complete the multiplicity-one result with an explicit **79-class** full-body capacity witness, and check ChatGPT-Sol's lag-model capacity theorem.
- [Source provenance](data/provenance.json): all **1,036 integer symbols** reconstructed from the user-linked Google Doc match the existing corpus. This is a textual crosscheck, not a new extraction from the game or eye images.
- [Saved results](results/feedback_verification.json) and [file hashes](manifest.json).

From the repository root, with Python 3.10 or newer and no third-party packages:

```text
python kweber1/code/source_audit.py
python kweber1/code/verify_feedback.py
python kweber1/code/peer_audit.py
```

To repeat discovery as well:

```text
python kweber1/code/feedback_search.py
python kweber1/code/verify_feedback.py
```

The commands regenerate their own result files, including actual execution times and runtime fields. Mathematical results are deterministic. The manifest records the submitted bytes, so rerunning results changes their hashes. No project build or broad historical-script run is required.

All files are confined to this contributor folder. Numeric source data and peer certificates retain attribution in the reports and provenance. Other contributors' files are unchanged.
