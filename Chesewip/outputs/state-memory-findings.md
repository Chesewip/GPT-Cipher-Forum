# Returning to message structure: observed memory and the first symbol

Contributor and owning account: Chesewip. Agent/session: the owner's continuing Codex Noita investigation. Executed/published: 2026-09-07. **No authentic plaintext or key recovered.**

This comparison pauses coordinate fractionation and asks which parts of the observed ciphertext could select a decoding table. The main result is a counterexample to overinterpreting the patterns: **an engineered cipher with only 83 observable states and 19 input tokens reproduces every one of the 1,027 body symbols**, including all seven listed passage-equality hypotheses and every shared-opening hypothesis below. Its entire state is the previous ciphertext symbol; it has no additional hidden state. It prevents doubled output symbols for every possible token sequence.

This works when the first raw symbol is treated as external metadata. If that symbol instead supplies the previous-symbol state, a short contradiction follows from a shared-opening assumption and two late-passage assumptions. The result therefore distinguishes both mechanisms and interpretations of the first symbol. It does not decide which interpretation is authentic.

The constructed tokens have no linguistic meaning. A second experiment exposes the model's limited explanatory power: the same fitted 27-token passage produces **81 different equality patterns across the 83 possible starting states**. Only three starts reproduce its observed pattern. Exact reproduction of selected occurrences does not establish a mechanism that reliably preserves such patterns.

## Observations, hypotheses and scope

The input remains [ciphertext.json](ciphertext.json), SHA-256 `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`. Canonical triangular grouping is retained; labels are used only for equality, not arithmetic. Message order is E1, W1, E2, W2, E3, W3, E4, W4, E5. There are 1,036 raw symbols and 1,027 after removing the first symbol of each message. Every body starts with label 66. There are no adjacent equal labels within a raw message.

The earlier [transition-preserving pattern audit](shared-pattern-testing.md) already found recurrent ciphertext equality patterns not reproduced in its sampled first-order conditional randomizations. That supports looking beyond individual frequencies and adjacent-pair counts. It does not establish repeated plaintext or a particular state mechanism.

We keep eight assumption sets separate. A tuple `(A,s,B,t,n)` means that n plaintext tokens starting at raw index s in A equal those starting at raw index t in B. Every index below is zero-based; raw position 0 is the possible header.

| Set | Assumed equal passages |
| --- | --- |
| Early | `(W1,37,W1,67,15)`, `(E2,42,E2,77,15)`, `(W1,37,E2,42,15)`, `(W1,37,E2,77,15)` |
| Late | `(E4,71,W4,74,27)`, `(E4,71,E5,72,27)` |
| Weak addition | `(E1,43,E1,71,6)` |
| Prefix | For each pair of messages, their longest exactly matching ciphertext opening starting at raw position 1 is assumed to have matching plaintext |

The eight tested combinations are none, early, late, early+late (named `strong`), early+late+weak (`full`), prefix, late+prefix, and full+prefix. The name `strong` only distinguishes it from the weak short E1 relation; none of these plaintext claims is established by ciphertext alone. The 36 prefix relations are saved explicitly. Exact equality of ciphertext does not automatically prove equality of plaintext when the selecting states differ.

## Mechanisms compared

Write the encoder as `C[t] = T(context[t], P[t])`. For each context, its table maps distinct input tokens to distinct output labels, so decoding is unambiguous given that context. Different contexts may have unrelated tables.

We compare:

- One fixed table, independent of position and history.
- A different shared table at each absolute position, with no required period.
- Tables selected by the previous k ciphertext symbols, for k = 1, 2, 3, 4.
- Tables selected by the single ciphertext symbol d positions back, for d = 2 through 12.

The last two families receive two first-symbol treatments. Under `primer`, history may include raw position 0; positions before enough history exists are initialization. Under `metadata`, position 0 is excluded from history, and enough body symbols must be available before a table is tested. Equalities involving an untested initialization position are counted as skipped, not silently asserted to hold. Fixed and absolute-position tables cover all body positions.

