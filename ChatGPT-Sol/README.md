# ChatGPT-Sol — Noita eye cipher investigation

Owning GitHub account: **Chesewip**. Agent/session identity: **GPT-5.6 Sol / Noita cipher investigation**.

**Unsolved: no authentic plaintext or full-corpus key recovered.** This folder contains independent AI-assisted follow-up work. Conditional exclusions, synthetic-control failures and local constructions are not decipherments.

## Current results

- [Stage 82 — exact ciphertext-capacity theorem](reports/stage82-h-ciphertext-capacity.md): with unrestricted plaintext, raw lag-L H is universal on ciphertext for every lag. The current local repair has exact ciphertext image equal to sequences with no adjacent repeats. The Eyes satisfy that property, so exact replay cannot identify lag 4; H4 is capacity-compatible rather than ciphertext-supported.
- [Stage 81 — passage provenance audit](reports/stage81-passage-provenance-audit.md): all seven registered passage tuples are nonliteral ciphertext equality-isomorphs, and the inspected source trail explicitly treats repeated plaintext as an unverified model assumption. This converts Stage 80 into a cross-model incompatibility: current H4 and the repeated-plaintext semantics of any one registered passage cannot both be correct.
- [Stage 80 — exact five-symbol H4 obstruction](reports/stage80-h4-five-symbol-obstruction.md): each of the seven repeated-plaintext passage assumptions individually contradicts the raw lag-4 H4 core and current local collision-repair family. Conditional because those plaintext equalities are not authenticated.
- [Stage 79 — H4 +1 collision-fix amplification stress test](reports/stage79-fix-amplification.md): the collision repair removes adjacent doubles but does not amplify the reviewed lag-8 baseline enough to explain the Eyes' gap-4 signal in the controlled stress model.
- [Stage 78 — lag-4 H4 audit](reports/stage78-h4-audit.md): the provisional repair is non-injective, the current permutation optimizer fails a stronger synthetic recovery gate, and E1/W1 re-convergence does not uniquely identify lag 4.

## Reproduction

Run the commands listed in each report. Python source, canonical ciphertext, saved logs and SHA-256 manifest are included.

## Scope

This contribution evaluates families inherited from the supplied handoff. It does not claim a historical key, a verified Finnish plaintext, or a complete decoder.
