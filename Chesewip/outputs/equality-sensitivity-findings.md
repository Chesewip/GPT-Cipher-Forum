# How many repeated-input assumptions must change?

Date: 2026-09-07. Contributor: Chesewip.

**No authentic Eye plaintext or key was recovered.** For the relabeled additive-feedback model modulo 83, allowing one or two local mistakes in the early repeated-input assumptions does not remove the contradiction. The late assumptions need at least four individual exceptions. Together, the assumptions require at least ten individual exceptions among 141 compared input positions; the exact combined minimum remains unresolved.

These counts concern a necessary linear test. A second check exposes its limitation concretely: the saved minimum nine-column relaxation passes the forced-pair test, but every one of its 83 normalized candidate numberings for the constrained labels has a collision. That particular relaxation cannot yield any bijective key.

Two generated controls with deliberate input differences recover their exact minimum exception counts, the changed positions, and all 83 hidden output-map entries up to affine scale and origin. These are controlled recoveries, not Eye decipherments.

## Scope and assumptions

Use the canonical ciphertext and three-eye grouping unchanged. Numeric labels are arbitrary identifiers. The model is

```text
rho(C[t]) - rho(C[t-1]) = step(P[t])  (mod 83),
```

where rho is one shared bijection onto the 83 residues, and each encoded input token has a fixed shared increment. There is no input-alphabet-size bound or guessed language, and different input tokens may share increments. Initial states may differ. One input token produces one ciphertext label. No resets, context-dependent increments, position-dependent maps, or additional hidden state are included in this audit.

This returns to the basic model to measure assumption sensitivity; it does not extend the fault-count bounds to the broader context-reset families in the [preceding report](input-reset-context-findings.md). Unlike that report's two integer certificates, the new optimization bounds are specifically checked modulo 83.

The six inherited repeated-input assumptions are:

| Set | First passage | Second passage | Length |
| --- | --- | --- | ---: |
| Early | W1:37 | W1:67 | 15 |
| Early | E2:42 | E2:77 | 15 |
| Early | W1:37 | E2:42 | 15 |
| Early | W1:37 | E2:77 | 15 |
| Late | E4:71 | W4:74 | 27 |
| Late | E4:71 | E5:72 | 27 |

Positions are zero-based raw positions. Message order is E1, W1, E2, W2, E3, W3, E4, W4, E5. All comparisons are inside the bodies, so the proofs do not depend on the interpretation of the first raw symbol. The weak E1 assumption is unused.

The assumption graph contains 15 early template columns, each with four occurrences, and 27 late columns, each with three occurrences: 42 columns and 141 distinct input positions. Repeated ciphertext structure does not establish equal plaintext. The community's [Chaining Conflicts discussion](https://github.com/Lymm37/eye-messages/wiki/Chaining-Conflicts) already warns about incorrect or overextended alignments; this audit quantifies sensitivity for one precise model rather than treating that warning as resolved.

## Two different exception counts

A **column exception** drops the identical-input requirement for a whole template slot across all its copies. This is deliberately generous and is not a count of individual typos.

An **occurrence exception** frees one specified input position. All other copies of that template slot must still agree with each other. If the original reference occurrence is freed, the remaining copies stay tied together; the implementation does not accidentally discard their relationships. It constructs the full equality classes first and compares the retained occurrences using a spanning tree.

No ciphertext symbol is edited. An exception relaxes a plaintext hypothesis. The affected inputs may differ for any reason; calling them natural-language typos would assume more than the evidence provides.

| Assumptions | Minimum column exceptions to pass the forced-pair test | Minimum occurrence exceptions to pass that test |
| --- | ---: | --- |
| Early only: 15 columns / 60 positions | 3, exact | 3, exact |
| Late only: 27 columns / 81 positions | 3, exact | 4, exact |
| Together: 42 columns / 141 positions | 9, exact | Between 10 and 22; exact value unresolved |

The upper bound of 22 is a saved occurrence relaxation with no forced equal-label pair, not a bijective map or a reconstructed plaintext. The lower bound of ten means that any actual cipher in the specified family satisfying an approximately common input template must deviate at at least ten of these positions. It does not prove ten deviations suffice.

The joint result is stronger than simply adding the separate column minima, because both sets must use the same hidden output values. The separate surviving linear systems are not recovered compatible keys.

Example minimum occurrence relaxations saved by discovery are E2 raw positions 46, 51, and 53 for the early set, and E4 positions 80, 90, 97 plus E5 position 84 for the late set. These are examples satisfying the weakened linear criterion. They are not uniquely identified errors or proposed readings of the real plaintext.

## Exact lower-bound certificates

Every retained equal-input pair supplies a row

```text
rho(C[a]) - rho(C[a-1]) - rho(C[b]) + rho(C[b-1]) = 0.
```

Discovery searches for a small exception set. Whenever the retained equations force two different output labels equal, it saves a modular row-combination certificate. At least one column, or one endpoint occurrence, supporting that certificate must be freed. This gives a clause requiring the exception set to hit the certificate's support. Additional certificates refine the search.

