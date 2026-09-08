# Nonlinear coordinate codebooks: an equation-free exclusion

Contributor and owning account: Chesewip. Agent/session: the owner's continuing Codex Noita investigation. Execution/publication: 2026-09-07. Status: exact exclusion under the specified encoding and schedule; weaker models remain unresolved. **No plaintext or authentic key recovered.**

The previous [linear-codebook result](scattered-codebook-findings.md) assumed a particular kind of equation between the three input digits. This round removes the equation entirely. For the fractionation model below, a codebook in which **any two input coordinates uniquely determine the third** cannot generate the Eye corpus. This holds with an arbitrary unknown output-symbol substitution and short first and last blocks.

All **37,534** tested nontrivial shared block configurations have independently replayed contradiction certificates. This is not an exclusion of every 25-symbol codebook, arbitrary 27-symbol alphabets, or fractionation in general. The coordinate-dependency property is a substantive encoding assumption.

## Exact assumption and data

Suppose two permitted input codes agree in any two coordinate positions. The assumption says they must also agree in the remaining position. For example, a codebook cannot contain both `(0,2,1)` and `(0,2,4)`. The analogous restriction must hold for each of the three choices of coordinate pair.

This includes nonlinear Latin-square codebooks and their subsets, but does not require a full square or a chosen operation. It only requires the three uniqueness properties on the permitted triples. Such a codebook has at most 25 triples over five digits. Arbitrary scattered alphabets need not have those properties, even when they contain 25 or fewer symbols.

Input is [ciphertext.json](ciphertext.json), SHA-256 `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`. Canonical triangular grouping and message order E1, W1, E2, W2, E3, W3, E4, W4, E5 are retained. Raw lengths are 99, 103, 118, 102, 137, 124, 119, 120, 114. This round uses symbol identity, not the numerical base-5 value of the observed label. No new image transcription, language assumption, quotation or repeated-plaintext equality is introduced.

An arbitrary shared injective mapping assigns each observed output label to a triple over five coordinate values. An unknown fixed input codebook obeys the uniqueness properties above. To decrypt a block of n mapped output triples, flatten them into 3n digits, split that stream into three n-digit rows, and zip the rows into input triples.

The schedule permits a common period B, a common first-block length R with `1 <= R <= B`, full subsequent blocks of length B, and a possibly shorter unpadded final block. We test all B from 2 through the longest retained message and every R. Either all first raw symbols are retained or all are omitted; bodies are read either all forward or all reversed. Every retained symbol is used.

Settings and mapping are shared across messages. A short first block is not a cut through a partly missing larger encrypted block. A common permutation of output-coordinate positions is absorbed into the unknown output mapping. Periods above the maximum retained length add no new partitions. Period 1 cannot bijectively map the 83 observed label distinctions into an input codebook of at most 25 symbols.

## How the proof works

Each coordinate of each output label starts as a formal variable. Repeated appearances of a label reuse its variables. This does **not** assert that different variables have different digit values; it records only equalities that are known.

After routing variables into input triples, suppose two triples have already-known equal first and second coordinates. The codebook assumption then forces equality of their third coordinates. Apply the corresponding rule for each coordinate pair, repeatedly. If the process forces all three coordinates of two different output labels to agree, an injective mapping is impossible.

Each equality step is saved as two input-row indices and the coordinate being equated. A verifier needs only to check that the other two coordinates are already equal. There is no guessed key, Latin-square enumeration, language score or solver timeout in a contradiction certificate.

Some settings require the five-value limit as well. Pick six formal coordinate variables. For each of their 15 pairs, temporarily suppose the two variables have the same value. If every such supposition forces an output-label collision, those six variables must be pairwise different. Six different values cannot fit into a five-value coordinate alphabet.

## Complete result and the three difficult settings

The initial variable-boundary screen found:

| Initial outcome | Configurations |
| --- | ---: |
| Directly forced output collision | 37,523 |
| Six-variable pigeonhole certificate | 8 |
| Equality closure survived | 3 |

The three survivors were preserved, then refined separately:

| Period B | First block R | First raw symbol | Body reading |
| ---: | ---: | --- | --- |
| 117 | 5 | Retained | Reversed |
| 121 | 1 | Retained | Reversed |
| 117 | 4 | Omitted | Reversed |

