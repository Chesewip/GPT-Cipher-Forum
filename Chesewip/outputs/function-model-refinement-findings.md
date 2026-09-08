# Function codebooks: a period-2 exclusion and intrinsic key ambiguity

Contributor and owning account: Chesewip. Agent/session: the owner's continuing Codex Noita investigation. Execution/publication: 2026-09-07. **No Eye plaintext or authentic key recovered.**

Six more settings from the [previous weaker-function screen](nonlinear-dependency-findings.md) are now excluded by independently checked contradictions. This leaves **272 unresolved settings out of the original 1,626**, with 1,354 excluded. A separate generated-control experiment establishes a useful limitation: even a known codebook and unlimited structurally valid ciphertext need not identify the original output key or plaintext.

These are two distinct results. The exclusions apply to the Eye corpus under the specified fractionation model. The key ambiguity applies to a particular generated codebook; it is not a discovered Noita key or a count of possible Noita keys.

## Model and data

Keep the canonical triangular grouping into output labels. Assign each observed label an arbitrary shared, injective coordinate triple over five values. No arithmetic meaning is assigned to the label numbers. Decrypt a block by flattening its mapped output triples, splitting the stream into three equal coordinate rows, and zipping those rows into input triples.

The input codebook has one specified coordinate that is an arbitrary function of the other two. The function is a 5-by-5 table with entries in 0 through 4; it need not be linear, invertible or Latin. A codebook may use only a subset of its 25 points. Any partial function on coordinate pairs can be extended to a full table, so exclusions for every full table also exclude such subsets.

All messages share the table, output mapping, period and reading treatment. The first raw symbol is either retained in every message or omitted in every message; retained bodies are either all forward or all reversed. Short final blocks are permitted. The new period-2 proof also permits a first block of length 1 or 2. The broader 1,626-case accounting still refers to full first blocks only.

Input: [ciphertext.json](ciphertext.json), SHA-256 `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`. The nine messages contain 1,036 raw labels, or 1,027 after omitting one per message. Message order is E1, W1, E2, W2, E3, W3, E4, W4, E5. No new transcription, guessed language, quotation or plaintext alignment is used.

## A counting proof closes period 2

Write a mapped output pair as `u=(u0,u1,u2)` and `v=(v0,v1,v2)`. Its two decoded input points are:

```text
P0 = (u0, u2, v1)
P1 = (u1, v0, v2)
```

Make a directed graph of observed full two-symbol blocks. Each distinct output label is a vertex; `a -> b` means that ordered pair occurs as a full block. Repeated occurrences contribute one edge. Singletons contribute no edges. An injective output mapping must embed this graph into the legal-pair graph on all 125 coordinate states.

If the first input coordinate is determined, `x=F(y,z)`, every target state in the complete legal-pair graph has exactly five possible predecessors. If the last coordinate is determined, `z=F(x,y)`, every source state has exactly five possible successors. The observed graph violates the respective limit in all eight boundary/read views.

The middle-coordinate case, `y=F(x,z)`, needs a different argument. The legal-pair equations are:

```text
u2 = F(u0, v1)
v0 = F(u1, v2)
```

For a fixed source state `u=(a,b,c)`, let `m` be the number of occurrences of value `c` in row `a` of the table. There are `m` choices of `v1`, five choices of `v2`, and then exactly one `v0`. Its outdegree is therefore `5*m`. The same multiplicity occurs in five states, one for each choice of `b`. Incoming degrees have the analogous form using column multiplicities.

For one chosen direction, let `H_k` count observed labels with degree greater than `5*(k-1)`, for `k=1,...,5`. At least `ceil(H_k/5)` row/value multiplicities must be at least `k`. Summing these necessary counts gives:

```text
sum over k=1,...,5 of ceil(H_k / 5) <= 25
```

Why 25? The sum of all row/value multiplicities is the number of cells in the function table. The same holds for columns. Using a smaller codebook can only remove legal edges and cannot evade this necessary bound.