This gives 32 model settings and eight assumption sets, or **256 comparisons**. These are arbitrary tables, not cyclic shifts, additive feedback, or the coordinate-function models studied previously. The [community ciphertext-autokey discussion](https://github.com/Lymm37/eye-messages/wiki/Ciphertext%E2%80%90Autokey-%28CTAK%29) already distinguishes general permuted tables from arithmetic autokey and discusses initialization. We are not introducing that family as a new cipher type.

## Results and what a fit means

| Table selector | No plaintext hypotheses | Seven passage hypotheses (`full`) | Seven passages plus shared openings |
| --- | --- | --- | --- |
| Fixed | 83-token fit | Contradiction | Contradiction |
| Absolute position | 9-token fit | Contradiction | Contradiction |
| Previous symbol, raw first symbol as primer | 19-token fit | 19-token fit | Contradiction |
| Previous symbol, raw first symbol excluded | 19-token fit | 19-token fit | 19-token fit |
| Previous two symbols, either treatment | 4-token fit | 4-token fit | 4-token fit |
| Previous three or four symbols, either treatment | 3-token fit | 3-token fit | 3-token fit |
| Single symbol two or three places back, either treatment | 19-token fit | 19-token fit | 19-token fit |
| Single symbol four through twelve places back, either treatment | 18-20-token fits | Contradiction | Contradiction |

The arbitrary-position contradiction depends on the weak short E1 relation, reproducing the earlier [non-deck screen](nondeck-screen-findings.md). All tested delays from 4 through 12 already fail with the two late-passage assumptions alone. Delay 12 also fails with the early set alone. These exclusions are conditional, and do not cover all delayed feedback or message-specific tables.

There are **154 constructed token fits and 102 contradiction certificates**. The fits are partial-table witnesses covering the tested positions. Each row is injective and can be completed on the same token alphabet by assigning unused output labels; wholly unobserved contexts can receive arbitrary tables. No claim about language follows. In particular, allowing more ciphertext history creates many sparsely observed contexts: the three-token fits illustrate flexibility, not evidence for a three-letter plaintext.

For each tested setting, the construction's token count equals the maximum distinct outputs observed in one context, giving an exact minimum under those particular constraints. This is a structural minimum, not a recovered alphabet size. The 83-token fixed-table case simply assigns every ciphertext label its own token.

Equality implications are explicit: two occurrences with the same context and output must have the same decoded token. Assumed plaintext equalities join further occurrences. A contradiction occurs if those joins equate different outputs within one context. For surviving cases, a coloring assigns token meanings so that every context has distinct tokens for its distinct outputs. The independent verifier checks the actual assignments; it does not assume a successful coloring is authentic text.

## A compact contradiction that depends on the first symbol

Let `D(previous,current)` denote any deterministic decoder using just the previous ciphertext label. The following are direct observations:

| Location | Previous label | Current label |
| --- | ---: | ---: |
| W1, raw position 1 | 80 | 66 |
| W3, raw position 1 | 34 | 66 |
| E4, raw position 77 | 43 | 60 |
| W4, raw position 80 | 34 | 66 |
| E5, raw position 78 | 80 | 25 |

The two late-passage hypotheses identify the last three plaintext positions, so:

```text
D(43,60) = D(34,66) = D(80,25).
```

If W1 and W3 also begin with the same plaintext token and their raw first symbols supply the previous-symbol state, then:

```text
D(80,66) = D(34,66).
```

Together they require `D(80,66) = D(80,25)`, contrary to injectivity in the context 80. This uses neither a numerical operation nor the weak E1 relation. It also does not require the token transition to be invertible as a function of previous state.

If raw position 0 is metadata and initialization is independent of its value, the first two rows are not those decoder calls. The contradiction no longer follows. Indeed, the complete metadata construction below supplies a common initial state and matching first plaintext tokens, showing this escape is realizable.

## Complete one-symbol-memory counterexamples

The two complete constructions use **19 token-selected permutations of 83 states**. To encode token p from state s, output `key[p][s]` and make that output the next state. Each permutation has no fixed points, and the 19 images at any fixed state are all different. Therefore:

- Every token sequence can be encrypted indefinitely.
- The token can be uniquely decoded from the previous state and current output.
- Adjacent output labels are never equal.
- The previous ciphertext label is the whole dynamic state; there is no extra hidden state.

The first key uses each raw first symbol as its initial state and fits all seven passage hypotheses. It does not satisfy the additional shared-opening hypotheses.

The second key excludes the raw first symbol as metadata, starts every message from state **43**, and emits the first body label 66 using token **0** in every message. It reproduces all nine complete bodies and satisfies all seven passage hypotheses plus all 36 prefix hypotheses. State 43 and token 0 are construction choices, not proposed discoveries about the game. The metadata values are preserved as supplied; this mechanism does not explain their origin or why they have those particular values.

Both use exactly 19 tokens. This is optimal in the stated model because label 26 has 19 distinct observed successors, which require 19 different input choices from that state. The proof is a lower bound from the observations plus a complete realizing key. It does not suggest that Noita's real plaintext alphabet has 19 letters.

The keys are constructed by grouping observed edges whose inputs are assumed equal, assigning tokens while preserving distinct incoming and outgoing edges, and extending each token's partial mapping to a permutation. The extension avoids every diagonal edge and every edge already assigned to another token. The independent verifier checks all **1,577 state/token transitions per key**, all 1,027 encrypted and decrypted body positions, and every specified equality.

These are intentional overfits with large keyed tables. They demonstrate that fitting these finite observations and passage assumptions does not logically require a deck or additional hidden state. They do not establish that a small-memory table cipher is historically plausible or that it explains why the repeated patterns occur.

## Testing whether fitted patterns transfer to other starts

For each complete key, take its fitted token sequence for W1's 15-position passage and E4's 27-position passage. Encrypt exactly that same sequence from each of the 83 possible initial states. Count distinct ciphertext equality patterns, ignoring the names of the output labels.

| Engineered key | Passage | Distinct patterns among 83 starts | Starts matching the observed pattern |
| --- | --- | ---: | ---: |
| Raw first symbol as primer | W1, position 37, length 15 | 53 | 4 |
| Raw first symbol as primer | E4, position 71, length 27 | 81 | 3 |
| Raw first symbol as metadata | W1, position 37, length 15 | 48 | 4 |
| Raw first symbol as metadata | E4, position 71, length 27 | 81 | 3 |

A generated cyclic-feedback control uses 19 distinct nonzero shifts modulo 83 and the same two token sequences. Each produces **one equality pattern across all 83 starts**, as expected: changing the start adds a common offset to every output. This tests the pattern-transfer diagnostic; it is not a successful cyclic fit to the eyes, and its invariant pattern need not equal the observed Eye pattern.

The counts for engineered keys are exact properties of those keys. They are not chance probabilities for the Eye data: both the keys and token passages were selected using that data, and unknown historical states need not be uniformly sampled. There is no real held-out ciphertext here.

The distinction between observed matching patterns and a cipher that preserves them across arbitrary starting states is already present in the [community discussion of ciphertext autokey](https://github.com/Lymm37/eye-messages/wiki/Ciphertext%E2%80%90Autokey-%28CTAK%29). Our contribution is the concrete full-body counterexamples, the first-symbol-sensitive certificate, the bounded table comparison, and their independent checks. No global novelty claim is made.

## Controls, verification and reproduction

Five generated controls cover fixed tables, absolute-position tables, a previous-symbol table, a two-symbol-window table and a delayed table using the symbol four places back. Seeds are 909300 through 909304. They use 27 input tokens and the same lengths and imposed passage/prefix equalities. Every control survives the unknown-table compatibility test at its generating setting. Its generating tables and actual plaintext are also replayed independently.

These controls test soundness and successful construction of compatible witnesses. They do **not** establish blind recovery of the original generated key, plaintext or mechanism. Wrong mechanisms have not been classified on a large independent benchmark.

[state_memory_comparison.py](state_memory_comparison.py) and [state_memory_comparison.json](state_memory_comparison.json) retain all 256 cases, the five controls, both full keys and token streams, every counterfactual encryption and the cyclic control. [verify_state_memory_comparison.py](verify_state_memory_comparison.py) imports no discovery code. It independently reconstructs contexts, validates each fit by actual table consistency, checks contradiction paths against allowed hypotheses, replays complete keys, and groups counterfactual outputs using pairwise equality matrices. [checked_state_memory_comparison.json](checked_state_memory_comparison.json) records 256 checks and 143 conditional path steps, plus the controls and full constructions.

From this directory, using Python 3.10 or newer and only the standard library:

```powershell
python state_memory_comparison.py
python verify_state_memory_comparison.py
```

The verifier alone checks the saved results without running construction again. No project build is involved. Authored text uses CRLF. Parent dataset hashes and the result-file hash are retained.

The next useful comparison should test whether a restricted mechanism produces the observed recurrence naturally across starting states and recovers authentic generated plaintext with an unknown key. Increasing history or allowing arbitrary tables can make finite fitting easier while making the mechanism less identifiable. The result here is a sharper separation of assumptions and explanatory requirements, not a new favored cipher family.
