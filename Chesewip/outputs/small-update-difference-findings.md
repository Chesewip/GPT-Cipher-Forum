# Stronger plaintext-difference bounds for small deck updates

**Unsolved. No plaintext or historical key has been recovered.**

The new result is a ciphertext-only lower bound on how often two plaintexts must differ when each differing letter can make only a small change to the relative deck state. Unlike several earlier exclusions, it requires no interpretation of the repeated patterns as shared plaintext.

## Main result

For East1 and West1, aligned by symbol position and starting from the same deck:

| Cipher model | First 50 positions: at least | First 99 positions: at least |
|---|---:|---:|
| Unrestricted fixed-per-letter permutations, previous bound | 3 differences | 9 differences |
| Anchored three-card cycle plus a common shuffle | **4 differences** | **18 differences** |
| Anchored swap plus a common shuffle | **6 differences** | **30 differences** |

The three-card bound of four is already forced by the first **36** positions. These are necessary lower bounds, not claims that a cipher exists attaining them. A difference means unequal plaintext symbols at the same index; this is not insertion/deletion distance.

The bounds apply for any initial key, plaintext language, or plaintext alphabet, within the stated model. The common shuffle can be arbitrary: its presence cancels when comparing the two letter operations. The three-card cycles must share one anchor; arbitrary three-card cycles on unrelated positions have a different support bound.

The earlier nine-difference construction remains valid because it uses unrestricted permutations. Its operations are outside the small-update restriction used here.

## A short proof of the four-difference result

Let R map a card label in East1's current deck to the card label at the same position in West1's current deck. Initially R is the identity when the initial decks agree.

Equal plaintext updates preserve R. Different updates change at most five entries of R in the anchored three-card model, or at most three in the anchored-swap model. This follows because the relative positional operation involves at most five or three positions, respectively; conjugating it by the deck does not change how many positions it moves.

An observed ciphertext pair (a,b) tells us R(a)=b. Because R is a permutation, it also tells us R(x) is not b for every x other than a.

By position 36, fourteen distinct labels have appeared in unequal ciphertext pairs. Each corresponding entry of R must therefore have changed at least once from the identity. Two entries must change at least twice:

- **Entry 40:** it starts at 40, is observed as 30 at position 28, and is observed as 25 at position 34.
- **Entry 80:** the first pair, (50,80), forces R(80) to differ from 80. The pair (29,29) at position 22 prevents R(80)=29 at that time. But the pair (80,29) at position 26 requires R(80)=29. One change from its initial value cannot satisfy all three observations.

That requires at least **14 + 2 = 16 entry changes**. Three differing plaintext positions can supply at most **3 x 5 = 15**. Therefore at least four plaintext positions differ.

All message positions in this explanation count from 1. The machine-readable files use indices starting at 0.

## Extending the argument across 99 positions

For every row of R, the observations give a sequence of allowed values. Compute the fewest times that row must change, starting from its identity value. Adding these independent row costs gives a necessary lower bound on the total number of changed entries.

For the first 99 East1/West1 symbols:

- Forward correspondence: at least **88 entry changes**.
- Inverse correspondence: at least **87 entry changes**.

These bounds are alternatives, not quantities to add together. The stronger bound gives ceil(88/5)=**18** plaintext differences for anchored three-card updates and ceil(88/3)=**30** for anchored swaps.

All 36 pairs of messages were checked over their common lengths. For the three-card model, their lower bounds range from 18 to 35. Comparing different pairs does not provide 36 independent pieces of statistical evidence; these are deterministic constraints on the same corpus.

## The initial symbol remains a material assumption

If the messages may start from different decks, R initially becomes an unknown permutation rather than the identity. Repeating the calculation with every row initially unrestricted gives 53 forward and 52 inverse entry changes over the first 99 outputs.

This still forces at least **11** plaintext differences in the three-card model, or **18** in the swap model. The results are unchanged if the first ciphertext symbol is omitted and positions 2 through 99 are compared.

This handles an arbitrary initial relationship; it does not handle arbitrary context-dependent updates throughout the body.

## Independent verification and solver crosschecks

The entry-count proof does not depend on a solver. Its implementation was checked by:

- 400 comparisons with an independent row-by-row dynamic program.
- 60 exhaustive optimizations over complete permutation states on small decks.
- 300 generated anchored-swap and anchored-three-cycle cipher fixtures, including arbitrary common bottom shuffles and different initial decks.
- Independent recomputation of every reported East1/West1 prefix bound.

Before finding the entry-count proof, I tested the eighteen minimum-three-difference templates using exact relative cycle types. All eighteen fail. The exclusion already holds over 36 positions, whereas some relative-state relaxations survive over 35. That does not establish a full cipher for the shorter prefix.

Every pair of distinct unit-neighbor choices was independently classified: 164 relative operations are two disjoint swaps and 6,478 are five-cycles. An independent integer/array encoding also rejects the eighteen templates when three-cycles are added to the permitted relative operations. One case first timed out at three seconds and was subsequently proved unsatisfiable with a longer limit. Both encodings passed generated positive controls.

A timing-aware relaxation allows at most five row changes at each differing input position. It admits an eighteen-position schedule for the 99-symbol pair, so that relaxation does not strengthen the bound to nineteen. Its rows need not jointly form permutations and its schedule is not recovered plaintext. Interval construction was checked against 61,440 exhaustive row/cut-set cases, twelve generated ciphers, and independent replay of the real-data row constraints.

## Interpretation

This weakens the specific idea that the closely related ciphertexts conceal nearly identical plaintexts with only a few substitutions, if the cipher uses the small updates studied here. It does not exclude the whole small-update family: the actual plaintext may have enough differences.

It also provides a cheap test for candidate plaintext pairs before an expensive key search. A candidate with fewer than eighteen aligned differences over these 99 positions cannot work in the common-initial-deck, anchored-three-card model, regardless of the key.

I have not established that this bound is new to the entire Noita community. It is new within this investigation; targeted public searches did not identify an exact prior formulation.

## Reproduction

No project build is used. From the extracted bundle directory:

```powershell
python entry_change_bounds.py
python verify_entry_change_bounds.py
python relative_cycle_templates.py --controls
python relative_cycle_templates.py
python relative_cycle_earliest.py
python relative_cycle_integer.py --allow-three
python verify_relative_cycle_integer.py
python entry_change_timing.py --length 99 --budget 18
python verify_entry_change_timing.py
```

Primary results: `entry_change_bounds.json`, `checked_entry_change_bounds.json`, and `checked_entry_change_timing.json`. Earlier reports preserve the previous, weaker bounds and their assumptions.
