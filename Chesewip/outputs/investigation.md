# Noita eye cipher: first investigation

**Not solved. No plaintext or key recovered.** This investigation verifies the published corpus, audits assumptions, and tests two restricted encoding families. It does not identify the actual cipher or claim these experiments are new to the community.

## Data and assumptions

The numerical transcription in [ngraham20's repository](https://github.com/ngraham20/NoitaCryptographyResearch/blob/master/eye/reference/noita_eye_data_trigrams.csv) agrees symbol-for-symbol with [Lymm's ASCII representation](https://github.com/Lymm37/eye-messages/wiki/Data). There are 1,036 symbols in nine messages, with lengths 99, 103, 118, 102, 137, 124, 119, 120, and 114. All 83 integers from 0 through 82 appear. There are no adjacent equal symbols. The pooled coincidence index, normalized to an 83-symbol uniform alphabet, is 1.0660436834.

This verifies agreement between published representations, not an independent extraction from Noita's executable.

Three assumptions deserve care:

- **Spaces have not been shown to be absent.** The [original gap-pattern document](https://docs.google.com/document/d/12sCi3OrTuy4PPcu3zUykue7suHvAPyK-uFKcm8Rp4Go/edit) explicitly retracts the assumption used to infer triple plaintext letters. That argument remains in the supplied progress summary and should not be used as a constraint.
- **A deck cipher is a conditional hypothesis.** [Lymm's explanation](https://github.com/Lymm37/eye-messages/wiki/Explanation-of-Progress) distinguishes a mechanism that fits observations from a proven identification. Matching ciphertext equality patterns are evidence for repeated plaintext, not proof.
- **Prime message lengths do not eliminate every block construction.** They exclude a fixed full-block model without padding removal or partial final blocks. Allowing a shorter final block removes that particular contradiction, without making the model likely.

## Ordinary move-to-front requires at least 59 input symbols

The precise tested model is: a plaintext symbol selects a fixed rank in a deck; output that card's label; move it to the front; preserve the other cards' order. No additional shuffle is applied.

If a card last appeared at position r and reappears at t, its rank before selection at t equals the number of distinct labels between r and t. This is independent of the initial deck order. Already-repeated labels therefore reveal part of the plaintext rank stream without the key.

The corpus has 474 such observations, requiring **59 distinct ranks**. This model cannot explain the data with a fixed plaintext alphabet of 58 or fewer symbols. It excludes ordinary letter-only implementations under the stated one-symbol/one-rank rule.

It does not exclude a larger alphabet, multiple ranks per plaintext letter, or additional state updates. The complete rank set is in `results.json`.

## 26,240 simple deck configurations require at least 81 input symbols

The tested operation is:

1. Select a bottom position using a fixed plaintext-to-position mapping.
2. Swap that card with the top card and output the new top label.
3. Permute the other 82 positions, leaving the top fixed.

Numbering bottom positions 0 through 81, the fixed permutation is:

    P(x) = (a*x + b) mod 82, with gcd(a,82) = 1.

There are 40 valid multipliers and 82 offsets: 3,280 permutations. All were tested under eight configurations: forward/backward reading, inclusion/exclusion of the original first symbol, and ascending/descending initial deck order. Exclusion occurs before reversal.

| Configuration | Minimum selection alphabet | Best normalized coincidence index |
|---|---:|---:|
| Forward, first included, ascending | 81 | 1.123862 |
| Forward, first included, descending | 81 | 1.118203 |
| Forward, first excluded, ascending | 81 | 1.113305 |
| Forward, first excluded, descending | 81 | 1.115329 |
| Reverse, first included, ascending | 81 | 1.049376 |
| Reverse, first included, descending | 81 | 1.055035 |
| Reverse, first excluded, ascending | 81 | 1.050893 |
| Reverse, first excluded, descending | 81 | 1.054006 |

Every configuration requires at least **81 different selections**. None supports a fixed plaintext alphabet of 80 or fewer symbols under these initialization and operation rules. Scores use 82 possible bottom selections. The maximum score is a search maximum, not calibrated statistical significance or evidence of language. The configuration count does not imply all tested ciphers are inequivalent.

**Positive control:** given nine synthetic messages encrypted using 27 selections and a planted shuffle a=17, b=9, the same exhaustive search recovered the 27-symbol minimum and the planted parameters. This checks the implementation against a known answer.

**Limits:** the initial deck may be keyed, the bottom permutation may be non-affine, a common shuffle may move the top card, or each plaintext character may perform a more complicated operation. Those possibilities remain open.

## A boundary mistake that verification caught

A separate necessary-condition graph tests the same swap/top-fixed-shuffle family with an arbitrary bottom permutation P and arbitrary initial deck order. Let p_t be the selected bottom position. If a ciphertext card last occurred at r and next occurs at t, then:

    p_t = P^(t-r-1)(p_(r+1)).

The card is displaced from the top at r+1, then follows P until its next output. Combine those equations with hypothesized repeated plaintext, while requiring distinct cards to occupy distinct positions.

Initially, I equated plaintext at every position of matching ciphertext runs. This produced a contradiction. Checking it exposed an overly strong boundary assumption: n ciphertext outputs contain n-1 internal transitions. The first output can serve as the starting visible state; the plaintext producing that first output need not be shared.

A direct witness, using **zero-based positions**:

- East 4 at positions 68 through 100 and West 4 at 71 through 103 have the same ciphertext equality pattern.
- Immediately before those runs, both output card 26: East 4 at 67, West 4 at 70.
- At relative position 22, East 4 outputs 26 at 90, whereas West 4 outputs 21 at 93.

If plaintext operations from the very start of those runs were identical, any fixed-per-letter deck cipher would move that preceding top card along the same positional path. It would reappear at the same relative time. It does not. Thus whole-run plaintext equality is incompatible with that model. This does **not** invalidate a common transition sequence beginning one step later.

After shifting the ten tested equality hypotheses to internal transitions, the graph has 1,036 nodes, 631 edges, and 451 components, with **no detected contradiction**. This is inconclusive: necessary constraints are not a reconstructed key. Twenty synthetic repeated-phrase examples using random bottom permutations and random initial decks passed the graph check.

This is an implementation lesson from this investigation, not a claim that the community overlooked the distinction. Both versions are retained in `results.json` to make the abandoned inference auditable. **Do not cite the uncorrected contradiction as an exclusion of the cipher family.**

## Remaining work

The live version of this simple deck hypothesis has a keyed initial order and a potentially non-affine common shuffle. A next experiment would combine recurrence equations, correctly aligned repeated-transition hypotheses, distinct-card constraints, and a bound on plaintext alphabet size in a constraint solver. It should first recover planted examples with unknown initial decks and unknown shuffles.

Failure of that restricted attack would still leave other deck operations and imperfectly isomorphic mechanisms open. Nothing here establishes English versus Finnish, absence of spaces, or the first output being a numerical index.

A solve needs a fully specified decoder, a common key/initialization rule explaining all nine messages, coherent plaintext, and exact re-encryption. This investigation has not reached that standard.

## Reproduction

Keep these files together. Python 3.10 or later runs the graph/rank analysis. The scan also requires NumPy; version 1.24.3 was used.

    python analyze.py
    python deck_scan.py
    python verify_scan.py

The scripts resolve input/output paths relative to their own location. They regenerate `results.json`, `deck_scan_results.json`, and `scan_control.json`, respectively. `ciphertext.json` contains the verified corpus. Source revisions and its hash are in `provenance.json`.

All delivered text files use Windows CRLF. No project build was performed.
