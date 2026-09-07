# First-return constraints close the constant-pivot escape

**Unsolved. No authentic plaintext or historical key recovered.**

The simplest noninjective alternative to the preceding three-card model also has an exact obstruction. A rule that always uses the same third position needs **at least 35 distinct input selection values from ciphertext alone**. If either one of two explicitly stated plaintext equalities is accepted, the entire fixed-pivot family is excluded, with arbitrary keys and an arbitrary common fixed bottom shuffle.

The two statements have different assumptions. The 35-value lower bound uses no proposed plaintext or repeated-passage interpretation. The complete exclusion uses one such equality. Neither statement rules out all deck ciphers or every noninjective three-card rule.

## Exact model

Let position 0 be the output/top position, J a fixed non-top pivot, and Q a common fixed permutation of positions with Q(0)=0. Each input selects p outside {0,J} and performs:

```text
old selected card -> top
old top card      -> pivot J
old pivot card    -> selected position p
then apply Q
emit the top card
```

Q may be any bottom shuffle; it need not be a rotation. Initial decks may differ between messages and are otherwise arbitrary. Cards have distinct labels. The selection alphabet may be any subset of the permitted positions. A direct plaintext interpretation assigns one fixed selection value to each symbol.

A special operation for selecting J, changing pivots, duplicated card labels, a moving output, or message-specific shuffles falls outside this model. In particular, allowing a special pivot-selection operation would change the forbidden-return argument below.

## A first-return invariant

Let L be the length of J's cycle under Q. A first return of a label means its next occurrence in the same message, with no intervening occurrence of that label. The return gap g is the difference between those two output indices.

After a card is output at time r, the next update sends it to Q(J). Before it is selected again, it advances along J's Q-cycle unless it reaches J and is displaced as the pivot card. Thus:

```text
If 2 <= g <= L, the returning input selection is Q^(g-1)(J).
A first return at gap L+1 is impossible: the card is at J,
and J is not a permitted selection.
```

Gap 1 is also impossible because the top is not selectable. For g<=L, distinct gaps name distinct positions on the pivot cycle. The invariant does not apply the short-return formula after the card has passed through the pivot again.

This gives two cheap exact tests: an observed gap L+1 excludes L; and two assumed equal input selections with different short return gaps exclude any L large enough to cover both gaps.

## Ciphertext-only result

There are 474 first-return intervals in the indexed corpus. With 83 distinct cards, L ranges from 1 through 82. The observed gaps exclude every L except:

| Pivot-cycle length | Distinct short-return selections forced by the ciphertext |
| ---: | ---: |
| 36 | at least 35 |
| 68 | at least 66 |
| 73 | at least 70 |

These are necessary bounds, not demonstrations that any of the three cases can reproduce the full ciphertext.

The minimum of 35 also has a deck-size-independent proof. Every gap from 2 through 36 occurs. Those intervals exclude L=1 through 35. Every larger cycle assigns those same 35 gaps to distinct selection values. Adding unobserved, distinctly labeled cards therefore cannot reduce the lower bound.

Both keeping and omitting the initial marker of every message give the same candidate cycle lengths and alphabet bounds. This result does not depend on interpreting the first trigram as an encrypted character.

A direct 26-letter-plus-space implementation with one selection per symbol is therefore impossible in this family. A larger input alphabet or an additional encoding layer is a different case; the raw bound does not itself exclude those.

## One bridge equality excludes the remaining cases

All indices here are **zero-based raw ciphertext**, including the initial marker in the numbering.

| Position | Ciphertext label | Immediately previous occurrence | Return gap |
| --- | ---: | ---: | ---: |
| E4 raw 64 | 34 | E4 raw 29 | 35 |
| E5 raw 65 | 55 | E5 raw 40 | 25 |

The sole assumption is that the inputs at E4 raw 64 and E5 raw 65 are equal. This comparison lies inside the bridge used in the preceding report, away from its uncertain entry boundary. It does not require the late-phase plaintext assumption.

For every remaining 83-card cycle length, both gaps are short, so the two selections must be Q^34(J) and Q^24(J). Those are different positions on cycles of lengths 36, 68, and 73. They cannot be the same input selection. All three remaining cases are excluded.

