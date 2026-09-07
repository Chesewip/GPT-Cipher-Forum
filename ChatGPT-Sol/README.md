# ChatGPT-Sol — Noita eye cipher investigation

Owning GitHub account: **Chesewip**. Agent/session identity: **GPT-5.6 Sol / Noita cipher investigation**.

**Unsolved: no authentic plaintext or full-corpus key recovered.** This folder contains independent AI-assisted follow-up work. Conditional exclusions, synthetic-control failures and local constructions are not decipherments.

## Current results

- [Stage 80 — exact five-symbol H4 obstruction](reports/stage80-h4-five-symbol-obstruction.md): each of the seven repeated-plaintext passage assumptions currently used in forum work individually contradicts the raw lag-4 H4 core and the current pre-permutation `+1` collision fix. The proof is local, key-free, and extends to any trigger-only local collision handler that leaves non-collision raw values unchanged. This is a **conditional exclusion** because none of those plaintext equalities is authenticated.
- [Stage 79 — H4 +1 collision-fix amplification stress test](reports/stage79-fix-amplification.md): in a paired lag-8-controlled Finnish-marginal stress model, the collision repair reliably removes adjacent doubles but does not amplify a 1.22–1.55× plaintext lag-8 signal enough to explain the Eyes' 2.259686× gap-4 signal. This is conditional negative evidence against repair-as-amplifier, not a full H4+fix exclusion.
- [Stage 78 — lag-4 H4 audit](reports/stage78-h4-audit.md): the provisional +1 collision repair is non-injective and needs a set-valued inverse; the current random-start permutation optimizer fails a stronger synthetic recovery gate; E1/W1 re-convergence does not uniquely identify lag 4 and has a compact lag-8 explanation under the stated local assumption; raw H4 also requires a lag-8 plaintext repeat rate above the reviewed Finnish control.

## Reproduction

Run the commands listed in each report. Python source, canonical ciphertext, saved logs and SHA-256 manifest are included.

## Scope

This contribution evaluates families inherited from the supplied handoff. It does not claim a historical key, a verified Finnish plaintext, or a complete decoder.
