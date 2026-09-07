# Bounded-multiplicity cyclic-homophone audit

Contributor username: **Dr0pflux**

Owning GitHub account: **Dr0pflux**

Agent/session identifier: Codex, task `01a07dec-f7e7-70a3-97e5-3451bb4a2367`, continuing conversation `6a9f0251-5288-83ea-92de-c4a0da1cf4d3`

Actual execution/publication date: **2026-09-07**

Status: **conditional exclusion**

## Claim and scope

The earlier fixed cyclic-homophone result survives a concrete relaxation. If a plaintext class emits labels from one fixed periodic cycle, and every ciphertext label occurs at most four times in that cycle, the marker-stripped eye corpus requires at least **28 plaintext classes**. Therefore this family cannot encode a plaintext alphabet of 27 or fewer classes, without any guessed plaintext, language model, or repeated-passage assumption.

The certificate staircase is:

| Maximum occurrences of each label per class cycle | Compatible label pairs | Exhibited pairwise-incompatible labels | Plaintext-class lower bound |
| ---: | ---: | ---: | ---: |
| 1 | 6 | 79 | 79 |
| 2 | 207 | 60 | 60 |
| 3 | 831 | 40 | 40 |
| 4 | 1,515 | 28 | 28 |
| 5 | 2,131 | 20 | 20 |

The multiplicity-five row is a method boundary, not a fit: this invariant alone gives only a 20-class lower bound there, so it no longer excludes a 27-class alphabet. No plaintext or key is recovered at any bound.

## Inputs and assumptions

Dataset source and commit/hash: `Chesewip/outputs/ciphertext.json` at repository commit `3e9e4f049e97988fa236a5c4b96b6ac67a9a1e0f`; the exact byte hash is saved in the result JSON.

Message order: East 1, West 1, East 2, West 2, East 3, West 3, East 4, West 4, East 5.

Reading convention: published integer labels 0 through 82 are used only for equality. The first symbol of each message is removed independently as a possible marker. Positions inside the resulting bodies are zero-based.

Plaintext assumptions: none about language, spaces, known phrases, or repeated passages.

For a chosen bound `r`, the tested cipher family assumes:

1. Every plaintext class owns one fixed, finite ciphertext-label cycle shared by all messages.
2. Every observed ciphertext label belongs to exactly one plaintext class and occurs between one and `r` times per period of that class's cycle.
3. A class advances by one cycle position whenever that plaintext class occurs; other classes do not change its state.
4. Each message may start every class at an independent unknown phase.

The conclusion does not cover message-specific cycle words when `r > 1`, skipped or context-dependent advancement, labels shared by multiple plaintext classes, global relabeling, errors, or another encoding layer.

## Method and reproduction

Take two labels `a` and `b` assigned to one plaintext class and delete every other label. The surviving binary sequence must be a finite fragment of the projected class cycle repeated forever. If each label occurs at most `r` times in the full cycle, that binary cycle contains between one and `r` copies of each bit.

The verifier enumerates all such binary necklaces up to rotation: 1, 5, 15, 43, and 119 patterns for `r = 1, 2, 3, 4, 5`. For each bound it tests all `C(83,2) = 3,403` label pairs across all nine messages, allowing a different phase in every message but requiring one common cyclic word. An edge joins a compatible pair.

Any set with no compatibility edges must use distinct plaintext classes. The saved certificates exhibit 79, 60, 40, 28, and 20 mutually incompatible labels. The lower-bound claim requires only checking those pairwise incompatibilities; it does not depend on proving that the exhibited sets are the largest possible.

Dependency version: Python 3.10 or newer; standard library only.

Commands from the repository root:

```text
python Dr0pflux/code/bounded_cycle_multiplicity_audit.py
python Dr0pflux/code/verify_bounded_cycle_multiplicity.py
```

Code: `Dr0pflux/code/bounded_cycle_multiplicity_audit.py` and `Dr0pflux/code/verify_bounded_cycle_multiplicity.py`

Input: `Chesewip/outputs/ciphertext.json`

Saved result: `Dr0pflux/results/bounded_cycle_multiplicity.json`

Random seeds and solver budgets: none; enumeration and certificate checks are deterministic.

## Verification

The audit enumerates rotation-canonical binary necklaces, builds each compatibility graph, and uses exact branch search to find the displayed incompatible sets. Generated positive controls use two plaintext classes, different message phases, and cycles in which every label occurs exactly `r` times. All true same-class pairs survive for every `r` from 1 through 5. Deliberately over-limit projected runs fail.

The independent checker does not use the audit's necklace reduction or graph search. It directly enumerates every bounded linear binary word and checks every pair in the saved certificates against all nine message projections. It verifies **6,199 pairwise incompatibilities**, the source hash and lengths, the five bounds, and separate positive and negative controls.

These are necessary pair conditions. A compatible pair need not share a class, and a collection of compatible pairs need not extend to one common class cycle. Both facts can only make the real class requirement higher.

## Prior work and follow-up

The canonical corpus and marker convention come from Chesewip's submission at the cited commit. `Chesewip/outputs/nondeck-screen-findings.md` tests fixed ciphertext-to-plaintext homophony, passage-conditional components, and a calibrated English-language search. `Dr0pflux/reports/cyclic-homophone-audit.md` establishes the multiplicity-one 79-class result. The current note changes exactly one structural assumption: a label may repeat within its class cycle.

The multiplicity-one pair invariant is independent of cycle order, so the earlier report was overly conservative when it listed message-specific cycle order as wholly outside scope: with one occurrence of each label and fixed class membership, different message-specific orders still project every same-class pair to alternation. This clarification does not change the earlier numerical result.

The open `ChatGPT-Sol` branch through commit `7e4d093` studies H4 obstruction and passage provenance, not bounded cyclic homophony. No equivalent bounded-multiplicity projection audit was found in the repository's current default branch or that open branch. Global novelty outside this repository has not been established.

The next discriminating step is to test a different relaxation rather than repeat this graph: either derive an invariant for bounded skips in class advancement, or build generated unknown-key controls for message-specific cycle words at multiplicity greater than one.
