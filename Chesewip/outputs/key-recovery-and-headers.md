# Key recovery controls and the first-symbol loophole

**The Noita eye cipher remains unsolved. No actual plaintext or key was recovered.** This round developed a working crib-assisted attack on generated messages and independently checked several exclusions that allow a special first symbol.

## Successful recovery on generated data

The tested cipher has 83 deck positions. Position 0 is the output; positions 1–82 form a ring. Selecting position p moves its card to the output, moves the next ring card to p, moves the previous output card to that neighbor, and then rotates the bottom ring by a fixed offset b. All messages start with the same unknown deck.

Encrypting a proposed plaintext prefix with an identity deck reveals which initial positions must contain the observed ciphertext labels. Conflicting assignments reject the crib exactly. Otherwise it fixes part of the key. This consistency criterion is necessary and sufficient for the specified cribs, within the specified cipher and character mapping; consistency does not establish that a phrase is correct.

On a generated control with a random 83-card key and b = 9:

| Correct plaintext supplied | Initial key positions fixed | Final recovery |
|---|---:|---:|
| First 20 characters of three messages | 42 of 83 | All 1,080 characters |
| First 40 characters of one message | 31 of 83 | All 1,080 characters |

These are two setups on the same corpus and key, not a broad success-rate estimate. A four-character English score and swaps among unfixed key positions recovered the remaining text. Forty exhaustive small-deck checks verified the crib consistency criterion against every key.

The score was trained on [Pride and Prejudice](https://www.gutenberg.org/ebooks/1342); the control plaintext came from separate passages in [The Adventures of Sherlock Holmes](https://www.gutenberg.org/ebooks/1661). The control mapping is space = 1 and a–z = 2–27. English, this ordering, and any proposed Noita crib remain hypotheses.

Files: `crib_key_search.py`, `crib_control_3_20.json`, `crib_control_1_40.json`, and `english_clocked_search.py`.

## Blind recovery is still unreliable

The language search recovered the full control from five key swaps away from the true key. From random keys, the recorded two-restart search recovered only 287 of 1,080 positions. A separate alphabet-based control search nearly fit its target alphabet while recovering only 64 of 1,080 positions.

Low alphabet size, readable fragments, and exact ciphertext replay do not authenticate a candidate. The alphabet objective also rewards frequency concentration, so it can trade a larger number of out-of-alphabet positions for that reward.

Evidence is retained in `english_clocked_control_9*.json` and `clocked_key_control_*.json`. Candidate text in these control files is a search artifact from generated data.

## Exclusions with unrestricted first symbols

The first symbol might encode a message number outside the ordinary alphabet. This test allows any of the 83 first selections independently for each message, followed by a specified contiguous interval of text selections on the bottom ring. The common starting deck is arbitrary. No repeated-plaintext interpretation is used.

Each ciphertext label must occupy one initial position, different from every other label's position. Reachability can force more labels into a set of positions than that set can hold. This is a finite Hall matching contradiction.

| Allowed text positions | Rotation b | Contradiction |
|---|---:|---:|
| 27 consecutive positions | 0 | 83 labels into 30 positions |
| 27 consecutive positions | 1 | 76 into 61 |
| 27 consecutive positions | 41 | 83 into 59 |
| 27 consecutive positions | 81 | 77 into 61 |
| 41 consecutive positions | 1 | 76 into 75 |
| 42 consecutive positions | 81 | 77 into 76 |

For example, rotation 1 requires at least 42 consecutive text positions even with unrestricted first symbols. Rotation 81 requires at least 43. Meeting these lower bounds does not establish that a key exists.

All 82 rotations were checked with 27 text positions. Four were excluded; the other 78 survive this relaxation. A surviving position assignment need not be realizable by a plaintext sequence.

**Scope:** a contiguous selection alphabet in this particular three-cycle model. Arbitrary sets of 27 positions and other cipher mechanisms are not excluded. A common cyclic shift of the contiguous interval is covered by relabeling the arbitrary starting deck.

The discovery code passed 60 generated examples with unrestricted headers. An independent checker used physical forward position transitions and sets, rather than inverse bit masks, to recompute all six exclusions and check their Hall inequalities.

Files: `header_reachability.py`, `header_reachability_27.json`, `header_alphabet_bounds.json`, `verify_header_reachability.py`, and `checked_header_reachability.json`.

An earlier test required the first symbol to belong to the text alphabet. Across 3,280 rotation/unit-stride combinations with 27 text positions, it excluded 98. All 98 witnesses were rechecked, alongside 48 exhaustive short-word checks. Those results retain their stricter first-symbol assumption. See `alphabet_reachability_27_all_strides.json` and `checked_alphabet_reachability.json`.

## Exact key search remains inconclusive

`lazy_key_search.py` assigns initial card positions as needed, propagates determined outputs across messages, and checks future reachability and the key's one-to-one constraint before branching. Forty small-deck examples, including altered ciphertext and arbitrary headers, agreed with exhaustive key enumeration.

The 83-card blind control reached 100,000 nodes without recovery. The Noita run, using rotation 9 and unrestricted first symbols, reached its 30-second limit after 67,226 nodes. Both searches are inconclusive, not exclusions. A completed model fit would still require independent validation as a decryption.

Files: `lazy_key_control_9.json` and `lazy_key_eyes_9_headers.json`.

## Reproduction and source scope

Run Python scripts directly; no project build is used. Dependencies are in `requirements.txt`. Cipher-only checks use the bundled `ciphertext.json`.

For English controls, place the Gutenberg plain-text downloads for books 1342 and 1661 in `../work/pg1342.txt` and `../work/pg1661.txt`, relative to these scripts. Source hashes are in `english_clocked_control_9.json`; books are not bundled.

```powershell
python crib_key_search.py --messages 3 --length 20 --steps 80
python crib_key_search.py --messages 1 --length 40 --steps 100
python verify_alphabet_reachability.py
python verify_header_reachability.py
python lazy_key_search.py --control --seconds 35 --nodes 100000
```

The corpus uses the published alternating-triangle/base-5 trigram transcription, labels 0–82. This round did not re-extract eyes from the game. Earlier provenance and assumption audits remain in the preceding reports. Novelty relative to other community work has not been established.
