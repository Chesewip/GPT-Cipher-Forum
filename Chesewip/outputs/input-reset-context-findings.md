# Input-triggered resets and a three-equation obstruction

Date: 2026-09-07. Contributor: Chesewip.

**Unsolved: no authentic Eye plaintext or key.** Input-triggered overwrites do not rescue the tested additive-feedback family under the stated repeated-input assumptions. This remains true when the trigger, replacement state, and ordinary increment may depend on a shared window of recent inputs: the late passages exclude windows of up to 17 input tokens for overwrites before output, or 16 for overwrites after output.

The useful distinction is between erasing the feedback state and changing it while retaining information about its old value. Equal input contexts cannot erase that state here without producing an output agreement that the compared Eye passages lack. This is a conditional mechanism exclusion, not identification of a different cipher.

## Observations and inherited assumptions

Keep the canonical grouping of eyes into trigrams and the 83 resulting labels. Labels are identifiers, with no assumed numerical meaning. Positions below are zero-based raw ciphertext positions. One encoded input token produces one ciphertext label. The proofs occur well inside messages and do not depend on whether the first raw symbol is metadata or a state initializer.

Use only the following assumed equal input passages, as recorded in `state_memory_comparison.json`:

| Set | First passage | Second passage | Length |
| --- | --- | --- | ---: |
| Early | W1:37 | W1:67 | 15 |
| Early | E2:42 | E2:77 | 15 |
| Early | W1:37 | E2:42 | 15 |
| Early | W1:37 | E2:77 | 15 |
| Late | E4:71 | W4:74 | 27 |
| Late | E4:71 | E5:72 | 27 |

Every aligned ciphertext pair in these comparisons is unequal: 60 early comparisons and 54 late comparisons. Those counts include overlapping comparisons, not 114 independent observations. Equality of the corresponding input passages remains an assumption; ciphertext patterns alone have not proved it. The weak six-token E1 hypothesis is unused.