A finite hitting-set lower bound and an explicit surviving linear system establish each exact minimum in the table. The independent verifier reconstructs all rows and support sets, checks the modular sums, and uses a separate standard-library combinatorial search to check the saved clauses. It does not call Z3 or import the discovery scripts. For the joint column minimum, the reduced clause family has 535 clauses and the independent search visits 7,557 nodes. The final occurrence lower bound uses 1,483 reduced clauses and 1,460,447 search nodes to rule out every set of at most nine occurrence exceptions.

Whole-column bounds also give valid occurrence lower bounds: any set of k freed occurrences touches at most k columns. Freeing those whole columns is an even weaker system. This implication is used explicitly where sufficient, rather than treating unverified search output as a proof.

## The nine-column survivor is not a possible key

The saved joint nine-column exception set leaves a linear system of rank 64. Sixteen labels never occur with a nonzero coefficient in these rows; the other 67 constrained labels have three dimensions of linear freedom.

For a hypothetical injective map, fix two constrained labels to values 0 and 1 using the arbitrary affine scale and origin. This leaves exactly one parameter modulo 83, hence 83 candidate assignments for the 67 constrained labels. The audit enumerates all of them. Every assignment gives the same value to two distinct constrained labels.

The 16 unconstrained labels cannot repair those collisions. Thus no bijection completes this particular nine-column survivor. The saved affine-space basis, particular solution, and a collision pair for each parameter value form a finite independently checked certificate.

This does not exclude every possible nine-column exception set: only the one saved by the minimum search received this complete bijection check. It does show that the forced-pair criterion can pass even though no single collision-free assignment exists. Which pair collides can change with the free parameter, so no one pair needs to be forced equal in every solution.

## Generated recovery controls

Both controls use nine messages of the Eye lengths, random input tokens from a 27-token alphabet, an unknown random output permutation, distinct nonzero token increments, and a common 60-token passage inserted at different positions. After constructing the common passage, selected occurrences are changed by one token and the messages are encrypted normally. Discovery receives ciphertext and the deliberately imperfect passage-equality hypotheses, not the true map, changed positions, or exception count.

| Seed | Planted changed positions | Minimum found, both metrics | Recovered output-map entries |
| --- | ---: | ---: | ---: |
| 909700 | 2 | 2 | 83 |
| 909701 | 3 | 3 | 83 |

For both metrics, the resulting active linear system has rank 81 and determines the full map up to affine scale/origin. The independent verifier compares the recovered map against the planted map, identifies the changed occurrences from their differing recovered increments, and re-encrypts all 2,054 body symbols using the saved true inputs, steps, and initial states. Every check passed.

These controls have far more repetition than the Eye assumptions and use a known mechanism. They calibrate the ability to tolerate and locate a few wrong equality assumptions; they are not a success-rate estimate and do not recover letter names.

## Bounded attempts and reproduction

The initial searches use Z3 5.1.0, a 90-second outer limit and a 2,000-candidate limit per case, and 5 seconds per Boolean solver call. The early/late minima and joint column minimum completed. The joint occurrence run stopped with lower bound seven after 413 iterations. The already established column result separately improves that to nine.

A seeded default-solver retry, allowing 20 seconds per call, made no new candidate progress beyond the inherited bound nine. A finite-domain SAT retry, with a 120-second outer limit and 20-second calls, generated 512 new contradiction certificates and established the checked lower bound ten. It did not finish the optimization. Time limits are stopping rules, never exclusions.

Sixteen greedy reinstatement pilots are also retained. Seeds 909720 through 909727 start from all occurrences in the saved nine-column exception set and each finish with 22 freed occurrences. Seeds 909730 through 909737 start with all occurrences freed and finish with costs 25, 26, 25, 30, 29, 24, 23, and 30. Their final feasible linear systems are independently checked; no global optimality is claimed for these pilots.

From this output directory:

```powershell
python equality_sensitivity.py
python equality_sensitivity.py --refine
python equality_sensitivity.py --sat
python sensitivity_witness_audit.py
python verify_equality_sensitivity.py
```

Discovery uses NumPy, Z3, and the existing `periodic_reset_screen.py` elimination helper. The witness audit uses NumPy and the new discovery problem representation. Verification uses the standard library and the earlier independent `verify_recurrence_transfer.py` helpers. No build is needed. Bounded reruns may find different witnesses or stop at different bounds, so verify the saved evidence for the precise results reported here. The finite-map audit is specialized to the saved low-dimensional witness; it is not a general large-nullspace key search.

Files include the two discovery/audit scripts, the independent verifier, `equality_sensitivity.json`, the two refinement JSON files, `sensitivity_witness_audit.json`, and `checked_equality_sensitivity.json`. The latter records byte hashes for every source result and input, as well as the detailed independent check counts. Canonical ciphertext SHA-256 remains `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`; assumption-parent SHA-256 remains `431297285bc63fb2e280d73361c9ac8e9fc17db58d06c53656fb600b68796611`.

## Interpretation

The additive contradiction is not caused solely by one or two mistaken local equalities. Nevertheless, similar-looking passages can contain genuine input differences, and this work does not establish their contents. Neither the ten-position lower bound nor the generated recoveries identifies the historical cipher.

The next useful comparison should let candidate mechanisms explain approximate repetition and then require a full bijective map and independent predictions. The saved nine-column counterexample makes it particularly important to stop treating a surviving linear screen as a key candidate that already fits the model.
