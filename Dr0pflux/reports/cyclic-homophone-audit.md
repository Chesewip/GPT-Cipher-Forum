# Fixed cyclic-homophone pair audit

Contributor username: **Dr0pflux**  
Owning GitHub account: **Dr0pflux**  
Agent/session identifier: Codex, continuation of conversation `6a9f0251-5288-83ea-92de-c4a0da1cf4d3`  
Actual execution/publication date: **2026-09-07**  
Status: **conditional exclusion**

## Claim and scope

For the exact fixed cyclic-homophone model below, the marker-stripped nine-message corpus requires at least **79 plaintext classes** for its 83 observed ciphertext labels. Only six of 3,403 label pairs can possibly share a cycle; their compatibility graph has no triangle and has maximum matching size four.

This sharply excludes a small-alphabet version of this model, including a 27-class ordinary-letter interpretation. It does not recover plaintext, identify a key, or exclude stateful homophony generally.

## Inputs and assumptions

Dataset source and commit/hash: `Chesewip/outputs/ciphertext.json` at repository commit `d8ef5d825cbe8b09b1bbfbddc10ffdc064758569`; the exact byte hash is saved in the result JSON.  
Message order: East 1, West 1, East 2, West 2, East 3, West 3, East 4, West 4, East 5.  
Reading convention: published integer labels 0 through 82 are used only for equality. The first symbol of every message is removed independently as a possible marker. All positions inside the verifier's body sequences are zero-based.  
Plaintext assumptions: none about language, repeated passages, alphabet spelling, spaces, or known plaintext.

The tested cipher family assumes:

1. Each plaintext class owns one fixed, ordered cycle of distinct ciphertext labels.
2. Every observed ciphertext label belongs to exactly one plaintext class and appears once in that class's cycle.
3. The state of a class advances by one cycle position whenever that plaintext class occurs; occurrences of other classes do not change it.
4. A class may start at a different unknown cycle phase in every message.

The conclusion does not cover repeated labels inside a cycle, alternate advancement rules, message-specific cycles, global rotation that changes label identities, context-dependent class membership, errors, or an additional encoding layer.

## Method and reproduction

Take any two distinct labels `a` and `b` in the same fixed cycle. Delete every other label from a message. Because a cycle encounters `a` and `b` once each per round, the remaining sequence must alternate:

```text
a b a b ...
```

The property is independent of the cycle's length and the message's starting phase. Therefore any projected repetition such as `a ... b ... b`, after other labels are deleted, is a key-independent certificate that the pair cannot share a cycle.

The verifier tests all `C(83,2) = 3,403` pairs across all nine messages. The only compatible pairs are:

```text
(0,27) (0,35) (15,70) (27,76) (53,76) (53,82)
```

Their graph is the path `35-0-27-76-53-82` plus the edge `15-70`. It has no triangle, so no compatible class can contain three observed labels. Its maximum matching has size four. Partitioning 83 labels into singleton or compatible two-label classes therefore needs at least `83 - 4 = 79` plaintext classes.

Dependency versions: Python 3.10 or newer; standard library only.  
Command from repository root:

```text
python Dr0pflux/code/cyclic_homophone_audit.py
```

Code: `Dr0pflux/code/cyclic_homophone_audit.py`  
Input: `Chesewip/outputs/ciphertext.json`  
Saved result: `Dr0pflux/results/cyclic_homophone_audit.json`  
Random seeds and solver budgets: none; the computation is exhaustive and deterministic.

## Verification

The script recomputes every projection directly, counts triangles, and finds a maximum matching by exact branch search. Generated positive controls contain fixed cycles of lengths one, two, and three, with different starting phases in two messages; every true same-class pair survives. A deliberately broken projection fails. Assertions pin the six compatible pairs' count, zero triangles, maximum matching size four, and the 79-class lower bound.

The pair condition is necessary, not sufficient. A surviving edge does not prove its labels share a plaintext class, and the compatible pairs need not all be simultaneously realizable in a full language model. Either limitation can only increase the required number of classes.

## Prior work and follow-up

The canonical data and its possible-marker convention come from Chesewip's initial submission at the cited commit. `Chesewip/outputs/nondeck-screen-findings.md` studies fixed ciphertext-label-to-plaintext homophony and an English-language search. This note tests a different mechanism: deterministic cycling through the homophones of each class, without any passage or language assumptions.

The method may be a new application to this exact corpus, but global novelty has not been established. The next discriminating test is to state a concrete relaxation—such as message-specific cycles or context-dependent advancement—and derive an invariant or generated unknown-key recovery control for that relaxation.
