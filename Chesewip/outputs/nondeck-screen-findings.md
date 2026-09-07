# Non-deck comparison: feedback, position tables, and homophony

Executed 2026-09-07. **Unsolved: no authentic plaintext or key recovered.** Deck experiments were paused for this pass. None of the findings identifies a replacement cipher family, and eliminating these models does not establish a deck cipher.

## Results at a glance

| Candidate | Result | Main limitation |
| --- | --- | --- |
| Two simple numerical feedback/drift families | Every tested key leaves at least 82 or 83 distinct decoded residues | Exact only in the stated numerical representation and finite families |
| Shared position-dependent bijective substitution | A short conditional contradiction applies even without a repeating period | Depends on inferred plaintext equalities, including a weak short E1 match |
| Fixed homophonic substitution | Assumed passages force one symbol to occupy 84.23% of the bodies; a separate English attack finds no coherent text | Passage assumptions may fail; language search is heuristic and language-specific |

The useful methodological improvement is an unknown-key homophonic search that recovers over 99% of three generated English controls. Its result on the eyes remains negative, not a decipherment.

## Corpus and assumptions

The input is `ciphertext.json`; its hash is recorded in `nondeck_screen.json`. Message order is E1, W1, E2, W2, E3, W3, E4, W4, E5. There are 1,036 raw symbols with labels 0 through 82. We treat the first symbol of each message as a possible header and remove it from language tests, leaving 1,027 body symbols. Numeric tests use the existing trigram-derived labels as arithmetic coordinates; the table and homophone constraints use only equality of labels.

Every position below is zero-based in the raw message, including the first symbol. A tuple `(A, i, B, j, n)` assumes that the n plaintext symbols starting at position i in A equal those starting at j in B. These are hypotheses about plaintext, not observations proved by ciphertext.

- Within-message set: `(W1,37,W1,67,15)`, `(E2,42,E2,77,15)`, `(E1,43,E1,71,6)`.
- Cross-message additions: `(W1,37,E2,42,15)`, `(W1,37,E2,77,15)`.
- Late-family additions: `(E4,71,W4,74,27)`, `(E4,71,E5,72,27)`.

We test the within set, within plus cross, all three sets, all sets without the short E1 relation, and the late set alone. The late constraints were withheld from earlier fitting stages but were already known to the investigator: this is model holdout, not fresh blind data. Prior context interpretation and public-source credit are in `strong-affine-classification-findings.md`. This pass does not claim global novelty.

## 1. Numerical feedback and drift

For every coefficient pair a,b modulo M, we calculate:

- Second-order ciphertext feedback: `P[t] = C[t] - a*C[t-1] - b*C[t-2] (mod M)`. The header and first two body symbols are unconstrained initialization; 1,009 remaining outputs are evaluated.
- Linear position/header drift: `P[t] = C[t] - a*(t-1) - b*H (mod M)`, where H is the message's first symbol; all 1,027 body outputs are evaluated.

An arbitrary fixed plaintext-to-residue substitution and common additive offset are allowed. Arbitrary nonlinear relabeling of ciphertext and persistent message-specific offsets are outside these tests.

| Family | Modulus | Coefficient pairs | Minimum distinct residuals | First minimizing a,b |
| --- | ---: | ---: | ---: | --- |
| Feedback | 83 | 6,889 | 82 | 1,0 |
| Feedback | 125 | 15,625 | 83 | 0,0 |
| Drift/header | 83 | 6,889 | 82 | 44,75 |
| Drift/header | 125 | 15,625 | 83 | 0,0 |

Thus these formulas cannot expose a small fixed plaintext alphabet in the tested coordinates. The 82-symbol first-difference minimum is compatible with the already observed lack of adjacent equal ciphertext symbols; it is not a new promising key. Four generated controls, covering both families and moduli, verify planted 27-symbol plaintext residue alphabets and coefficients. All 45,028 real coefficient pairs were recomputed independently.

## 2. Periodic and arbitrary absolute-position substitution

The model uses an injective plaintext-to-ciphertext table for each phase `(t-1) % period`. Tables are shared across messages with a common reset phase. We also test a relaxation that allows different tables per message, thereby including arbitrary relative message phases.

For each assumed plaintext equality, we join the corresponding `(table owner, phase, ciphertext label)` nodes. A component containing two different labels in the same table is impossible. Saved exclusions include explicit paths of assumed equalities and observed symbol coincidences. A surviving component test is only a necessary condition: it does not supply a complete key or a small-alphabet assignment.

Periods 1 through 64 were tested across all five assumption sets and both table modes. With all assumptions, no shared-table period survives. With separate tables per message, many periods survive, starting at 8. Removing the short E1 assumption restores many shared-table survivors, starting at 17. Independently of passage assumptions, period 32 is the first tested shared-table period whose maximum number of observed labels per table is at most 27. This counting bound is necessary, not a solution; longer-period tables have substantial freedom.

