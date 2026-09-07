# Unknown output substitutions still require every coordinate value

Contributor and owning account: Chesewip. Agent/session: the owner's continuing Codex Noita investigation. Execution/publication: 2026-09-07. Status: exact structural exclusion; cipher unsolved.

**No plaintext or authentic key recovered.** Allowing an arbitrary shared substitution of entire ciphertext symbols does not rescue coordinate-fractionation codebooks that omit a digit from any input coordinate, under the shared block schedule below. Every coordinate must use all five values. This is a restriction on the shape of the codebook, **not a lower bound of 125 input symbols**. A scattered 27-symbol codebook remains possible; a generated counterexample demonstrates the distinction.

This extends the direct-coordinate test in [fractionation-boundary-findings.md](fractionation-boundary-findings.md) across a previously excluded output-substitution layer. The two results have different scope: this round permits arbitrary output relabeling but requires the block settings to be shared across messages. We do not combine their conclusions as if their assumptions were identical.

## Model and data

The input is [ciphertext.json](ciphertext.json), SHA-256 `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`. Canonical triangular grouping is unchanged; message order is E1, W1, E2, W2, E3, W3, E4, W4, E5, with raw lengths 99, 103, 118, 102, 137, 124, 119, 120, 114. Source records remain in [provenance.json](provenance.json). No new image transcription or plaintext quotation is used.

An unknown shared injective mapping assigns each observed ciphertext label to one of 125 triples over digits 0 through 4. It need not respect the numerical value of the observed label. Unobserved labels can complete the map to a permutation of the full cube.

To encrypt a block of n input triples, concatenate its n first coordinates, n second coordinates, and n third coordinates; regroup the stream into output triples; apply the unknown output substitution. Decryption reverses those steps. Input symbols have fixed coordinate triples. Their letter names and language are unconstrained.

The schedule has a common period B and common first-block length R, with 1 <= R <= B. Later blocks have length B except for a possibly shorter, unpadded last block. We test B from 2 through the longest retained message, every R, forward or reversed bodies, and either retaining or omitting the first raw symbol of every message. All choices are shared across messages. Every retained symbol is used. A short first block is not an unknown cut through a larger block with missing data.

Periods beyond the longest message add no new partitions. A common within-output-trigram coordinate permutation is absorbed into the arbitrary output mapping. A common renumbering of the five digit values is likewise absorbed. Independent message-specific maps, periods, coordinate conventions or omission choices are not covered.

## The obstruction: too many labels for the available triples

Suppose one input coordinate never uses digit 0. Whenever a coordinate of an output label is routed into that input coordinate, that output coordinate cannot be 0. Repeated appearances of the same ciphertext label accumulate these restrictions because its unknown triple is fixed.

For each label and target input coordinate, record which of the three output coordinate positions must avoid 0. There are only eight such routing-mask types. Each type permits a precisely enumerable set of output triples. If a set of labels has fewer available triples than labels, no injective output mapping exists. This is a pigeonhole certificate, or equivalently a violation of the necessary matching condition.

Digit 0 is representative: if the omitted digit were any other value, a common digit renaming would turn it into 0 without changing the routing or injectivity. We check all three input coordinates separately. We do not need to guess the actual output map.

For example, with B = R = 2, forward reading and the first symbol retained, all **83 labels** must avoid 0 in two particular output coordinates when testing omission from the first input coordinate. Only **4 x 4 x 5 = 80 triples** meet those restrictions. The other two input coordinates each give the same 83-versus-80 contradiction, with different constrained output positions.

The complete discovery run covers **37,534 configurations** and supplies **112,602 certificates**, one per input coordinate per configuration. Every certificate succeeds. An independent implementation verifies all of them; the smallest label-count excess over available triples is 2.

Therefore, for every tested B >= 2 setting, any fitting input codebook must use all five values in **each** of its three coordinates. This excludes, for example, any codebook contained in a 3 x 3 x 3 rectangular arrangement, or any raw coordinate codebook wholly inside the first 27 numerical slots of the 125-cell cube. It does not exclude an arbitrary selection of 27 scattered slots.

