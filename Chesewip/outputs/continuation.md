# Noita eye cipher: continuation and reproducible exclusions

The next round is recorded in `further-exploration.md`, including an assumption audit and a broader conditional exclusion of grouped-position updates.

**The cipher remains unsolved. No plaintext or real key has been recovered.** This continuation replaces several searches over guessed keys with exact necessary conditions. The strongest results concern a precisely defined deck-cipher family; they do not exclude deck ciphers in general. I have not established whether these results are new to the community.

## Starting point: the groups of three eyes

These experiments use the documented triangular-trigram reading throughout. Five eye directions are assigned the digits 0–4. Alternating upward and downward triangles supply three base-5 digits per symbol, producing values 0–82. For example, 312 in base 5 equals 82 in decimal. The five directions, grouping, and reading convention are described in [Trigrams](https://github.com/Lymm37/eye-messages/wiki/Trigrams) and [Reading Orders](https://github.com/Lymm37/eye-messages/wiki/Reading-Orders).

The “83 cards” below are mathematical labels for those 83 whole-trigram values. Converting the eyes into numbers is the input representation; finding the plaintext is the unresolved next stage. The exact arbitrary-key results allow any common bijective renumbering of the 83 symbols. Changing the grouping of the individual eyes, or applying different renumberings at different positions, is outside those tests. None of the exclusions below disproves the base-5 trigram representation itself.

## The tested family

There are 83 distinct cards and a common, arbitrary initial deck for the nine messages. Position 0 is the top. A plaintext symbol selects a fixed position p. Choose a fixed positional permutation Q and let a = Q⁻¹(0). Each step:

1. Swaps the cards at a and p.
2. Applies Q to all positions.
3. Outputs the top card.

This includes many arrangements described as a swap plus a fixed shuffle. Moving the fixed shuffle before the swap can be absorbed into a change of coordinates. Additional fixed permutations can also be absorbed into Q. It does **not** include general letter-dependent permutations or two independently varying swaps.

An alphabet bound here counts distinct selected positions. It is not necessarily the number of letters in the underlying language: homophones, multi-symbol encodings, punctuation, or extra state can invalidate that identification.

## Results that do not assume repeated plaintext

| Common shuffle structure | Necessary selection alphabet | Evidence |
|---|---:|---|
| Ordinary move-to-front, a different model | At least 59 | Exact recurrence-rank calculation in the first report |
| Q fixes the top and cycles all 82 other positions | At least 45 | Exhaustive circular-support constraints, all 83 possible initial top labels |
| Q has two cycles of lengths L and 83−L, with top in the first, for L=2,…,8 | At least 41 | Support constraints and independently checked finite hitting-set certificates |
| Q fixes the top and has two other cycles of length 41 | At least 41 | Support constraints; independent finite coloring checker covers every alphabet allocation |
| Q is a full 83-position cycle | At least 79 | Distinct short return distances force distinct selections |
| Q(x)=a·x+b mod 83, a≠0, arbitrary initial deck | At least 41 | Complete classification of all 6,806 affine shuffles, combining the preceding certificates and cycle reachability |

The affine result concerns the **common shuffle inside the swap-and-shuffle construction**. It is not a claim about all affine ciphers, or a restatement that all group-autokey ciphers have been excluded.

The earlier affine scans assumed sorted or reversed initial decks. The new result removes that initialization restriction. The 82-cycle bound was also rechecked allowing an identity selection for the first output; no candidate initial top was discarded merely because it matched a message's first symbol.

Evidence files: `checked_cycle_subset_10_44.json`, `checked_synchronized_bound_2_40.json` through `checked_synchronized_bound_8_40.json`, `checked_multicycle_bound_1_41_41_40.json`, and `affine_family_certificate.json`.

## A stronger result, conditional on the repeated-plaintext interpretation

Assume that the published isomorphic ciphertext passages correspond to equal internal plaintext transitions at the specified offsets. Under those equalities, **every fixed permutation Q in the one-swap family is excluded**, with arbitrary initial deck and without a small-alphabet assumption.

This remains true after omitting the first two internal comparisons from every passage: only relative plaintext positions 3 onward are required, where the ciphertext run starts at relative position 0. Thus the contradiction does not use an equality at the start of a run. The exact runs are recorded in `progressive_reduction.py`; the trimmed certificates are in `trimmed_isomorph_3.json` and their verification in `checked_trimmed_isomorph_3.json`.

The proof separates possible lengths L of Q's cycle through the top:

- For L=1,…,7, synchronized ciphertext yields partial permutation constraints. Allowing every possible set of initial top-orbit cards still leaves contradictions. The required deletions exceed L, as checked by an independent finite hitting-set search.
- For L=8, corresponding positions in West 1 require different membership in the top cycle, contradicting equal plaintext selections.
- For L≥9, West 1 positions 38 and 68 (zero based) have return distances 8 and 9. Equal plaintext would require Q⁷(0)=Q⁸(0), impossible on a cycle of length at least 9.

Both the original and trimmed forms passed 80 generated controls each. These controls used random initial decks, arbitrary permutations outside the top cycle, and plaintext with exactly the tested repeated sections imposed. The reduced graph accepted them; directly inferred selections agreed with the planted plaintext.

`conditional_arithmetic_certificates.json` exposes the small arithmetic contradictions directly. For L=1,2,3,5,6,7, respectively, the certificate contains 2,3,4,6,7,8 pairwise-disjoint contradictory label sets. Each would need an exceptional initial top-orbit label, but only L exist. The L=4 certificate uses a five-node finite hitting-set search instead. These are inspectable counting arguments, not unexplained solver verdicts.

The interpretation matters: matching ciphertext equality patterns are not proof of matching plaintext. The conclusion is a choice between a more complicated update and a failure of those particular plaintext equalities, not a proof that the broader deck-cipher hypothesis is wrong.

## Why the exact bounds work

**Return distances.** After a card is output at the top, it follows Q until it is selected again or reaches the swap anchor. If its next occurrence is d steps later with d≤L, the next selected position must be Q^(d−1)(0). Distinct such distances force distinct selections. Also, because all 83 card labels occur somewhere in the corpus, every cycle outside the top cycle must be selected at least once: an initial card cannot leave that cycle without a selection there. These costs concern disjoint positions and can be added.

**Synchronization.** Following L consecutive distinct outputs, the entire cycle through the top is known: its cards are the latest L outputs in reverse age order around that cycle. Later top-cycle contents can be followed exactly from ciphertext. The supplied messages synchronize immediately for L≤8.

**Removing the swaps.** Let X₀ map initial card labels to positions. From the known output and anchor labels, undo the successive label transpositions to obtain a reduced label b at step t. Apart from labels in the discarded prefix and the unknown initial top orbit, the selected position satisfies

    p_t = Q^t(X₀(b_t)).

There are at most L unknown initial top-orbit labels. This is a necessary relation; it does not guess their identities or the initial key.

**Circular supports.** If b belongs to a residual cycle of length M, collect the times at which it occurs modulo M. Its selected positions are that set shifted by an unknown phase. Different initial labels in the same cycle require different phases. Exhaustively failing to fit a subset of these supports into A positions proves that the subset cannot share an A-position selection alphabet.

For a single residual cycle, each failing subset must contain an unknown initial top-orbit label. The certificate proves that more than L deletions would be required. For two residual cycles, the checker enumerates every allocation of the available alphabet and searches for a compatible assignment of labels to cycles, allowing those same deletions. It uses finite backtracking rather than the SMT solver that discovered the constraints.

**Repeated plaintext.** Equal selections at steps s and t give a relation R^(s−t)(b_s)=b_t for R=X₀⁻¹QX₀. In a connected component, integer offsets must fit a permutation cycle without putting two distinct labels at the same phase. The conditional certificates show that no choice of the potentially invalid labels repairs all components.

## Controls, failed searches, and remaining work

The circular-support search matched 800 small brute-force decisions and accepted ten planted 83-card examples. The synchronization formula matched 41,519 generated observations in the original two-cycle tests and 9,360 additional observations across fourteen partition controls. None of the full positive-control constraint runs produced a false exclusion; some were inconclusive within their limits.

A separate key-search method evaluates changes to the starting deck efficiently. It recovered complete planted plaintext equality patterns for several 83-card controls. One difficult control required annealing after simpler searches failed. Searches on the eyes did not recover a small alphabet. These negative heuristic results are **not** exclusion proofs. A search that scored both repeated-plaintext agreement and alphabet size failed its own planted control, so it supplies no evidence against the cipher.

Tests of other cycle partitions, including (2,40,41), (3,40,40), (4,39,40), (8,37,38), and (2,54,18,6,1,1,1), were inconclusive at the recorded limits. They remain open in the absence of the repeated-plaintext assumptions. Solver timeouts and iteration limits have been preserved as such in the result files.

Another implemented mechanism uses a three-cycle involving the top, the selected position p, and a second position f(p). Because two positions vary with the plaintext, it lies outside the one-swap family. Without an additional common shuffle, however, A input symbols touch at most 1+2A initial positions. All 83 labels appearing therefore requires A≥41, regardless of key or f. The heuristic searches for this unshuffled version failed their 27-symbol planted control; annealing reached 38 selections and block moves reached 34, without recovering the plaintext pattern. Those failures add no exclusion evidence. The simple reachability argument supplies the actual bound.

Adding a common rotation of the 82 bottom positions removes that reachability obstruction. For f(p)=p+d on the bottom ring and common shuffle Q(p)=p+b, I scanned all 81 nonzero neighbor offsets d and all 82 shuffle offsets b. Across ascending/descending starting decks, forward/backward readings, and inclusion/omission of the first symbol, the 53,136 configurations require at least 81 selections. This scan **does not exclude arbitrary initial keys**. Its full planted control recovered the 27-symbol alphabet at d=17,b=9, with all 83 ciphertext labels present; 60 generated comparisons also checked the rotating-frame calculation against direct physical-deck encryption. See `clocked_three_cycle_scan_results.json` and `clocked_three_cycle_control.json`.

The clocked, three-variable-position model with an arbitrary initial key remains a concrete unexcluded target. More general letter-dependent permutations and alternative interpretations of the repeated passages also remain open. Any `exact_replay` flag in a search result only checks decryption/encryption consistency. It is not evidence of an authentic solution.

## Sources and reproduction

The numerical corpus agrees between [ngraham20's transcription](https://github.com/ngraham20/NoitaCryptographyResearch/blob/master/eye/reference/noita_eye_data_trigrams.csv) and [Lymm's data](https://github.com/Lymm37/eye-messages/wiki/Data). This is agreement between published representations, not independent extraction from the game. See `provenance.json`.

Context: the [supplied progress document](https://docs.google.com/document/d/1XMNXktCoSabnFWZf9rJFoaKMzsA1bbv7x1Xh9tXkKYk/edit), [deck-cipher description](https://github.com/Lymm37/eye-messages/wiki/Deck-Cipher), and [explanation of progress](https://github.com/Lymm37/eye-messages/wiki/Explanation-of-Progress). The distinction between observations and assumptions in those sources remains essential.

Run the Python scripts beside `ciphertext.json`, with NumPy and z3-solver available. No project build is required. `README.md` lists the main verification commands. The bundle includes failed and inconclusive experiments to preserve the audit trail.