A stronger conditional test gives every absolute position its own arbitrary shared table, without requiring periodicity. It still fails with the full assumptions. Here is the compact reason, writing `P_A[i]` for the plaintext at raw position i:

1. Assumed W1 repetition gives `P_W1[71] = P_W1[41]`.
2. Assumed cross-message repetition gives `P_W1[41] = P_E2[46]`.
3. E2 and E1 both have ciphertext 13 at position 46, so the shared invertible table gives `P_E2[46] = P_E1[46]`.
4. The short E1 assumption gives `P_E1[46] = P_E1[74]`.
5. E1 and W4 both have ciphertext 19 at position 74, so `P_E1[74] = P_W4[74]`.
6. The late-family assumption gives `P_W4[74] = P_E4[71]`.
7. Therefore W1 and E4 must have equal plaintext at position 71. Their ciphertext labels there are 46 and 56, contradicting the same position's injective table.

The weak short E1 relation is essential to this certificate. Removing it makes the arbitrary-position closure test survive. Consequently this is as much a check on our passage assumptions as on the cipher family. It does not exclude message-specific keys, phases, nonces, or history-dependent transformations. Fourteen generated table controls survive at their true periods. The independent verifier checked 642 table closures and 200 explicit contradiction paths.

## 3. Fixed homophonic substitution

Here each ciphertext label has one fixed plaintext meaning, but several labels may share that meaning. Assumed plaintext equalities force labels into common components. Components can merge further but cannot split.

| Assumption set | Maximum distinct plaintext symbols | Largest forced symbol count | Fraction of 1,027 body symbols |
| --- | ---: | ---: | ---: |
| Within only | 57 | 112 | 10.91% |
| Within plus cross | 46 | 288 | 28.04% |
| Full set | 18 | 865 | 84.23% |
| Full set without short E1 | 20 | 844 | 82.18% |
| Late only | 38 | 210 | 20.45% |

This is a poor ordinary-prose model if the assumed passages are correct. It is not a mathematical impossibility for arbitrary text or another encoded layer. Ten generated homophonic controls check that the component logic does not merge distinct known plaintext symbols.

### English search without passage assumptions

A separate attack supplies none of those equality assumptions. It learns joint tetragram log frequencies from Project Gutenberg 1342, *Pride and Prejudice*, and searches a fixed map from 83 ciphertext labels to lowercase English letters plus space. Generated controls use separated passages from Gutenberg 1661, *The Adventures of Sherlock Holmes*, with message lengths matching the eyes. Sources are stripped of Gutenberg boilerplate and normalized consistently. The original licensed texts and their hashes are retained.

The initial four-restart searches failed calibration on two of three controls, recovering about 1.95%, 2.63%, and 99.81%. We preserved that result in `homophonic_language_probe.json`. We then allowed one bounded extension of 16 additional restarts for each failed control, with no key hints or changes to the search algorithm. Winners were selected by language score, not known plaintext accuracy. Because the budget was increased after seeing failures, these are reused controls, not a fresh blind validation set.

The selected controls recovered **99.32%, 99.90%, and 99.81%** of plaintext symbols. The eyes received the same total budget of 20 restarts, each with 6,000 annealing steps and final greedy sweeps. The best result is degenerate text without coherent English. Mean tetragram log scores were approximately -8.787, -8.794, and -8.776 for controls versus **-11.994** for the eyes, with higher being better. Scores are an optimizer diagnostic, not calibrated probabilities or proof of unreadability.

This is negative evidence for a simple fixed English homophonic layer. Three generated controls cannot establish a general search success rate. Different languages, unusual plaintext, other homophone allocations, additional encoding layers, and missed optimization basins remain outside the conclusion. The saved status is `unverified_language_candidate`; readable-looking fragments are not claimed as plaintext.

## Verification and reproduction

`verify_nondeck_screen.py` does not import the discovery code. It independently enumerates numeric support with `numpy.unique`, rebuilds table and homophone components with graph traversal, checks certificate paths against observed ciphertext and the stated assumptions, and redecodes/rescores saved language candidates. It independently normalizes the source books and calculates string-keyed tetragram frequencies. Six saved language candidates were checked, including original failures and extended successes. All checks passed; see `checked_nondeck_screen.json`.

From this directory, with Python and NumPy installed:

```powershell
python nondeck_screen.py
python homophonic_language_probe.py
python homophonic_language_extension.py
python verify_nondeck_screen.py
```

The first three commands regenerate experiments and can take several minutes. The extension requires the initial probe result. Run only the last command to check the existing evidence without rerunning optimization. Keep the sibling `../work/pg1342.txt` and `../work/pg1661.txt` files available for language checks. No project build is needed.

The next comparison should broaden representations and language assumptions or test message-dependent mechanisms, with generated controls before interpreting failures. The short E1 equality deserves particular skepticism. These results provide no basis for returning to deck ciphers by elimination.
