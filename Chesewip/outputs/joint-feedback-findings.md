# Joint constraints and partial-key propagation on short controls

Executed 2026-09-08. **Unsolved: no authentic Eye key or plaintext.**

A local alphabet-cap filter now completes partial keys on all three existing Eye-length generated controls. Supplying 43 of the 83 key entries is sufficient for these particular masks; the additive model also uses its affine normalization. The input codebook is not supplied, and this propagation experiment uses no repeated-passage assumptions. Initially determined transitions reveal only 24 or 25 input values; pruning determines the remaining key entries and all 27 input values.

This is assisted recovery, not blind key discovery. With only 27 supplied entries, every fixture stalls. With no supplied entries, the propagation does no useful recovery beyond additive normalization, and a separate simultaneous solver times out on all three blind tests. The actual Eyes were not searched in this round because the blind controls did not qualify. No cipher family has been identified or excluded by these timeouts.

## Scope and assumptions

The three supplied rules remain:

```text
rho(C[t]) = f(rho(C[t-1])) + code(P[t]) mod 83
f(x) = x, x^2, or inverse(x), with inverse(0) = 0
```

rho is a permutation of 0..82 and the codebook contains at most 27 values. This round removes the global no-doubles code restriction used by the earlier discovery search. An absence of doubled outputs in the observed corpus does not justify assuming they are universally impossible.

Both methods are told which of the three functions generated each control. They do not discover the function. All partial-key entries are explicitly derived from generated truth and recorded as pins. The blind stage receives no key entries or input codes. For addition only, affine symmetry allows rho(0)=0 and rho(1)=1; generated truth is transformed into that gauge before pinning or comparison. This normalization is not plaintext knowledge.

Use the unchanged fixtures in `frozen_candidate_search.json`, seeds 909800, 909801 and 909802. Their nine message lengths match the canonical Eye corpus. Raw symbol 0 is metadata, raw symbol 1 is an observed primer, and decoding begins at raw position 2. Message indices 0..5 provide 671 fitting transitions; indices 6..8 provide 347 held-out transitions. The 54 late input-equality comparisons are checked only after a candidate is fixed. These generated fixtures have known truth and deliberately contain all 27 input values in fitting data. They are not three new independent ciphertext samples.

The simultaneous solver uses the four early alignments in `frozen_candidate_search.json`; propagation uses none. No language scores, true input codes, held-out symbols or held-out equalities enter either method's candidate selection. The source file and parent result hashes are recorded in each new artifact. The underlying Eye corpus is unchanged, SHA-256 `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`.

## Exact simultaneous solver pilot

`joint_feedback_constraints.py` puts every output-key value and a Boolean membership codebook into one constraint system. It enforces key bijection, the supplied feedback rule, the early equality hypotheses, and a maximum of 27 code values on every fitting transition. Seven-bit corrected subtraction represents residues modulo 83; this is not arithmetic modulo 128. A 128-bit membership vector has its unused upper bits fixed to zero.

Each check has a 12,000 ms solver timeout, excluding construction time. Solver seed is 83; installed Z3 version is 5.1.0. Missing labels are nested prefixes of deterministic random orders with seeds 909880..909882. Statuses below are actual run outcomes, not timing guarantees across installations.

| Supplied rule | Fully pinned baseline | 8 entries hidden | 24 entries hidden | All entries hidden |
| --- | --- | --- | --- | --- |
| Addition | Correct key | Correct key | Correct key | Timeout |
| Squaring | Correct key | Correct key | Timeout | Timeout |
| Inversion | Correct key | Correct key | Timeout | Timeout |

Every returned key matches canonical generated truth exactly and passes all held-out checks. As a negative encoding control, fixing the entire true key while lowering the alphabet cap to 26 is unsatisfiable for every fixture. This has an independent numeric explanation: each pinned key produces 27 distinct fitting residues. Blind timeouts are inconclusive even with the rule supplied.

## Propagation without repeated passages

`propagate_feedback_domains.py` gives each unpinned output label a domain of possible internal values. It repeatedly applies necessary conditions:

1. A value already assigned to another label cannot be reused in a permutation.
2. Trying one value determines input residues on transitions to or from already fixed neighbors. Reject it if these residues, together with all already determined residues, require more than 27 code values.
3. Once 27 code values are determined, a value must have compatible support across each observed transition within that codebook.

Each deletion records its label, value and reason for independent replay. The successful 40-hidden runs need only the first two rules; the third rule is available but contributes no deletions in those runs. No statistical approximation or guessed English is used in these filters.

| Rule | Explicit pins | Entries fixed initially, including normalization | Initially determined code values | Entries fixed at finish | Final code values |
| --- | ---: | ---: | ---: | ---: | ---: |
| Addition | 43 | 44 | 24 | 83 | 27 |
| Squaring | 43 | 43 | 25 | 83 | 27 |
| Inversion | 43 | 43 | 25 | 83 | 27 |
| Addition | 27 | 29 | 21 | 29 | 21 |
| Squaring | 27 | 27 | 23 | 27 | 23 |
| Inversion | 27 | 27 | 24 | 27 | 24 |
| Addition | 0 | 2 | 0 | 2 | 0 |
| Squaring | 0 | 0 | 0 | 0 | 0 |
| Inversion | 0 | 0 | 0 | 0 | 0 |

The 8-hidden and 24-hidden propagation runs also recover all three complete keys. Every complete recovery exactly matches canonical truth, uses a frozen 27-value codebook, has zero outside-codebook residues among 347 held-out transitions, and has zero mismatches among 54 late comparisons.

Thus the alphabet constraint can help before a complete active map or full codebook is known. The stronger general solver timing out at 24 hidden nonlinear entries does not imply the instance is intrinsically difficult: these inexpensive local deductions solve that same partial-key problem. The methods have different constraint sets and implementations, so this is an observed pilot comparison rather than a general solver benchmark.

There is only one nested hiding order per fixture. Forty hidden entries is a tested successful point, not a maximum repair radius or a claimed success rate across arbitrary masks. Moreover, knowing 43 key entries is a substantial advantage unavailable for the Eyes. Twenty-seven pins do not suffice for the implemented local rules in these masks; that does not prove the rest of the key is mathematically undetermined.

## Implication for the investigation

The present bottleneck is obtaining an initial map without true-key hints. Once a sufficiently useful partial map exists, even incomplete alphabet information can finish it on these short controls. That makes the local filter a candidate for pruning a future repeated-passage constraint search. It supplies no evidence that the historical cipher uses these specific feedback functions.

The previous [sparse-completion experiment](sparse-completion-findings.md) succeeded on richer generated messages after solving most of their linear maps. This experiment instead uses the short fixtures and explicit key pins to isolate the completion stage. Neither experiment has yet achieved blind recovery on the short fixtures.

## Reproduction and independent verification

From this directory:

```powershell
python joint_feedback_constraints.py
python joint_feedback_constraints.py --guards
python propagate_feedback_domains.py
python verify_joint_feedback.py
```

Only the simultaneous solver and its guards require Z3. Propagation and verification use the standard library. Running discovery again can alter timing fields or timeout outcomes; preserve this dated result when comparing new runs. The propagation result hashes the joint run whose hiding orders it uses.

The independent verifier imports none of the new discovery implementations. It checks every returned solver candidate by ordinary integer arithmetic; replays every propagation deletion from its local justification; checks that final domains reach a fixed point under the implemented rules; verifies that no true value was deleted; and reproduces frozen held-out scores. It also checks all 6,889 possible operand pairs for the corrected seven-bit subtraction and re-encrypts 3,081 body symbols in the three source fixtures. Saved negative cap guards are supported by independent counts of the pinned keys' 27 residual values. No independent proof is claimed for solver timeouts.

All checks passed. Artifacts: `joint_feedback_constraints.py`, `joint_feedback_constraints.json`, `joint_feedback_guards.json`, `propagate_feedback_domains.py`, `propagate_feedback_domains.json`, `verify_joint_feedback.py`, and `checked_joint_feedback.json`. Every successful or failed pilot stage is preserved. No project build was run.

This is a new calibration within our ongoing work, not a claim of worldwide novelty for constraint propagation or alphabet bounds. The preceding report credits existing community work on ciphertext feedback.