Every tested view forces **26**, exceeding the table's 25 cells. For full first blocks, the compact certificates are:

| First raw symbol | Reading | Certificate direction | H1, H2, H3, H4, H5 | Required count |
| --- | --- | --- | --- | ---: |
| Retained | Forward | Incoming | 83, 37, 2, 0, 0 | 17 + 8 + 1 = 26 |
| Retained | Reversed | Outgoing | 83, 39, 2, 0, 0 | 17 + 8 + 1 = 26 |
| Omitted | Forward | Incoming | 82, 36, 3, 0, 0 | 17 + 8 + 1 = 26 |
| Omitted | Reversed | Outgoing | 83, 38, 2, 0, 0 | 17 + 8 + 1 = 26 |

All four short-first-block views also force 26 in a selected direction. Thus **eight views times three determined-coordinate choices, or 24 period-2 settings, are excluded**. Four of these resolve cases among the previous 278 survivors; the others were either already excluded or outside that full-first-block screen. Period 1 was already impossible because 83 distinct output labels cannot inject into at most 25 input points.

The independent verifier also checks a different finite relaxation: there are seven integer partitions of five describing a row's possible multiplicities. It enumerates all `7^5 = 16,807` ordered row-profile combinations. None provides enough state-degree capacity for any of the eight observed certificate vectors. This crosscheck does not rely on the summed-ceiling shortcut.

## Two further conditional-equality exclusions

A bounded graph refinement tests pairs among the 16 most frequent coordinate-equivalence classes in each of the 278 prior survivors. If assuming equality of two classes forces different output labels to collide, the pair must have different digit values. Six pairwise different classes cannot fit into five digits.

Two settings yield such six-variable certificates:

| Determined coordinate, zero-based | Period and full first block | First raw symbol | Reading |
| ---: | ---: | --- | --- |
| 1 | 32 | Retained | Reversed |
| 1 | 113 | Omitted | Reversed |

The independent checker replays all **30 conditional branches and 4,359 equality implications** in these two proofs. Other discovered real-data graph edges remain search metadata. Failure to find a six-clique in the bounded search does not prove that a key exists. Combined with the four new period-2 resolutions, the unresolved list falls from 278 to **272**; that list is saved in [checked_function_refinements.json](checked_function_refinements.json).

## Solver calibration: fitting is not always recovery

Two encodings were tried for an unknown function table and output mapping. An uninterpreted-function/bit-vector pilot timed out on four real period-2 settings and three generated controls at a five-second solver limit. An explicit Boolean finite-table encoding timed out on one real setting and one unknown-table control at a twenty-second solver limit. **All nine timeouts are inconclusive** and contribute no exclusions.

The Boolean encoding also received the actual table for two generated controls, while still searching for the output mapping:

| Generated control | Period | Result with table supplied |
| --- | ---: | --- |
| Seed 908210, first coordinate determined | 2 | Valid fit, but only 79 of 123 observed key entries match; 236 of 1,036 plaintext positions differ |
| Seed 908211, middle coordinate determined | 7 | All 125 observed key entries and all 1,036 plaintext positions recovered exactly |

Both satisfiable runs took about 1.6-1.8 seconds of solver time after model construction. Their saved maps are permutations and independently decode into their supplied codebooks. This is a **known-table calibration**, not blind recovery of an unknown cipher. In particular, the period-2 fit is not the original generated plaintext.

## An ambiguity that survives unlimited structural data

The period-2 discrepancy prompted a simpler experiment using generated control 908210's actual key and known table. All 7,749 two-entry swaps affecting at least one observed label were checked independently. Seventy-seven preserve sample codebook validity while changing the plaintext in a way that is not a fixed symbol renaming.

One compact example swaps output labels 12 and 79, which occur 16 and 27 times. Their original mapped codes are 25 and 29, respectively, corresponding to `(1,0,0)` and `(1,0,4)`. The swap changes **43 plaintext positions across all nine messages**, yet every decoded point remains in the same 25-point codebook. For example, the same original input code 5 becomes code 5 at flattened position 0 and code 9 at position 235. Indices and codes here refer to the generated control, not English letters or Eye plaintext.

