# Regular resets in relabeled additive feedback

Date: 2026-09-07. Contributor: Chesewip.

**The Eye cipher remains unsolved. No authentic plaintext or output map was recovered.** Under the explicit repeated-input assumptions below, regular arbitrary state resets cannot rescue the tested additive feedback family when the reset interval is at least four symbols and the phase is common to all messages. Allowing separate message phases weakens that conclusion: the early W1/E2 assumptions alone exclude every interval of at least 32 symbols. Shorter intervals retain unresolved cases; these are not keys.

Three generated examples provide a positive calibration: among intervals 1 through 32, the procedure isolates each planted nontrivial schedule and recovers all 83 hidden output-map entries up to affine equivalence. This establishes recovery on these redundant controls, not on the Eyes.

## Model and assumptions

Retain the canonical trigram decoding and treat the resulting 83 labels as arbitrary identifiers. Write rho for an unknown shared bijection from these labels to residues modulo 83. Away from a reset, require

```text
rho(C[t]) = rho(C[t-1]) + step(P[t])  (mod 83).
```

Each input token has one fixed step, shared across messages. The Eye exclusion does not impose an alphabet-size bound or require different tokens to have different steps. The state here is the previous output residue; there is no extra hidden state or changing output map.

Raw positions are zero based. Treat raw symbol 0 as metadata; body symbols start at raw position 1. Comparisons involving a transition at t < 2 are omitted. A periodic reset occurs when `(t - 1 - phase[message]) % B == 0`. At that output, discard the ordinary transition equation entirely. The reset may choose an arbitrary state separately at every boundary and in every message. This is a relaxation: an exact contradiction also excludes a more constrained reset rule with this same schedule and ordinary transition law.

The plaintext-equality assumptions are inherited from `state_memory_comparison.json`. A tuple `(A,s,B,t,n)` assumes the n input tokens starting at raw s in message A equal those starting at raw t in message B. Message order is E1, W1, E2, W2, E3, W3, E4, W4, E5.

| Set | Assumed identical input passages |
| --- | --- |
| Early | W1:37 and W1:67, length 15 |
| Early | E2:42 and E2:77, length 15 |
| Early | W1:37 and E2:42, length 15 |
| Early | W1:37 and E2:77, length 15 |
| Late | E4:71 and W4:74, length 27 |
| Late | E4:71 and E5:72, length 27 |

These are hypotheses about plaintext, not consequences established by a ciphertext isomorph. The weaker six-token E1 hypothesis is not used. A wrong equality can cause a contradiction even if the mechanism is otherwise correct. See the [preceding recurrence audit](recurrence-transfer-findings.md) for the community distinction between observed patterns and universal pattern preservation, and attribution for earlier commutative-feedback exclusions.

## Exact exclusions

Each assumed equal input at two nonreset positions gives the homogeneous linear equation

```text
rho(C[a]) - rho(C[a-1]) - rho(C[b]) + rho(C[b-1]) = 0  (mod 83).
```

If a modular linear combination of these rows equals `rho(label_x) - rho(label_y) = 0` for different labels, no bijective rho exists. Saved certificates specify the labels and the exact weighted rows. The verifier reconstructs those rows and adds them directly, independently of discovery elimination.

| Test | Assumptions | Exhaustive finite settings | Excluded | Unresolved |
| --- | --- | ---: | ---: | ---: |
| Common phase in all messages | Early + late | 9,316 | 9,311 | 5 |
| Independent W1 and E2 phases | Early only | 847,756 | 847,717 | 39 |

The common-phase scan covers all B from 1 through 136 and every phase. Its only unresolved `(B,phase)` pairs are `(1,0)`, `(2,0)`, `(2,1)`, `(3,0)`, `(3,1)`. B=1 discards every transition constraint and is a degenerate survivor. None of the four other settings yields an Eye output-map witness in this test.

The independent W1/E2 scan covers every pair of phases for every B from 1 through 136, exactly `sum(B*B) = 847756`. Phases with identical removed equation rows are grouped, and every group pair is checked. This compression produces 9,403 distinct equation systems and 25 reusable contradiction certificates. It does not sample phases.

Its 39 unresolved phase pairs occur only at B in `{1,2,3,4,5,6,7,9,29,31}`. The complete list is in `checked_periodic_resets.json`. In particular, isolated surviving alignments at 29 and 31 do not identify a reset interval. They simply avoid the forced-collision obstruction under this necessary-condition test.

