# Plaintext-difference bounds without guessing the plaintext

**The cipher remains unsolved.** This note gives necessary bounds on how much two aligned plaintexts must differ under the deterministic deck-cipher model. It also gives a deliberately engineered counterexample that reproduces two real ciphertext prefixes. The counterexample is not a proposed Noita key or meaningful plaintext.

The specific bounds and construction are candidate new contributions from this investigation. I did not find them in the reviewed progress documents, local community wiki, or targeted public searches. That is not a claim of worldwide priority; private discussion and unindexed work were not checked.

## Main results

With a common initial deck, the first 50 symbols of East 1 and West 1 require at least **three plaintext differences**, including the first symbol. This bound is sharp in the unrestricted deterministic deck model: a reversible construction with 53 plaintext symbols attains it exactly.

For the first 99 symbols of that pair:

- Arbitrary per-letter deck permutations require at least **nine** aligned plaintext differences.
- A fixed-anchor, character-selected swap followed by a common arbitrary shuffle requires at least **eleven**.

These are Hamming-distance bounds at the existing alignment, not insertion/deletion distances. They do not assume that any published isomorph represents repeated plaintext, and they impose no English or Finnish alphabet hypothesis.

## Why ciphertext conflicts force plaintext differences

Consider two evolving decks, A and B. At any instant, associate the label at each position in A with the label at that same position in B. This defines a bijection R between their labels.

If both messages next apply the same positional permutation, R remains unchanged. Consequently, if their plaintexts agree at positions s+1 through t, the output pairs from position s through t must all fit one bijection.

Suppose the observed pairs at s and t instead require either one label to map to two labels, or two labels to map to one. Then **at least one plaintext difference must occur in the interval (s,t]**.

The inclusion of output s is intentional: it describes the deck states after that position, before the proposed common sequence begins. This argument is specific to the stated deck model, where output is read at a fixed position after the update. It must not be assumed for every mechanism casually called a deck cipher.

Each such conflict gives an interval that a plaintext difference must hit. Selecting the minimum number of positions that hit all intervals is an exact interval-stabbing problem. Equivalently, one can partition the output pairs into the fewest consecutive blocks that each fit a partial bijection. The resulting optimum is a necessary lower bound; it need not be attainable by an actual cipher.

### Two short certificates in the actual messages

All positions in this note are **one-based**; JSON and scripts use zero-based indices.

| Output observations | Why they conflict | Required plaintext difference |
|---|---|---|
| At position 22: 29 → 29. At position 26: 80 → 29. | A bijection cannot give two different inputs the same output. | Somewhere in positions **23–26** |
| At position 28: 40 → 30. At position 34: 40 → 25. | A bijection cannot send one input to two different outputs. | Somewhere in positions **29–34** |

These intervals are disjoint. The first outputs, 50 and 80, additionally require different first plaintext symbols if both messages start from the same deck. Therefore the first 50 positions contain at least three plaintext differences.

If the messages have independent initial decks, the first-symbol argument disappears; the two interval constraints remain valid. If the first symbol is external metadata rather than a cipher input, that alternative must be modeled explicitly.

The interval calculation was applied to all 36 message pairs over their common available lengths. The results are in `plaintext_change_bounds.json`. A chosen minimum hitting set is only a mathematical witness, not a recovery of the actual difference positions.

## An exact construction showing the three-change bound is sharp

I constructed a fixed alphabet of 53 tokens, each assigned its own fixed permutation of 83 cards. The two constructed token sequences differ only at positions **1, 26, and 34**. Starting from the same initial deck, they reproduce the actual first 50 ciphertext symbols of East 1 and West 1 exactly.

Every token has a distinct non-top output-source position. The construction is therefore reversible and prevents adjacent equal outputs for every input sequence, rather than merely happening to avoid them in this example.

| Positions | Observed ciphertext relationship | Constructed plaintext relationship |
|---|---|---|
| 1 | Different | Different |
| 2–25 | Equal | Equal |
| 26–29 | Different | Different only at 26 |
| 30–33 | Equal | Equal |
| 34–37 | Different | Different only at 34 |
| 38–50 | Equal | Equal |

During all thirteen matching outputs at positions 38–50, the two decks still differ in **seven positions**. They never become identical anywhere after their first differing output.

This construction uses arbitrary shuffles engineered for these prefixes. Its 53 tokens have no linguistic interpretation; it does not fit the remaining ciphertext and does not establish that a 27-letter or 40-letter cipher can attain the same bound. Its purpose is to demonstrate the sharp bound in the unrestricted model and distinguish output agreement from internal-state agreement.

Files: `sharp_prefix_counterexample.py` and `sharp_prefix_counterexample.json`. An independent inverse-index replay verifies every shuffle, the distinct source positions, both real prefixes, the three token differences, and the seven persistent state differences in `checked_plaintext_change_bounds.json`.

## A stronger bound when letter shuffles differ only slightly