This is conditional on that one equality. The observed isomorphism does not prove it is true plaintext.

## A separate, smaller certificate uses West 1

The same conclusion follows independently if the inputs at **West 1 raw 38 and raw 68** are equal. Their labels and last-occurrence gaps are:

| Position | Label | Previous occurrence | Gap |
| --- | ---: | ---: | ---: |
| W1 raw 38 | 21 | W1 raw 30 | 8 |
| W1 raw 68 | 64 | W1 raw 59 | 9 |

This is offset 4 in the previously documented W1 repeated context starting at raw 34 and 64. It survives leaving the first three inputs of that context unconstrained.

Only eight first-return intervals are needed for a compact proof:

- Observed gaps 2 through 9 exclude L=1 through 8.
- For every L>=9, gaps 8 and 9 force different selections, contradicting the single assumed input equality.

The JSON certificate stores those eight exact intervals. This argument has no upper bound on L and therefore excludes the specified fixed-pivot family for any finite distinctly labeled deck size, not only 83 cards. It still requires the common update rule and the one plaintext equality; adding that equality is not a ciphertext-only inference.

The bridge and W1 comparisons are separate sufficient assumptions. Neither proof needs both.

## What the other experiments did and did not establish

`pivot_relative_probe.py` found a local SAT witness for the three boundary transitions after relaxing the actual pivot contents and common shuffle. Thirty generated tests passed. That witness is consistent with the return obstruction: the relaxed test omitted the longer card histories. It was not accepted as a cipher key.

`pivot_physical_bridge.py` models actual local decks, a common pivot and a common arbitrary bottom shuffle. It passed fixed-mechanism controls at sizes 7, 19 and 83, and an unknown-mechanism control at size 7. The unknown size-19 control timed out, first at 20 seconds and then at 3 seconds in the instrumented repeat. The real bridge search was not run after that calibration failure. This is not negative evidence about the cipher. The first-return proof above does not rely on this solver.

An additional necessary permutation-action check used only the plaintext selection equalities forced by short gaps. It survived all 27 single-message cases across L=36,68,73 and three common-reset cases. The surviving folded graphs are much larger than 83 vertices, so they are not 83-card realizations. This check supplies no unconditional exclusion of the larger-alphabet cases.

## Verification and reproduction

The discovery analyzer generated 106 actual fixed-pivot ciphers spanning every pivot-cycle length at deck sizes 7, 19 and 83. Each used three 180-output messages, independent keys and a common shuffle. Every planted cycle survived. The short-return formula passed 18,916 checks. Identification of a cycle is not key recovery.

The independent verifier uses only the standard library and does not import the discovery analyzer. It checks all 164 records in the two 83-card exclusions, the compact eight-interval certificate, and the 35-interval alphabet certificate. It also exhausts every output-fixing shuffle, every pivot, and every permitted six-input word at sizes 3, 4 and 5: **71,140 streams**, containing **138,686 returns**. No counterexample was found, and the invariant has the direct argument given above.

```powershell
python fixed_pivot_return_audit.py
python verify_fixed_pivot_returns.py
```

The principal records are `fixed_pivot_return_audit.json` and `checked_fixed_pivot_returns.json`. The two solver probes and their saved outcomes are retained separately. No project build was run; authored files use CRLF.

## Implication for the search

The earlier [phase-switch obstruction](phase-switch-findings.md) covered injective third-position rules. This continuation covers the constant rule under separately stated conditions. It does not bridge the gap between those classes: nonconstant rules with collisions remain open, as do other update mechanisms and revisions to the proposed plaintext alignments.

The next discriminating question is whether a small number of third-position choices can explain the return structure without introducing an unconstrained rule for every selection. No such mechanism has yet been established.

The bridge pattern is prior work from [mvelzel/eye-vibe](https://github.com/mvelzel/eye-vibe/blob/main/docs/thirty-second-synchronizing-bridge-results-2026-07-26.md); the W1 context is also recorded in our [strong affine report](strong-affine-classification-findings.md). This pass derives and verifies the stated fixed-pivot consequences. It does not claim global priority for the invariant or a solution to Noita.
