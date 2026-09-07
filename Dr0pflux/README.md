# Dr0pflux cyclic-homophone audit

Contributor username: **Dr0pflux**

Owning GitHub account: **Dr0pflux**

Agent/session identity: Codex, conversation `6a9f0251-5288-83ea-92de-c4a0da1cf4d3` continuation

This folder contains a ciphertext-only audit of fixed cyclic homophonic substitution. The result is a conditional exclusion, not a decipherment: under the exact model in the report, the 83 observed labels require at least 79 plaintext classes.

- [Report](reports/cyclic-homophone-audit.md)
- [Verifier](code/cyclic_homophone_audit.py)
- [Saved result](results/cyclic_homophone_audit.json)

From the repository root, reproduce with Python 3.10 or newer:

```text
python Dr0pflux/code/cyclic_homophone_audit.py
```

The verifier uses only the Python standard library. It reads the canonical ciphertext file, runs generated positive and negative controls, recomputes every label-pair test, and rewrites the saved result.
