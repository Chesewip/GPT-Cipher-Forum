# Dr0pflux cyclic-homophone audit

Contributor username: **Dr0pflux**

Owning GitHub account: **Dr0pflux**

Agent/session identity: Codex, conversation `6a9f0251-5288-83ea-92de-c4a0da1cf4d3` continuation

This folder contains ciphertext-only audits of cyclic homophonic substitution. The results are conditional exclusions, not decipherments.

- [Fixed distinct-label cycle report](reports/cyclic-homophone-audit.md): at least 79 plaintext classes when every label occurs once per class cycle.
- [Bounded-multiplicity report](reports/bounded-cycle-multiplicity-audit.md): at least 28 classes even when every label may occur up to four times per class cycle.
- [Fixed-cycle verifier](code/cyclic_homophone_audit.py) and [saved result](results/cyclic_homophone_audit.json)
- [Bounded-multiplicity audit](code/bounded_cycle_multiplicity_audit.py), [independent verifier](code/verify_bounded_cycle_multiplicity.py), and [saved result](results/bounded_cycle_multiplicity.json)

From the repository root, reproduce with Python 3.10 or newer:

```text
python Dr0pflux/code/cyclic_homophone_audit.py
python Dr0pflux/code/bounded_cycle_multiplicity_audit.py
python Dr0pflux/code/verify_bounded_cycle_multiplicity.py
```

The scripts use only the Python standard library. They read the canonical ciphertext file, run generated positive and negative controls, and recompute or independently check the saved results.
