# Shared-pattern tests and further key searches

**Unsolved. This round recovered no Noita plaintext or key and established no new exclusion of a cipher family.** It did strengthen the pattern audit by comparing the ciphertext against randomizations that preserve its local transition counts.

## The concrete pattern being measured

Five different nine-symbol strings in the first three messages share the equality pattern `ABCDECFAE`. For example:

```text
47 44 48 42 19 48 13 47 19
71 11 74 56  4 74 19 71  4
```

Both repeat their first, third, and fifth symbols at the same relative positions. The first string also occurs literally in two messages, but this duplicate counts only once. `recurrent_pattern_witness.json` records all five strings and their six locations, using zero-based positions.

This is a **ciphertext** pattern. It is not a proposed plaintext letter pattern. Matching equality patterns do not prove that the underlying plaintext passages match.

The statistic searches every nine-symbol window and takes the largest number of distinct literal strings sharing any equality pattern with at least three repeat constraints. Its observed value is five.

## A stricter comparison than independent random symbols

For each message separately, I generated random sequences preserving:

- Every symbol's count.
- Every ordered adjacent pair's count, including the absence of doubles.
- Message length and first and last symbols.

A second version additionally holds the shared beginnings fixed. The protected prefix lengths, in corpus order, are 25, 25, 25, 6, 10, 6, 21, 21, and 21 symbols.

| Randomization | Samples | Largest statistic seen | Samples reaching the observed five |
|---|---:|---:|---:|
| Adjacent-pair counts preserved | 2,000 | 2 | 0 |
| Pair counts and shared beginnings preserved | 2,000 | 3 | 0 |

The latter samples changed an average of 817.56 of the 1,036 positions; all 2,000 sampled corpora were distinct. The comparison therefore had substantial freedom to rearrange the messages.

This suggests the observed recurrence is not adequately explained by individual frequencies and adjacent-pair counts under this conditional randomization model. It supports investigating structure beyond those local counts. It does **not** prove repeated plaintext, distinguish a deck cipher from every alternative, or assign a probability to our preferred cipher hypothesis.

For either comparison, the add-one Monte Carlo estimate is 1/2,001. The statistic was selected during the broader investigation; that selection and other investigations are not corrected by this number. It should not be presented as a discovery-wide significance level.

The sampler constructs directed transition graphs, samples last-exit trees, and randomizes the remaining outgoing-edge orders to obtain uniform Euler trails. This construction follows the relationship between sequence shuffling and Euler trails described in [Kandel, Matias, Unger, and Winkler's sequence-shuffling paper](https://math.dartmouth.edu/~pw/papers/genome.pdf); the tree sampler uses [Wilson's loop-erased random-walk method](https://doi.org/10.1145/237814.237880). With fixed transition counts, these trails have equal probability under a time-homogeneous first-order Markov model, even if each message has its own transition probabilities.

The implementation checked 36,000 samples against exhaustively enumerated small examples, recorded descriptive distribution checks, and verified the required count invariants for every sampled Noita corpus. Files: `transition_pattern_audit.py` and `transition_pattern_audit.json`.

## Why preserving triples does not give a useful stronger test

I repeated the experiment preserving every consecutive three-symbol count. Random sampling found very few alternatives, so I enumerated the possibilities exactly.

| Triple-count constraint | Exact possible corpora | Statistic in every corpus |
|---|---:|---:|
| First and last two symbols fixed | 8 | 5 |
| Shared beginnings also fixed | 4 | 5 |

With shared beginnings fixed, the numbers of possible sequences per message are 1, 1, 1, 2, 2, 1, 1, 1, and 1. In particular, the first three messages, which contain the measured five-string pattern, cannot change at all.

This null is nearly frozen. Its failure to remove the pattern is not evidence for a second-order cipher. The limited corpus cannot support this particular stronger conditional comparison.

Files: `context2_pattern_audit.py`, `context2_pattern_audit.json`, `verify_context2_enumeration.py`, and `checked_context2_enumeration.json`.

## Mechanism searches that did not resolve the cipher

### Return paths without an initial key

`return_path_bv.py` encodes necessary card-return constraints for the rotating three-cycle model using bit vectors. Once a card has been output, its next appearance constrains its intervening movement without requiring its initial position. The model includes the explicitly listed shared-plaintext assumptions but no alphabet-size restriction and no common-initial-key constraints.

Fifteen generated examples with their actual plaintext fixed passed. On the real corpus, full return-path tests for rotations 0, 1, 9, 17, 41, and 81 all timed out. The configured solver timeout was five seconds per check, but preprocessing and solver overhead made the actual total run about 113 seconds. These results exclude nothing. A future satisfying result from this encoding would still be only a relaxation, not a recovered key.

Evidence: `return_bv_all_10000.json`.

### Bidirectional propagation through shared passages

`shared_plaintext_search.py` extends the exact lazy-key search: a known key assignment determines a selection in one passage, and an assumed equal selection in another passage can then force a new key assignment. All key assignments remain one-to-one, and any completed result must reproduce the full ciphertext and the assumed plaintext equalities.

Forty-eight small examples agreed with exhaustive enumeration of all keys. They included altered ciphertext, arbitrary first symbols, and partial initial-key constraints.

The real-data run tested rotation 9, all 82 bottom selections, the listed repeated-passage and shared-prefix assumptions, and an additional hypothesis that the first symbols select positions 1 through 9 in the interleaved East 1, West 1, East 2, ... corpus order. That numbering and order are assumptions, not recovered information. It reached 579,746 nodes before its 30-second limit and remained inconclusive.

Two generated controls using the same equality layout also remained inconclusive: the 82-selection version reached a 100,000-node limit, and the 27-selection version reached a 30-second limit. Search progress through a partial branch does not mean those plaintext positions are correct.

Evidence: `shared_key_eyes_9_82_numbered_prefixes.json`, `shared_key_control_9_82_numbered_prefixes.json`, and `shared_key_control_9_27_numbered_prefixes.json`.

## Reproduction

Use the bundled `ciphertext.json` and dependencies in `requirements.txt`. No project build is required.

```powershell
python transition_pattern_audit.py --trials 2000
python context2_pattern_audit.py
python verify_context2_enumeration.py
python return_path_bv.py --rotations 0 1 9 17 41 81 --seconds 5
python shared_plaintext_search.py --numbered-headers --prefixes --nodes 1000000 --seconds 30
```

The broad working hypothesis remains an evolving symbol arrangement. This round provides stronger evidence for investigating the recurrence structure, while leaving the mechanism and the repeated-plaintext interpretation unproved. Novelty relative to other community work has not been established.