This particular swap is not merely an accident of the sampled messages. For its known table, the two coordinate states have identical sets of legal successors and predecessors and the same singleton membership. Their transposition preserves membership for **all 15,625 ordered state pairs and all 125 singleton states**. Equivalently, direct encoding of all 625 permitted two-symbol input blocks gives a legal-pair set invariant under the swap.

Of those 625 plaintext blocks, **42 change under the alternative decoding**. Saved witnesses show context dependence at each plaintext position separately: even allowing a different fixed symbol renaming at the two positions does not explain the transformation. Since blocks are independent and singleton validity is preserved, the ambiguity extends to every message length under this period-2 schedule, including singleton boundary blocks.

More generally, the generated legal-pair graph has **21 live classes** of states with identical predecessor/successor sets and singleton membership. Permuting within those classes gives at least:

```text
3,522,410,053,632 output-map permutations
```

that preserve its entire structurally valid ciphertext language. The count excludes permutations confined to states that never appear in a legal pair or singleton; additional automorphisms may exist. It is a lower bound for **this generated codebook**, not a count of plaintext solutions and not a result about the actual Eye ciphertext.

The practical consequence is specific: structural codebook validity and exact re-encryption can fail to identify the authentic key, even with a known table and arbitrarily much such data. Language structure, known plaintext or other independently justified constraints can break these ambiguities. Future recovery benchmarks should record authentic plaintext recovery and context-changing symmetries, alongside ciphertext reproduction.

## Artifacts and reproduction

[verify_function_refinements.py](verify_function_refinements.py) uses the standard library and imports no discovery implementation. It reuses the earlier independent equality-proof replayer, reconstructs pair graphs, enumerates degree-capacity profiles, decodes saved solver witnesses, repeats the complete two-entry swap search, and independently constructs the complete legal-pair graph by encoding plaintext pairs. Three new period-2 controls, seeds 909120-909122, pass the degree bounds and known-key decoding checks. The three prior controls also pass their key/table checks and their saved conditional-inequality edges agree with their true digit values.

Run the independent check from this directory:

```powershell
python verify_function_refinements.py
```

Discovery commands, retained for reproducibility:

```powershell
python function_dependency_refinement.py --max-variables 16
python period_two_degree_certificate.py
python function_table_solver.py --timeout-ms 5000
python function_table_boolean_solver.py
python function_key_ambiguity.py
python function_graph_automorphisms.py
python verify_function_refinements.py
```

The solver pilots require z3-solver; tested with version 5.1.0 and Python 3.10.0. Other new scripts use the standard library. Graph refinement took about 187 seconds. Solver limits exclude construction time, which was about 7-15 seconds per Boolean run. Exact solver witnesses and timings may vary. Parent result byte hashes are checked; preserve the saved parent JSON when replaying its descendants.

Results are stored in the correspondingly named JSON files, with the bounded graph run in `function_dependency_refinement_16.json`, the two solver logs in `function_table_solver_pilot.json` and `function_table_boolean_pilot.json`, and the verification record in `checked_function_refinements.json`. No project build is involved.

## Limits and next discrimination

The remaining 272 full-first-block cases are unresolved, not validated cipher candidates. Non-period-2 short-first-block cases of the weaker model have not been exhaustively screened here. Arbitrary scattered codebooks without a determined coordinate, message-specific mechanisms, different eye traversals and other cipher families remain open. The previous stronger any-two-determine-third exclusion is unchanged.

This work does not identify a cipher family by elimination. A useful next test is to extend ciphertext-only compatibility constraints to the longer-period survivors while calibrating unknown-table recovery on controls that measure actual plaintext recovery and structural ambiguity separately. No global novelty claim is made for degree bounds, graph twins, equality propagation or the general distinction between fitting and identification.
