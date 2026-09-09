# Relationship-preserving key search: calibrated stopping point

Executed 2026-09-08. **Unsolved: no Eye key or plaintext recovered.**

The proposed relationship-based search has now been tested without supplied key entries on all three short generated controls. Each 30-second solver trial returns unknown due to timeout. An additional squaring trial with an explicitly derived pair relationship also times out. No candidate reaches held-out evaluation.

There is one verified example of a useful relationship that does not determine individual values: the squaring control requires the internal values of output labels 20 and 46 to be negatives modulo 83. This reduces their possible distinct-value pairs from 6,806 to 82 while leaving 82 possibilities for each entry. It is a relationship in a generated fixture under its known repeated-input constraints, not a new finding about the actual Eyes.

The agreed stopping criterion is reached: this representation still fails blind recovery on the short controls. We should pause further expansion of this specific feedback-family search and return to comparing mechanisms against observed message structure. These timeouts do not exclude the family, and they do not establish that the cipher is close to being solved.

## Model and information boundaries

The supplied functions are unchanged:

```text
rho(C[t]) = f(rho(C[t-1])) + code(P[t]) mod 83
f(x) = x, x^2, or inverse(x), with inverse(0) = 0
```

rho is a bijection of 0..82; at most 27 input code values are used. Each test is told the correct function. No true key entries, true code values, language scores, guessed words or global no-doubles rule are supplied. Addition alone uses the valid affine normalization rho(0)=0 and rho(1)=1. No numerical anchor is imposed on the nonlinear rules.

Use the unchanged Eye-length generated controls in `frozen_candidate_search.json`, seeds 909800..909802. Only messages 0..5 and their four early 15-position equal-input alignments enter fitting. This provides 671 decoded transitions and 60 input-equality comparisons. Messages 6..8, their 347 transitions and 54 late comparisons are reserved for evaluating any candidate. Raw position 0 is metadata, raw position 1 is an observed primer, and decoding starts at position 2.

The generated alignments are true by construction. Their analogues in the real Eyes remain unproved plaintext hypotheses. The canonical Eye corpus remains unchanged, SHA-256 `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`. This round performs no new search on that corpus because the blind controls do not qualify.

## What changes in this representation

The earlier custom domain propagation stored possible values for each key entry separately. That can lose a relationship such as `x = -y` when both individual domains remain broad. The earlier joint SMT solver already retained the complete equalities logically; this experiment tests a different encoding of the same information, not an additional source of evidence.

Repeated-input comparisons give linear equations in output values r and feedback values s. For addition substitute s=r. For the nonlinear functions retain both maps. Solve the linear system completely as an affine space:

```text
all map entries = particular solution + sum(parameter * basis direction) mod 83
```

The solver chooses the remaining free coordinates rather than assigning every map entry independently. All passage equations therefore hold by construction for every parameter assignment. The solver still must enforce output bijection, the function links s=f(r), and the input-alphabet cap on all fitting transitions.

Inactive feedback columns are removed from the solver's free-coordinate list because they do not appear in any passage equation or any other map expression. Their values are computed through the function link. This is elimination of unused coordinates, not extra evidence or a new constraint on the key.

All fields are modulo 83. Nonnegative weighted sums use 32-bit arithmetic with explicitly checked bounds before reduction; corrected seven-bit subtraction then forms transition residues. The largest possible linear sums in these encodings are 17,260, 27,306 and 34,112 respectively, so none can overflow its 32-bit representation.

## Blind results

Z3 5.1.0, solver seed 83, timeout 30,000 ms per check, excluding construction. Actual elapsed times can vary by installation.

| Supplied function | Linear rank | Affine dimension | Inactive feedback parameters omitted | Remaining solver parameters | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Addition | 39, including two normalization equations | 44 | 0 | 44 | Timeout; no key |
| Squaring | 28 | 138 | 49 | 89 | Timeout; no key |
| Inversion | 45 | 121 | 37 | 84 | Timeout; no key |

For comparison, the additive passage equations alone have rank 37 before normalization. The larger nonlinear parameter counts include feedback coordinates whose function links are imposed separately; these counts are not intrinsic key entropy or measurements of cipher difficulty.

The independent verifier proves that the saved bases describe the entire linear solution spaces, checks the omitted columns, and reconstructs each planted key from its coordinates. Thus the algebraic parameterization does not discard the known solution. It does not follow that the solver must find that solution within this budget.

## Explicit relational check in the squaring fixture

A saved linear-combination certificate from `passage_domain_search.json` gives:

```text
s(20) - s(46) = 0 mod 83
```

Under squaring, `r(20)^2 = r(46)^2`. Since the output map is a bijection, these distinct labels cannot have the same value. Over the prime field modulo 83 they must therefore satisfy `r(20) = -r(46)`, with neither value zero. In the representatives 0..82, their ordinary integer sum is 83.

An exhaustive check of all 6,889 ordered value pairs confirms exactly 82 solutions after excluding equal values. Every nonzero first value remains possible and determines the second value uniquely. The earlier separate-domain propagation could miss this relation because it did not combine the row constraint with pairwise inequality in its support calculation.

The extra blind trial adds the exact eight-bit sum constraint for labels 20 and 46 to the parameterized squaring solver. It also times out after approximately 30 seconds. The cut uses no planted numeric value and is already implied by the passage equations, squaring and bijection; it is a solver aid, not an independent assumption or new evidence.

## Interpretation and stopping decision

Across the recent rounds we have demonstrated assisted recovery, complete recovery on richer constructed data, and checked constraints that exclude particular conditional models. None supplies a blind short-control key for this family. This relationship experiment does not change that assessment.

The next research direction should compare mechanisms using observations that require no guessed plaintext: recurrence and transition structure, message boundaries, and the effects of alternative state memories or symbol interpretations. Any future return to this family should be motivated by an independently supported new constraint or a method that first succeeds on appropriate controls, rather than simply another increase in these search budgets.

No claim of worldwide novelty is made for affine parameterization, modular solving or pairwise constraints. The contribution here is a reproducible test of the proposed representation, a verified example of retained relational information, and an explicit negative calibration result.

## Reproduction and independent verification

From this directory:

```powershell
python relational_key_search.py
python relational_key_search.py --pair-cut
python verify_relational_keys.py
```

Discovery requires Z3. Verification uses Python 3.10+ and the standard library; it imports none of the new search implementation or Z3. Preserve the dated output when repeating timed searches because timing and solver outcomes may change. The first run was saved before the optional pair-cut field was added to the script; it has no pair cut, and absence of that field is equivalent to null in later runs.

The verifier reconstructs source equations, independently computes ranks, verifies the particular solutions and every basis direction, checks basis completeness and inactive-coordinate elimination, verifies the arithmetic bounds, and reconstructs planted keys within the parameterization. It replays the linear-combination proof for the pair relation and checks all possible value pairs. It also re-encrypts 3,081 generated body symbols. Any returned candidate would be checked directly against fitting and held-out data; none was returned. Solver timeouts remain logged outcomes, not independently proved exclusions.

All checks passed. Artifacts: `relational_key_search.py`, `relational_key_search.json`, `relational_pair_cut.json`, `verify_relational_keys.py`, `checked_relational_keys.json`. Earlier failures and assisted results remain intact. No project build was run.