Although the loops stop at 136, the exclusion extends to larger intervals on this finite corpus. There are at most 136 body symbols. An interval greater than 136 places at most one reset in each body. Every such finite schedule, including no effective reset, has a representative at B=136, for both common and independent phases. Consequently the first test excludes all common-phase B >= 4, and the early-only second test excludes all independent-phase B >= 32, within this model and its assumptions.

### Limited additional phase probes

A separate exploratory scan allows independent phases for all five messages involved in the early and late equalities. At B=4, the eleventh lexicographic phase vector is unresolved: `[0,0,0,0,0,0,0,2,2]` in canonical nine-message order. Its 61 active equations have rank 52, nullity 31, and 18 wholly unconstrained labels. This supplies no bijective key.

For B=7 and B=13, the first 1,000 lexicographic phase vectors each fail. These five-message probes are bounded, not exhaustive. The later exhaustive early-only test excludes B=13 but retains four early phase pairs at B=7. The pilot must not be described as an exclusion of every independent-phase B=7 setting.

## Generated recovery controls

The controls use nine messages of the Eye lengths, a random hidden output permutation, 27 distinct nonzero input steps, and random arbitrary reset states at their planted boundaries. Each has a shared 60-token input passage inserted at different positions in all nine messages. Recovery receives the locations of the equal passages; the saved true map and input contents are used for independent verification.

| Seed | Planted (B, phase) | Schedules tested | Nontrivial unresolved schedules | Map entries recovered | Nonreset increments checked |
| --- | --- | ---: | --- | ---: | ---: |
| 909500 | (7, 2) | 528 | (7, 2) only | 83 | 869 |
| 909501 | (11, 5) | 528 | (11, 5) only | 83 | 925 |
| 909502 | (17, 3) | 528 | (17, 3) only | 83 | 956 |

All three also retain the degenerate (1,0) schedule. The 528 settings are all phases for B=1 through 32; schedule uniqueness is asserted only within that range. The recovered maps match the true generated maps after an affine change `rho -> a*rho+b`, with a nonzero modulo 83. That scale and origin cannot be determined by these equality equations.

The independent check also re-encrypts the entire generated corpus using the saved true steps, initial states, and reset states. Recovery does not identify letter names, recover a general reset-state key, or decode the first body input. These controls contain deliberately strong repeated-passage evidence in a known family; they are not an estimate of real-world solve probability.

## Reproduction and evidence

From this output directory:

```powershell
python periodic_reset_screen.py
python reset_phase_coverage.py
python verify_periodic_resets.py
```

Discovery uses NumPy and the earlier `recurrence_transfer_audit.py` equation builder. The verifier uses the standard library and earlier independent `verify_recurrence_transfer.py` helpers; it does not import either new discovery script. It checks exact certificate sums, active-row eligibility, unresolved ranks and kernel signatures, complete phase coverage, generated encryption, and recovered maps. All checks passed, including 861 certificate checks across the real scans and generated controls. No project build is needed.

Files: `periodic_reset_screen.py/.json`, `reset_phase_coverage.py/.json`, `verify_periodic_resets.py`, and `checked_periodic_resets.json`. The main JSON preserves the bounded pilot and all generated ciphertext, input, maps, and reset states. The coverage JSON preserves phase groups, system references, and proof certificates.

SHA-256 provenance (JSON byte hashes, not script hashes):

```text
ciphertext.json
9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529
state_memory_comparison.json
431297285bc63fb2e280d73361c9ac8e9fc17db58d06c53656fb600b68796611
periodic_reset_screen.json
2b0ae66c4976dbecd97a3dfca8dbc6a27bc709ecbba284240fbae2f902a79e97
reset_phase_coverage.json
32709cf90bf21d3627bc6d2f72e3ffdeb8fcf4cff2f49481125de3b400afe6c8
```

## Interpretation and next discriminating test

Regularly spaced arbitrary resets are a substantially constrained escape from the earlier additive-feedback contradiction. This result concerns a shared relabeled additive model; it does not exclude reset mechanisms with changing output maps or step tables, nonadditive transitions, irregular boundaries triggered by input, or additional hidden state. Nor does it weaken the canonical grouping of eyes into threes by itself.

A useful next comparison is an input-triggered boundary rule: the same input token should cause the same reset behavior wherever the assumed passages repeat. Unlike an unrestricted choice of exceptional positions, that hypothesis makes predictions across passages. First test those predictions on generated examples and then on the stated Eye equalities. The present result does not establish that such a rule is present, or that a breakthrough is imminent.