## Unknown-map recovery controls and the rectangular search

The initial search directly tested rectangular input sets A x B x C and solved the resulting injective output-label assignment by bipartite matching. It enumerates 641 canonical triples of nonempty digit subsets. Each of the five digits has one of eight memberships in the three sets; sorting those memberships quotients a common digit renaming without losing a case.

For a full first block and shared settings, 546 configurations were tested. The four period-1 settings have minimum bounding-prism volume **100**; all 542 nontrivial settings require **125**. Period 1 preserves 83 symbol distinctions, and the smallest product of three dimensions no larger than five that can contain 83 cells is 100. The stronger coverage certificates independently establish the 125 result for nontrivial periods, including additional short-first-block settings.

Three generated controls start from a 27-cell rectangular codebook with coordinate sets `{0,1,2}`, `{2,3,4}`, and `{0,1,4}`. They apply a random unknown permutation of all 125 output triples. Each uses plaintext lengths 103, 113 and 127, includes all 27 input symbols, and permits a short final block.

| Seed | Planted period | First-symbol/body convention | Observed output labels | Discovery minimum |
| --- | ---: | --- | ---: | ---: |
| 907410 | 7 | No marker, forward | 92 | 27 |
| 907411 | 11 | Prepended marker, forward | 85 | 27 |
| 907412 | 13 | Prepended marker, reversed | 87 | 27 |

In each control, the unique minimum among the tested reading/period settings identifies the planted settings and yields a valid unknown output map into a 27-cell prism. This is structural recovery. The original random permutation and plaintext letter identities need not be uniquely recovered.

The independent verifier replays all **1,526 saved control mapping witnesses** and all **1,029 planted plaintext symbols**. It checks the saved minimizer claims against the saved scans, but does not independently repeat exhaustive global optimality searches for the controls. Their runtime was included in the approximately 74-second rectangular discovery run.

## A counterexample that prevents overinterpretation

[scattered_coordinate_control.json](scattered_coordinate_control.json) uses seed 907413 to generate a different 27-symbol codebook, scattered across all five values in every coordinate. With period 7 and an unknown output substitution, it produces nine messages using 125 output labels. All three coordinate-coverage certificates succeed at the planted period, yet the generating input alphabet has only **27 symbols**.

The independent verifier replays its encryption/decryption and checks the three certificates. It proves by construction that requiring a 125-cell bounding prism does not imply 125 input symbols. This artificial example does not fit the real Eye messages or their 83-label alphabet.

## Verification and reproduction

[verify_coordinate_coverage.py](verify_coordinate_coverage.py) imports no discovery code. It starts with each input-coordinate position and traces it back to its output source; discovery starts with output coordinates and records their destinations. The verifier explicitly enumerates all 125 triples to check certificate capacities. It checks completeness of the configuration list, every certificate, real-data mapping witnesses, control mappings and the scattered-codebook counterexample. Results are in [checked_coordinate_coverage.json](checked_coordinate_coverage.json).

All scripts use the Python standard library; executed with Python 3.10.0. From this directory:

```powershell
python unknown_map_prism.py
python coordinate_coverage_certificates.py
python scattered_coordinate_control.py
python verify_coordinate_coverage.py
```

Discovery results are in [unknown_map_prism.json](unknown_map_prism.json) and [coordinate_coverage_certificates.json](coordinate_coverage_certificates.json). The latter stores compact routing-type certificates, not a large collection of guessed keys. Its discovery run took approximately 30 seconds. Discovery runtime fields change on rerun. No project build is used.

## What remains open

This closes the unknown-output-map escape for input codebooks with an omitted coordinate value, within the stated schedule. It leaves arbitrary scattered codebooks using all five coordinate values, message-specific settings, other transpositions and noninjective output mechanisms open. Our generated scattered control shows why that remaining distinction matters.

The next useful question is whether the *relationships between complete input triples*, beyond their individual coordinate ranges, constrain an unknown output map enough to test scattered small codebooks. That needs a calibrated recovery method; these certificates alone do not solve it. No global priority claim is made for the coordinate-routing or matching methods, and these negative results do not identify a deck cipher by elimination.