For each survivor, the refinement considers the ten most frequently occurring coordinate-equivalence classes and tests their 45 possible equality hypotheses. A graph edge records a proved inequality. Each graph contains a six-vertex clique, yielding the required 15-branch certificate. The final result is **37,523 direct-collision certificates plus 11 six-variable certificates**, covering all 37,534 configurations.

The final proof uses only the selected clique edges. Other discovered graph edges are search metadata, not additional independently checked claims. The initial three survivors remain visible in [latin_dependency_boundaries.json](latin_dependency_boundaries.json); their resolutions are in [latin_boundary_refinement.json](latin_boundary_refinement.json), pinned to the parent result's byte hash.

## A weaker model remains partly open

We also test only one uniqueness rule at a time: a specified input coordinate is an arbitrary function of the other two. The function may be nonlinear and need not be invertible. This is weaker than requiring all three pairwise rules.

This separate screen uses a full first block, a short final block, shared periods, both common reading directions and both common first-symbol choices. Each possible determined coordinate receives 542 settings:

| Determined coordinate, zero-based | Direct collisions | Additional six-variable certificates | Closure survivors |
| ---: | ---: | ---: | ---: |
| 0 | 445 | 4 | 93 |
| 1 | 444 | 0 | 98 |
| 2 | 451 | 4 | 87 |
| Total | 1,340 | 8 | **278** |

Thus **1,348 of 1,626** cases are excluded. The 278 survivors are unresolved; equality closure is not a complete five-value constraint solver and does not construct a fitting output map. This weaker screen does not include the variable first-block lengths of the main result.

## Generated controls and independent verification

Three generated Latin-codebook controls use seeds 908200, 908201 and 908202, random output permutations, and settings `(B,R) = (2,2), (7,3), (13,5)`. The latter two include markers, and the third reverses its body. Each contains nine messages of the same plaintext lengths as the Eye corpus and all 25 input symbols.

Their tables are constructed by backtracking, have permutation rows and columns, and are checked to be nonassociative and outside the earlier family `a*x + b*y + z = d`. All three survive the correct dependency screen. Three further controls, seeds 908210 through 908212, use arbitrary non-Latin function tables, one for each determined coordinate. They survive the appropriate weaker screen. These are soundness controls with known generating keys, not blind key-recovery claims.

[verify_nonlinear_dependencies.py](verify_nonlinear_dependencies.py) imports no discovery code. It constructs input rows by scattering each output coordinate to its destination; discovery traces each input coordinate back to its source. It independently checks every recorded equality implication, final output collision, pair coverage in every six-variable certificate, completeness of the configuration lists, and the generated controls' actual coordinate values.

[checked_nonlinear_dependencies.json](checked_nonlinear_dependencies.json) records:

- **5,521,017** equality implications replayed for the main final certificates.
- **165** conditional equality branches checked across the eleven six-variable certificates.
- All 1,626 weaker-model cases checked, including fixed-point checks for the unresolved equality closures.
- Six generated controls and **6,216** generated plaintext symbols replayed.
- All 542 cases of the original full-first-block closure pilot replayed.

The plain-text pilot counts for the single-function screen also match the later certificate screen. The discovery and refinement runs took about 176 and 5 seconds respectively in this environment; the weaker screen took about 10 seconds.

## Reproduction and limitations

All scripts use the Python standard library; executed with Python 3.10.0. From this directory:

```powershell
python nonlinear_coordinate_closure.py
python latin_dependency_screen.py
python latin_boundary_refinement.py
python one_coordinate_function_screen.py
python verify_nonlinear_dependencies.py
```

Run the refinement after the boundary screen: it records that screen's hash, including its runtime field. Proof payloads use base64 of zlib-compressed records containing two little-endian 16-bit row indices and an 8-bit determined-coordinate index. They are decoded and checked by the independent verifier. No project build is involved.

This result removes the linear-equation restriction from the preceding 25-point exclusion and also permits short first blocks. It still requires an injective shared output mapping, a shared block schedule and a fixed input codebook with the stated coordinate uniqueness. Arbitrary scattered codebooks, extra symbols violating those uniqueness rules, message-specific mechanisms and other eye traversals remain open. No global novelty claim is made for equality propagation or pigeonhole reasoning, and no cipher family is identified by elimination.