For a permutation R on n symbols, define

```text
w(R) = (n − number of odd-length cycles of R) / 2
```

Fixed points count as odd-length cycles. Equivalently, w is the sum of floor(cycle length / 2) over the cycles. It is the minimum number of transpositions or three-cycles needed to express R: either generator changes the number of odd cycles by at most two, and each cycle can be decomposed using that many generators. Thus w is subadditive and unchanged by conjugation.

A partial bijection consists of closed cycles and open paths. If a nontrivial component has v vertices, any completion contributes at least floor(v/2) to w. Closing each open path attains the sum of these lower bounds. Joining components cannot reduce it.

Suppose a pair of different plaintext letters changes the relative deck permutation by an operation of weight at most B. After k plaintext differences, its weight cannot exceed Bk. The visible partial bijection in any subsequent common-plaintext block therefore has weight at most Bk.

For a fixed-anchor swap plus a common shuffle, B = 1: comparing two letter operations gives a conjugated three-cycle or transposition. For an anchored three-cycle plus a common shuffle, B = 2: the relative operation moves at most five positions. The common shuffle and initial key may be arbitrary.

A dynamic program considers every possible placement of plaintext differences, requiring each output block to be bijection-consistent and to respect its cumulative weight budget. No particular block is assumed to be shared plaintext beforehand.

| East 1 / West 1 prefix length | Arbitrary permutations | Fixed-anchor swap + common shuffle | Anchored three-cycle + common shuffle |
|---|---:|---:|---:|
| 29 | At least 2 differences | At least 3 | At least 2 |
| 37 | At least 3 | At least 4 | At least 3 |
| 50 | At least 3 | At least 4 | At least 3 |
| 99 | At least 9 | At least 11 | At least 9 |

Only the unrestricted three-change bound for the first 50 positions has been shown attainable. The other entries are lower bounds. They do not exclude the listed cipher families outright; they constrain the plaintexts those families could encode.

Files: `shuffle_weight_bounds.py`, `shuffle_weight_bounds.json`, `verify_shuffle_weight_bounds.py`, and `verify_weight_dp.py`.

## Returning to agreement can be common without a state reset

A [public research notebook](https://github.com/GarethLowe/Noita-Eyes/blob/claude/bootstrap-files-extract-myxfgl/NOTEBOOK.md) rejects the broad deck model on the basis of long output reconvergence, using an estimate appropriate to strongly mixed independent states. That conclusion does not follow for nearby states under structured shuffles. The distinction is already implicit in the community's [deck-cipher discussion](https://github.com/Lymm37/eye-messages/wiki/Deck-Cipher); the new work here quantifies it and gives the actual-prefix counterexample above.

There is also a simple exact calculation. Let two decks differ in r positions and subsequently apply identical permutations. That count remains r. If plaintext selections are independent and uniform over all n−1 non-top source positions, the probability of L consecutive matching outputs immediately after a differing output is

```text
((n − r)/(n − 1)) × ((n − 1 − r)/(n − 1))^(L − 1).
```

Before the first match, one disagreement is at the top, leaving n−r matching bottom positions. After a match, all r disagreements are in the bottom positions. This gives the two factors directly.

For the simple top/selected/next-card three-cycle followed by a bottom rotation, changing one input creates r = 4 or 5. With 83 cards and all 82 selections equally likely, averaging over the changed pair gives a **44.9113%** chance of thirteen immediately matching subsequent outputs. In 10,000 generated trials, the observed fraction was **44.83%**. A separate 27-selection control gave **46.56%**; the uniform-82 formula does not apply to that restricted alphabet.

These are generated controls and an explicitly stated input model, not probabilities for Noita's unknown plaintext. They show that large state space alone cannot justify a tiny reconvergence probability. Files: `reconvergence_controls.py` and `reconvergence_controls.json`.

## Validation and practical use

The checks include 300 generated arbitrary-permutation examples, 100 exhaustive short interval problems, independent dynamic programming for all 36 real message pairs, 120 exhaustive partial-permutation completion checks, 200 exhaustive short partition problems, and 180 generated small-update ciphers. A separate bit-set dynamic program independently reproduced all twelve real-data weight bounds. The engineered prefix replay was verified independently of its generator.

The practical use is a fast rejection test for paired plaintext proposals. A candidate must differ somewhere in every forced-change interval; under a restricted shuffle family, it must also meet the stronger cumulative bounds. A candidate that passes remains unverified. This lets us challenge message templates before searching for an alphabet or key.

Reproduce directly with Python; no project build is used:

```powershell
python plaintext_change_bounds.py
python sharp_prefix_counterexample.py
python verify_plaintext_change_bounds.py
python shuffle_weight_bounds.py
python verify_shuffle_weight_bounds.py
python verify_weight_dp.py
python reconvergence_controls.py
```

The computations use the existing published trigram transcription. They do not independently verify the game glyph extraction or establish the cipher's language.
