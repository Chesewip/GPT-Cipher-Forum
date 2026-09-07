# Review of the proposed E3/E4 Hermetic plaintexts

**Assessment: the ciphertext observations largely reproduce, but the report does not verify either plaintext. E3 has an unreported source-text alteration and an exact contradiction within the fixed-per-letter positional permutation family. E4 remains an unverified crib.**

Reviewed document: `Noita_Eye_Messages_E3_E4_Step_by_Step (1).pdf`, eight pages, supplied by the user. The PDF explicitly says it is not a complete solution; this review respects that distinction. Its stronger claim that the proposed passages are unusually strong candidates still requires scrutiny.

## What reproduces

- Both complete ciphertext arrays in Appendix A match the existing corpus exactly: 136 E3 body symbols and 118 E4 body symbols.
- The nine total lengths, first symbols and body lengths match.
- All 36 distinct pairwise body-prefix lengths in the table match, including the 2/5/9/20/24 hierarchy.
- The candidate strings printed in the PDF normalize to exactly 136 and 118 characters under its stated case/space/dash rule. They share the first nine characters, `THEREISNO`.
- The claimed 28-symbol pattern exists in E3/E4/W4/E5 at the stated positions when those positions are interpreted as **zero-based raw indices including the first symbol**. The reported branching at lengths 29 and 31 also matches.
- The three repeated-pair index distances in that pattern really are 4, 13 and 4.
- Under the proposed E3 alignment, plaintext E corresponds to 16 different ciphertext labels.
- With ASCII character values modulo 83, the first four derived keystream values repeated as a period-four key give 132 errors. Optimizing the four key values instead gives 124 errors, still not a fit. No exact periodic affine fit exists for periods 1 through 32 under this encoding. Rejection of these simple models does not authenticate the candidate.

Three unrestricted base-five digits span 0-124. The observed 0-82 range is an additional property of the chosen eye reading, not a consequence of base five by itself. The PDF does not provide original eye images or a complete row-reading implementation, so this review crosschecks the supplied integer transcription rather than independently extracting glyphs from the game.

## E3 is not the unaltered Mead quotation

The report's opening is:

`There is no difference with one another;`

The cited Mead text instead opens the relevant sentence:

`With Him, therefore, is there no difference with one another;`

See [Mead, Corpus Hermeticum XVIII, section 14](https://sacred-texts.com/gno/th2/th235.htm), printed page 296. The report omits the introductory wording and changes the order of *is there* to *there is*. Those operations are not capitalization, space removal or dash normalization.

Using that source sentence followed by the same subsequent sentences through the report's selected endpoint produces **154 normalized characters**, not 136. Omitting the introductory wording gives a 136-character excerpt beginning `ISTHERENO`, so length alone does not select the report's `THEREISNO` wording. An independently documented alternate transcription could change this source comparison, but it is not identified in the PDF.

The E4 wording does appear in [the cited Hermetic transcription, chapter VI](https://sacred-texts.com/chr/herm/hermes6.htm). Its selected excerpt ends at a genuine semicolon within a continuing sentence. Selecting that endpoint is a choice that needs to be counted when assessing how surprising the length match is.

The six-row source-length table does not supply all six exact excerpts or a complete search log. It therefore cannot establish that the candidate was uniquely selected by a fixed, reproducible corpus-search procedure. The claim that normalization was chosen before fitting is a statement about the other agent's workflow, not something this PDF independently demonstrates.

## A four-observation contradiction for E3

This test is independent of the quotation-source issue and does not require a recovered key.

Assume each plaintext character applies one fixed permutation of deck positions, and ciphertext is read from one fixed output position after each update. The initial deck can be arbitrary and the per-character permutations can be arbitrary. This includes the fixed-update positional deck/GAK family under discussion; it does not include every cipher that might be called stateful or deck-based.

For a particular plaintext word, its composite position permutation is fixed. If that word leaves the output card unchanged in one occurrence, its permutation fixes the output position. It must therefore leave the output card unchanged in every occurrence, regardless of the starting deck.

The proposed E3 plaintext violates this with the two-letter word `NO`:

| Occurrence of NO | Body positions of N and O, one-based | Ciphertext immediately before N | Ciphertext after O |
| --- | --- | ---: | ---: |
| Opening `...ISNO...` | 8-9 | 60 | 40 |
| Later `...ANOTHER...` | 28-29 | 13 | 13 |

One occurrence changes the output card, while the other preserves it. In equations, a fixed composite U for NO and an initial deck permutation D would require both `U(0) != 0` and `U(0) = 0`. Changing D cannot resolve the contradiction because D is injective.

This uses only four ciphertext observations and the proposed plaintext between them. It is unaffected by arbitrary relabeling of the ciphertext alphabet. It occurs within the first 29 body symbols, so it does not depend on the rest of the quotation, its endpoint or the full message length.

The existing permutation-action graph checker independently reports the same exclusion. A separate verifier checks the elementary NO argument without graph folding or SMT. It also verifies the return invariant on 14,040 exhaustive small-deck/two-update cases and 100 generated 83-card streams.

**Scope:** the exact E3 candidate is impossible within this stationary fixed-output permutation family. A cipher with time-dependent updates, a variable output rule, or other state-dependent behavior may escape the test. The Noita cipher family remains unknown, so this is not a universal disproof of every imaginable encryption of that text.

E4 has no contradiction in these tests. That means only that this necessary test does not reject it. The surviving graph is not a recovered 83-card key or a verified decoder.

## Why the other observations do not verify the quotations

The prefix depths are genuine, but they are lengths, not decoded letters. Many phrases can have nested prefixes of those lengths. Choosing `TH`, `THERE`, `THEREISNO` and a 20-character continuation after inspecting the hierarchy does not establish that these letters were encrypted. The report provides no calibrated search-space count or held-out prediction to support the phrase “unusually strong.”

The 28-symbol block is also genuine, but its existence is independent of which quotation is proposed. Substitution maps constructed by pairing the same aligned isomorphic windows necessarily compose consistently on those observed labels; that composition check adds no independent evidence for Mead's wording.

The two proposed plaintexts do not even contain identical text at their aligned block positions. This is not by itself a universal contradiction: ciphertext isomorphism need not imply identical plaintext in every stateful model. It does show that the block has not been explained by a straightforward shared-passage interpretation of these quotations.

Failure of substitution, short-period additive and affine models establishes only that the candidate does not fit those models. An incorrect proposed plaintext will commonly fail them too. It is not positive evidence that a more elaborate cipher must make the candidate correct.

## Files and reproduction

- `mead_candidate_audit.py` and `mead_candidate_audit.json`: counts, prefix matrix, block pattern, periodic tests, source comparison and permutation-action check.
- `verify_mead_return_certificate.py` and `checked_mead_return_certificate.json`: the independent four-observation NO contradiction and generated controls.

Run directly, without a project build:

```powershell
python mead_candidate_audit.py
python verify_mead_return_certificate.py
```

The current audit JSON also records the supplied PDF hash and exact Appendix A crosschecks performed during the review. The input PDF was not edited. The most useful next evidence for E4 would be a precisely specified cipher and a successful independently checked encryption or a held-out prediction, not additional length coincidences.