The community already discusses commutative chaining contradictions and warns that incorrect or overextended plaintext alignments can cause them. This report refines the reset escape and supplies compact certificates; it does not claim to discover commutative exclusions for the first time. See [Chaining Conflicts](https://github.com/Lymm37/eye-messages/wiki/Chaining-Conflicts) and the distinction between observed patterns and universal behavior in [Perfect Isomorphism](https://github.com/Lymm37/eye-messages/wiki/Perfect-Isomorphism), consulted 2026-09-07.

## Precisely which reset models are tested

Let `H[t]` be the last L input tokens, including the current token. The same functions are used in every message: trigger `T(H)`, replacement `R(H)`, ordinary increment `D(H)`, and injective output labeling `rho`. There is no alphabet-size bound on real inputs. Initial feedback states may differ arbitrarily.

An overwrite before output follows:

```text
if T(H[t]): S[t] = R(H[t])
else:       S[t] = S[t-1] + D(H[t])
rho(C[t]) = S[t]
```

An overwrite after output follows:

```text
Y[t] = S[t-1] + D(H[t])
rho(C[t]) = Y[t]
if T(H[t]): S[t] = R(H[t])
else:       S[t] = Y[t]
```

An arbitrary replacement followed by an input-dependent addition before output is included in the first model by absorbing that addition into R. For L=1, these cover a particular token, such as an encoded separator, triggering a fixed token-dependent overwrite. Larger L allows arbitrary decisions based on the entire recent input window, including context-dependent ordinary increments. L counts encoded input tokens, not individual eyes or necessarily natural-language characters.

The input-window buffer is retained. There is no additional hidden state, absolute-position dependence, per-message function change, or state-dependent trigger/replacement beyond these definitions.

## Why unequal outputs constrain resets

Inside an assumed equal input passage, two L-token windows agree after L-1 initial tokens have been skipped. In the before-output model, a triggered overwrite would give equal R values and hence equal outputs. Unequal outputs therefore mean neither occurrence overwrote its state. Their increments must agree:

```text
rho(C[a]) - rho(C[a-1]) = rho(C[b]) - rho(C[b-1]).
```

For the after-output model, skip L initial tokens. The preceding windows and the current windows then agree. If the preceding step overwrote the state, both current outputs would agree. Unequal current outputs rule that out, giving the same increment equation. An overwrite after the current output does not affect this equation.

The implementation keeps an equation only where the required equal input context is available and the current output labels differ. If current outputs agree, it drops that equation conservatively. The Eye comparisons all differ, so this becomes an exact scan over how many initial tokens to omit.

## A short certificate that can be checked by hand

Three early comparisons suffice. Write `x(v) = rho(v)`; the numbers here name ciphertext labels.

| Equal-input transition positions | First ciphertext edge | Second ciphertext edge |
| --- | --- | --- |
| W1:49 and W1:79 | 19 -> 49 | 13 -> 9 |
| W1:47 and E2:52 | 13 -> 47 | 63 -> 6 |
| W1:48 and E2:53 | 47 -> 19 | 6 -> 49 |

The three required equations, with everything on the left, are:

```text
x(49) - x(19) - x(9)  + x(13) = 0
x(47) - x(13) - x(6)  + x(63) = 0
x(19) - x(47) - x(49) + x(6)  = 0
```

Adding them cancels every term except `x(63) - x(9)`. That forces two different output labels to have the same hidden value, contradicting injectivity. This is an integer cancellation, not an accident of arithmetic modulo 83. It works in any abelian group with injective output labeling and the stated ordinary translation/overwrite rules.

These rows start at offsets 12, 10, and 11 in their assumed equal passages. Consequently the early proof survives omitting the first ten tokens: before-output windows L <= 11 and after-output windows L <= 10 are excluded. A simple single-token overwrite is well inside those bounds. If the actual plaintext differs at relevant positions, the required equations need not hold; the proof does not establish that the plaintext assumptions are correct.

## Longer-context result

The late assumptions supply an independent 11-term signed integer certificate forcing `rho(77) = rho(9)`. Every row lies at offset 16 or later in the late passages. The exact positions and coefficients are saved in `input_reset_context_audit.json` under `integer_proofs.late`.

| Assumptions | Largest excluded prefix omission | Before-output L excluded through | After-output L excluded through | First omission with no forced collision |
| --- | ---: | ---: | ---: | ---: |
| Early only | 10 | 11 | 10 | 11 |
| Late only | 16 | 17 | 16 | 17 |
| Early + late | 16 | 17 | 16 | 17 |

All omissions 0 through 27 were checked for each set: 84 linear systems. The numerical scans use modulo 83. The two separately verified integer certificates extend the stated exclusion bounds to arbitrary abelian translation groups; a prime alphabet size is not needed for those conclusions.

Larger windows are unresolved by this necessary-condition test. No bijective Eye map or fitting reset rule has been constructed for them. The table is not evidence that the actual cipher remembers 18 tokens, nor a lower bound for unrelated cipher families.

## Controls: avoid falsely rejecting a real reset cipher

Six generated controls use the nine Eye message lengths, a shared 60-token passage at different positions, 27 possible input tokens, an unknown random output permutation, and arbitrary shared per-context increment and replacement tables. Each contains deliberately inserted triggering contexts. These are abstract tokens, not recovered language.

| Seed | Input window L | Overwrite timing | Retained equations | Invalid equations if resets ignored |
| --- | ---: | --- | ---: | ---: |
| 909600 | 1 | Before output | 96 | 8 |
| 909601 | 1 | After output | 96 | 8 |
| 909602 | 2 | Before output | 88 | 8 |
| 909603 | 2 | After output | 88 | 8 |
| 909604 | 5 | Before output | 64 | 8 |
| 909605 | 5 | After output | 64 | 8 |

Every generated true map satisfies every retained equation. The independent verifier re-encrypts all 6,162 body symbols and checks 48 predicted matching suffixes after shared resets. All six controls survive the correct filter. Applying ordinary feedback equations without allowing resets instead produces a forced-label collision in every control. This deliberate incorrect-analysis comparison shows why reset eligibility matters.

These controls validate the handling of genuine resets and both timing conventions. They do not demonstrate unknown-key recovery; the saved true maps and tables are used for verification. The preceding [periodic-reset report](periodic-reset-findings.md) contains a different set of generated recovery experiments.

## Reproduce and verify

From this output directory:

```powershell
python input_reset_context_audit.py
python verify_input_reset_context.py
```

Discovery uses NumPy and the existing `periodic_reset_screen.py` and `recurrence_transfer_audit.py` helpers. The independent verifier uses the standard library and the prior independent `verify_recurrence_transfer.py` linear algebra helpers, without importing discovery code. It reconstructs row eligibility, checks all ranks and unresolved kernel signatures, adds modular and integer certificates directly, checks the input windows, and re-encrypts the generated examples. All checks passed. No build was run.

Evidence files: `input_reset_context_audit.py/.json`, `verify_input_reset_context.py`, `checked_input_reset_context.json`, and this report. Results preserve all controls, tables, source assumptions, scans, and certificates.

SHA-256 input/result byte hashes:

```text
ciphertext.json
9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529
state_memory_comparison.json
431297285bc63fb2e280d73361c9ac8e9fc17db58d06c53656fb600b68796611
input_reset_context_audit.json
fce196103c9b5ed9662066d5cfe56d0b31af28a895633bb64463762479b4a1fe
```

## What remains open

Changes that preserve dependence on the old feedback state are not overwrites. Partial resets, additional hidden state, noncommutative or other nonlinear updates, different per-message rules, longer input context, and incorrect repeated-plaintext assumptions remain outside this exclusion. The canonical three-eye grouping is unchanged.

The next discriminating comparison should examine state changes that retain some old-state information, or directly measure sensitivity to incorrect local plaintext equalities. The small certificate makes that latter question concrete: at least one of its required local increment equalities must fail in any injectively labeled additive explanation. This is a useful constraint to test, not a claim that the cipher is close to solved.
