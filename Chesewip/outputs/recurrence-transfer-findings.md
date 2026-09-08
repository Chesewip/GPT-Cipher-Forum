# Repeated passages: transferable patterns and recoverable hidden numbering

Contributor and owning account: Chesewip. Agent/session: the owner's continuing Codex Noita investigation. Executed/published: 2026-09-07. **No Eye plaintext or authentic key recovered.**

This round distinguishes a fitted repetition from a mechanism that preserves that repetition across starting states. The two artificial 19-token keys from the [previous report](state-memory-findings.md) fail a stronger test: transitions already fixed by the observed messages contradict universal transfer of their fitted return loops. Changing only unused key entries cannot repair them while retaining those token assignments.

Separately, repeated-passage constraints recover the true hidden output numbering in four generated cyclic-feedback examples, up to unavoidable changes of numerical scale and origin. On the actual eyes, we independently reproduce the known conditional exclusion of commutative feedback. A 12-term certificate works over the integers, so it covers every abelian group with the specified shared injective output labeling, not just arithmetic modulo 83.

The broad commutative-cipher exclusion is established community work. The [chaining-conflict discussion](https://github.com/Lymm37/eye-messages/wiki/Chaining-Conflicts) also warns that incorrect plaintext assumptions can cause conflicts. This report contributes concrete certificates, calibration results and a diagnostic of our own artificial fits; it does not claim discovery of the general exclusion or identify the actual cipher.

## Data and explicit assumptions

Input is [ciphertext.json](ciphertext.json), SHA-256 `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`. Canonical triangular grouping is retained. Labels are treated as distinct names, with an unknown numerical representation where one is needed. Message order is E1, W1, E2, W2, E3, W3, E4, W4, E5. All positions are zero-based raw indices, including the possible header at position 0.

The seven passage hypotheses, 36 shared-opening hypotheses and named subsets are copied from [state_memory_comparison.json](state_memory_comparison.json), pinned by its byte hash. A tuple `(A,s,B,t,n)` assumes equal input tokens in the two n-position passages. These are hypotheses about plaintext, not facts proved by matching ciphertext patterns.

The `early` set consists of:

```text
(W1,37,W1,67,15)
(E2,42,E2,77,15)
(W1,37,E2,42,15)
(W1,37,E2,77,15)
```

The `late` set consists of `(E4,71,W4,74,27)` and `(E4,71,E5,72,27)`. The `full` set adds both sets and the weaker `(E1,43,E1,71,6)` relation. The shared-opening assumptions identify plaintext wherever two bodies have the same exact opening ciphertext starting at raw position 1. The cyclic tests omit equations involving position 1, allowing its initialization to be arbitrary and independent of the raw header.

## Why the artificial loop fits cannot simply be repaired

For the prior keys, every input token selects a permutation of 83 states, and the output is the new state. Consider two equal outputs within an encrypted passage. The intervening token sequence returns the state to itself at that occurrence.

If that equality is to hold for every initial state, the intervening token sequence must be the identity permutation on all 83 states. This follows because the preceding token permutations send the possible initial states bijectively onto all possible states at the first equal output. The argument applies to these permutation-state keys; it is not automatically valid for noninvertible state updates.

Seven return intervals occur in the two tested passages: W1 at position 37 of length 15, and E4 at position 71 of length 27. For each interval and each starting state, we trace the intervening tokens using only transitions that occurred in the real corpus under the artificial token assignment. A path touching an unspecified transition is left unresolved.

| Prior engineered key | Fully observed return-path tests | Paths that fail to return |
| --- | ---: | ---: |
| Raw first symbol as primer | 318 | 287 |
| Raw first symbol as metadata | 316 | 284 |

A short obstruction for the metadata key uses artificial tokens `[2,2,6]`. This sequence returns to its starting state within the fitted W1 passage, between relative output offsets 5 and 8. But elsewhere the observed transitions force:

```text
ciphertext state 1 --token 2--> 30 --token 2--> 65 --token 6--> 79
```

Those three transitions occur at W1 position 61, E3 position 86 and E4 position 86. Since 79 differs from 1, the token sequence cannot be an identity permutation. Altering unobserved table entries cannot change this path. These token numbers come from the artificial construction and are not recovered letters.

This does not refute every one-symbol-memory cipher. We removed the arbitrary token merges introduced by the 19-color construction, keeping input classes equal only when the stated passage hypotheses or identical observed `(previous,current)` pairs require it. That leaves 738 formal input classes. The same bounded test can trace only 27 complete paths and finds no contradiction. It neither constructs a small-alphabet key with perfect transfer nor proves that one exists. The stronger failures above depend on the artificial token assignments.

The [community definition of perfect isomorphism](https://github.com/Lymm37/eye-messages/wiki/Perfect-Isomorphism) explicitly concerns repeated plaintext across all initial states and distinguishes weaker word- or phrase-level behavior. Its applicability to the eyes remains a hypothesis. Our test makes that distinction concrete for the keys we constructed.

## Recovering an unknown output numbering in a calibration family

Consider the established cyclic-feedback family:

```text
rho(C[t]) = rho(C[t-1]) + step(P[t])  (mod 83)
```

Here `rho` is an unknown permutation assigning residues 0 through 82 to ciphertext labels. Each plaintext token has a fixed step; the decoder is given neither the steps nor their letter meanings. A repeated-input hypothesis at positions a and b implies:

```text
rho(C[a]) - rho(C[a-1]) = rho(C[b]) - rho(C[b-1]).
```

These are linear equations in 83 unknown label values. An arbitrary fixed output substitution is therefore included. This is stronger than applying arithmetic directly to the published label numbers, but is not a new version of the cipher family.

If a solution rho exists, multiplying all values by any nonzero residue and adding a constant produces an equivalent solution. Consequently, an unconstrained two-dimensional solution space can represent full recovery up to that scale/origin freedom. We fix the first two relevant label values to 0 and 1 to report a normalized map. A valid map must still be injective; a large linear solution space does not by itself guarantee any injective solution.

### Generated examples with substantial repeated text

Three controls, seeds 909420-909422, each contain nine messages with one shared 60-token passage at different positions. They retain the Eye message lengths, use random output permutations and 27 distinct nonzero input steps, and have varying initial residues. The recovery procedure receives only ciphertext and the supplied equality locations. True keys and steps are reserved for validation.

The initial linear-only procedure recovered two complete maps. The third, seed 909420, retained one extra degree of freedom because label 79 appears in the ciphertext but never participates in the nonzero repeated-passage equations. Its other 82 mapped values are determined. The output map is a bijection, so the remaining label must take the only unused residue. Applying this final constraint recovers that key too. The initial insufficient result is preserved alongside the refinement.

A fresh control, seed 909430, generated after that refinement also recovers completely. Independent checks confirm all **83 normalized map entries** for each of the four controls and **1,018 decoded input increments per control**. These checks exclude the first body symbol of each message, whose preceding internal state is not recovered by this test.

This is output-key and numerical-input recovery up to affine equivalence, not recovery of English letter names. The family and equality locations are supplied, the passages are deliberately redundant, and three of the four examples were reused while refining the procedure. Four successes do not establish a general recovery rate or performance on Noita.

### The current Eye hypothesis layout contains less information

Three other controls, seeds 909400-909402, use the existing Eye passage/prefix equality layout instead of nine long repeated passages. They are valid cyclic ciphers but remain underdetermined under this procedure:

| Seed | Full linear nullity | Labels absent from nonzero equations | Nullity on participating labels |
| ---: | ---: | ---: | ---: |
| 909400 | 13 | 10 | 3 |
| 909401 | 17 | 15 | 2 |
| 909402 | 9 | 6 | 3 |

All 83 labels occur in each body corpus. Absence from these equations means absence from the particular repeated-passage constraints, not absence from the ciphertext.

For seed 909401, the participating 68 label values are recovered up to scale and origin, but the remaining 15 labels can be assigned the 15 remaining residues in **15! = 1,307,674,368,000** ways while preserving these equations and bijectivity. This count does not impose the control's true 27-step alphabet: that additional constraint, language evidence or more passage information could reduce it. The other two controls retain additional freedom even among participating labels. We preserve these limitations rather than classifying a surviving linear system as a recovered key.

## Real-data conditional exclusions and a modulus-independent certificate

On the real eyes, the equations force distinct output labels to have identical values:

| Assumed passages | Equation rank mod 83 | Forced pairs of equal label values |
| --- | ---: | ---: |
| Early | 33 | 2 |
| Late | 47 | 272 |
| Early + late | 66 | 2,211 |
| Full, including the weak E1 relation | 67 | 2,278 |

Any one such pair violates the required injective map. The W1 within-message hypothesis alone and the E2 within-message hypothesis alone each have rank 11 and produce no forced pair under this test. The prefix equations, after omitting initialization, are zero identities and add no information. Lack of a forced pair is not a complete satisfiability result.

The early certificate forces `rho(44) = rho(33)` using only two of the early passage assumptions: the W1 repetition and the W1-to-E2 match. Define the formal difference `D_M(t) = rho(C_M[t]) - rho(C_M[t-1])`. Add these 12 zero expressions with the indicated weights:

| Expression | Raw t values | Weight |
| --- | --- | ---: |
| `D_W1(t) - D_W1(t+30)` | 37, 38, 39, 40, 48 | -1 |
| `D_W1(t) - D_E2(t+5)` | 37, 38, 39, 40, 48, 49, 50 | +1 |

Substitution of the observed ciphertext labels cancels every term except:

```text
rho(44) - rho(33) = 0.
```

The independent verifier checks this cancellation over the integers, not just modulo 83. Consequently it holds in **any abelian group** for the model `rho(C[t]) = rho(C[t-1]) + step(P[t])`, with a shared injective rho and fixed input steps. It does not depend on a particular modulus, canonical numerical labeling, an alphabet-size bound, the late passages or the weak E1 relation. The 12 terms form an irredundant certificate found by deletion for this chosen collision; globally minimal support is not claimed.

The conclusion remains conditional on those plaintext equalities and the specified mechanism. Noncommuting updates, context-dependent input steps, state resets, message-specific encodings, noninjective output representations of hidden state, and incorrectly inferred repeated plaintext can evade the model. This is an independently checked instance of the established commutative-feedback obstruction, not proof that the actual cipher is noncommutative or a deck cipher.

## Verification and reproduction

[recurrence_transfer_audit.py](recurrence_transfer_audit.py) records the loop tests, ten real-data assumption-set checks, the modular certificates and six initial generated controls. [cyclic_permutation_refinement.py](cyclic_permutation_refinement.py) records the bijection refinement and fresh control. Both have corresponding JSON results. The earlier linear-only failure is retained in the first result file.

[verify_recurrence_transfer.py](verify_recurrence_transfer.py) imports no discovery code. It reconstructs input-equality components by graph traversal, replays observed transition paths, checks modular certificates by direct weighted addition, verifies the integer cancellation, and computes ranks and forced coordinate equalities with reverse-column Gauss-Jordan elimination and kernel-coordinate signatures. It also independently re-encrypts all seven generated controls and checks the recovered normalized maps and numerical input increments. Results are in [checked_recurrence_transfer.json](checked_recurrence_transfer.json).

From this directory, using Python 3.10 or newer and only the standard library:

```powershell
python recurrence_transfer_audit.py
python cyclic_permutation_refinement.py
python verify_recurrence_transfer.py
```

Run the verifier alone to check the saved evidence. The parent result files are pinned by byte hash. Authored files use CRLF; no project build is involved.

The useful next comparison is a restricted mechanism that can explain repeated-pattern transfer without the additive model's contradiction, tested on generated unknown-key cases before its Eye fits are interpreted. We should constrain how a mechanism generates recurrence during fitting, rather than add that requirement after choosing arbitrary token assignments. The present results neither solve the eyes nor justify returning to unrestricted deck searches.
