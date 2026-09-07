# Noita eye cipher: further exploration

**Still unsolved. No verified plaintext or key.** This round kept the documented base-5 triangular trigrams, audited the repeated-plaintext assumptions, and investigated deck updates with more than one moving position.

## What changed

The strongest new result is a conditional exclusion of a broader family: swapping a selected card to the top, making additional rearrangements inside fixed groups of bottom positions, and applying a common shuffle that permutes those groups. It fails for both possible nontrivial equal-sized partitions of 82 positions: two groups of 41, or 41 groups of two.

This allows an arbitrary initial deck, an arbitrary permutation of the groups, and arbitrary rearrangements within each group. It uses the presumed equal internal plaintext transitions in the documented passages of length **14 or more**. It does not need the shorter 10–12-symbol associations. Dropping to only the three longest passages leaves cases unresolved, so the assumption boundary is explicit.

For the previously implemented rotating three-cycle model, the result removes every neighbor offset that does not traverse the whole 82-position ring. The remaining offsets are equivalent after renumbering positions: one representative neighbor step, together with 82 possible common rotations, covers them. If the selection alphabet has at most 40 symbols, the zero-rotation case is separately excluded by reachability, leaving **81 representative parameter choices with arbitrary starting decks**. These are search targets, not candidate decryptions.

## How the exclusion works

The model performs a top/selected-position swap, a permutation within each group, and then a common shuffle Q which fixes the top and permutes the groups. If the exact position inside a group is temporarily ignored, the extra within-group rearrangements disappear from the calculation. The remaining group-level behavior is a top swap followed by a fixed permutation of the groups.

Undoing the ciphertext-driven swaps gives reduced labels b at each time. Equal plaintext selections at times s and t require their group assignments to differ by s−t applications of the group permutation. A connected set of these equations gives integer offsets and loop constraints on a possible permutation cycle.

In the certificates here, the large contradictory component has cycle-length gcd 1. Its labels must therefore all occupy the same group. That exceeds the allowed group capacity for every possible initial top label. For example, with initial top label 0, the longer-passage equations force **72 distinct initial labels into one group**, whose permitted capacity would be 41 or two.

The finite verifier recomputes the equations and checks every possible group-cycle length directly, independently of the integer-offset/gcd discovery calculation. It passed **7,138 modular checks**. Twenty additional controls used known repeated plaintext, random initial decks, arbitrary group permutations, and arbitrary letter-dependent rearrangements within the groups; all were accepted. The group-projection formula also passed 5,400 generated checks, and the earlier cyclic-phase special case passed 12,000.

Evidence: `block_system_exclusion.json`, `checked_block_system_exclusion.json`, and `quotient_phase_audit.json`. Code: `block_system_exclusion.py`, `verify_block_system.py`, and `quotient_phase_audit.py`.

This is not an exclusion of all deck ciphers. Updates that move cards across these groups, whole-deck shuffles that move the top, different initial states per message, or failures of the assumed plaintext equalities remain outside the conclusion.

## Auditing the repeated patterns

I separated evidence of nonrandom structure from the stronger claim of identical plaintext.

The global comparison statistic was the greatest number of **distinct literal nine-symbol strings** sharing any equality pattern with at least three repeated-symbol constraints. The eyes score five. Counting distinct strings avoids treating identical copied ciphertext as independent evidence.

I generated 2,000 random comparison corpora with the same message lengths, distinct first symbols, the prescribed shared-prefix relationships, and no adjacent repeated symbols. None reached five; the largest score was three. This supports nonrandom structure against that specific null model. It does not assign an overall probability to the cipher hypothesis, prove repeated plaintext, or establish every individual match. The simulation has finite resolution and does not model every plausible alternative mechanism.

The sensitivity audit found:

| Plaintext associations retained | Earlier one-swap test |
|---|---|
| Three longest passages only | Several top-cycle cases remain unresolved |
| All passages of length at least 14 | Top-cycle length 7 remains unresolved |
| All associations except the two three-message length-12 links | Conditional exclusion still holds |

The new grouped-position exclusion above succeeds with the length-at-least-14 set because it imposes a different structural restriction. There is no contradiction between those results.

Evidence: `pattern_assumption_audit.json`. Its fixed-pattern probabilities are descriptive probabilities for a predetermined pattern, not discovery-adjusted significance claims. The randomized global statistic searches all eligible length-nine patterns in each generated corpus.

## Two additional finite searches

**Starting orders suggested by the eye symbols.** I constructed 160 distinct initial decks from all five-direction renumberings in the canonical digit order, plus all digit orders under rotations and reflections of the four compass directions. These are initial-key hypotheses; the original eye grouping stays unchanged. Across every neighbor offset and common bottom rotation, the **1,062,720 recorded configurations require at least 80 selections**. The scan used forward messages with the first symbol included. It does not exclude other starting decks.

A planted control using one of these nonstandard initial orders recovered its 27-symbol alphabet at the known parameters. Results: `trigram_key_scan_results.json` and `trigram_key_control.json`.

**Rotating all 83 cards.** I also tested a three-cycle followed by a rotation of the entire deck, with its swap anchor chosen so the selected card becomes the output. Every nonzero neighbor offset and every whole-deck rotation was tested under ascending/descending initial decks, forward/backward reading, and inclusion/omission of the first symbol. All **53,784 configurations require at least 81 selections**. Arbitrary keys remain unexcluded.

The full planted control recovered the 27-symbol alphabet and the planted parameters. Sixty generated checks compared the efficient rotating-frame calculation with direct physical-deck encryption. Results: `full_rotation_three_cycle_scan.json` and `full_rotation_three_cycle_control.json`.

## Constraint-search results that remain inconclusive

For the rotating three-cycle model, a card's path between two occurrences can be expressed without its initial position. It follows the common rotation except when it is the selected card's neighbor; that event moves it backward by the neighbor offset. I encoded these paths as necessary constraints and checked ten generated examples with their actual plaintext pinned.

Using only returns at distance eight or less, the relaxed solver found a fit at neighbor offset 2 and shuffle offset 26. This was **not a key or plaintext recovery**: the relaxation omitted the common starting-deck constraints. The independent group-level proof now excludes that parameter class under the same repeated-plaintext assumptions, demonstrating why a relaxed fit cannot be authenticated as a solution.

Longer-return searches, and short-return searches restricted to the surviving whole-ring neighbor step, timed out. They supply no exclusions. Their exact statuses are retained in `clocked_return_*.json`; the encoding and controls are in `clocked_return_constraints.py` and `clocked_return_controls.json`.

The most concrete unresolved direction from this round is the whole-ring neighbor update with an unknown starting deck. Another is a whole-deck rotation combined with two variable-position moves. Replacing the repeated-plaintext interpretation with a weaker one also remains a distinct avenue.

## Source context and reproduction

The [original progress document](https://docs.google.com/document/d/1XMNXktCoSabnFWZf9rJFoaKMzsA1bbv7x1Xh9tXkKYk/edit), [isomorph discussion](https://github.com/Lymm37/eye-messages/wiki/Isomorphs-%28Gap-Patterns%29), and [perfect-isomorphism discussion](https://github.com/Lymm37/eye-messages/wiki/Perfect-Isomorphism) distinguish observed matching patterns from hypotheses about their causes. I have not established whether these new calculations are novel to the community.

Run the scripts beside `ciphertext.json` with the dependencies in `requirements.txt`. There is no build step. The ZIP includes scripts, certificates, controls, unsuccessful searches, and the earlier reports. `manifest.json` records file hashes.
