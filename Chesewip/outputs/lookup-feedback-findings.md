# Five-context certificate against arbitrary lookup-table feedback

Executed 2026-09-07. **Cipher unsolved. No plaintext or full-corpus key recovered.**

A new result in this investigation closes a gap left by our previous numerical scans: the feedback need not be linear, affine, or otherwise given by a simple formula. In the model

`C[t] = P[t] + F(C[t-1]) (mod 83)`,

where F is any one shared keyed lookup table and P uses any fixed encoding of plaintext into residues, five observed predecessor contexts force **at least 43 distinct input residues**. This is an exact ciphertext-only lower bound. It excludes every input alphabet of size at most 42 in that model, regardless of language or key.

The backward-reading variant needs at least 41. Related translation models modulo 125, with seven-bit XOR, or with three separate base-5 coordinates also require more than 40. This does not exclude all feedback ciphers, and it does not establish a deck mechanism.

## The five-context argument

Take every observed occurrence of a predecessor symbol x and collect the distinct symbols immediately following it into a set S_x. Under the proposed cipher, every member of S_x must decode by the same translation, subtracting F(x). Therefore the plaintext alphabet must contain a translated copy of each S_x.

Choose these five predecessor labels, ranked by the number of distinct successors (ties by label):

| Predecessor | Distinct observed successors |
| ---: | ---: |
| 26 | 19 |
| 60 | 18 |
| 54 | 17 |
| 64 | 17 |
| 5 | 16 |

They supply 87 distinct observed ordered pairs. Their exact successor sets and every source location are saved in `translation_set_bound.json`. No inferred plaintext equality enters the construction. Duplicate occurrences of a pair do not increase its weight.

We translate each of the five sets arbitrarily and minimize the size of their union. One common translation changes no union size, so the first shift can be fixed to zero. This leaves 83^4 = 47,458,321 relative assignments before pruning. Exact search gives a minimum union size of **43**. A realizing set of additive shifts is `[0,65,39,25,59]`; the union itself is saved. These shifts witness the optimum for the selected five contexts only. They are not a recovered key for the full ciphertext.

The independent verifier takes the claimed bound 43 and enumerates distinct partial unions that still contain fewer than 43 elements. After the fifth set, none survives. Separately, it verifies the supplied 43-element witness. Together these checks prove the selected-subset optimum, and hence the full-corpus lower bound. The full-corpus minimum may be larger.

This is stronger than saying an optimizer failed to find text. It proves that no choice of the 83-entry shift table can reduce these observations to a 27-symbol or 40-symbol input alphabet.

### Sensitivity to transcription errors

With the grouping and message order fixed, changing one raw trigram affects at most two adjacent-pair observations. Deleting those affected observations from the certificate can remove at most two successor-set elements. Removing d set elements can lower a minimum union by at most d: add those elements back under the same translations to prove the inequality.

Thus, even if one trigram was incorrectly transcribed and then corrected, the forward modulo-83 bound would remain at least **41**. More generally it remains at least `43 - 2e` under e trigram substitutions. This is a mathematical robustness bound, not a claim that transcription errors occurred. It does not address a different grouping or wholesale rearrangement of the eyes.

## Arithmetic and reading-order comparison

All cases use the same five-context selection rule, applied separately for each reading direction. The backward cases reverse each message body before collecting adjacent pairs.

| Translation group / representation | Forward lower bound | Backward lower bound |
| --- | ---: | ---: |
| Integers modulo 83, canonical labels | 43 | 41 |
| Integers modulo 125, canonical labels | 46 | 45 |
| Seven-bit XOR, canonical labels | 46 | 45 |
| Three base-5 coordinates, all common eye-direction numberings | at least 46 | at least 44 |

For separate base-5 coordinates, all 120 permutations assigning eye directions to digits reduce to six representatives. If two numberings differ by an affine digit change `d -> a*d+b`, where a is nonzero modulo 5, their translated-set union sizes are equal. Every numbering has a unique representative with its first two mapped digits 0 and 1. The six remaining permutations are explicitly enumerated and the orbit partition independently checked.

Permuting the three coordinate positions also preserves the quinary bounds: it is a bijective group map and converts each translation to another allowed translation. The original triangular grouping is retained. This does not cover arbitrary spatial traversals or regrouping eyes across trigrams.

## Separate result: all quinary linear feedback matrices

Before the arbitrary-table result, we tested

`P[t] = C[t] - A*C[t-1] + k` over the vector space F5^3,

where A is any 3 by 3 matrix and k is a common constant. This treats three base-5 digits separately, without integer carries. There are 5^9 = 1,953,125 matrices per numbering representative, giving **11,718,750 explicitly evaluated cases** across the six representatives.

Instead of guessing text, we maximize the number of equal decoded observation pairs. A decoded stream with N symbols over K distinct residues must have at least the balanced-distribution number of equal pairs: write `N = q*K+r`; the minimum is

`(K-r)*q*(q-1)/2 + r*q*(q+1)/2`.

For each possible matrix, equality of decoded positions is equivalent to `delta_C = A*delta_previous`. We aggregate those pair differences and evaluate every matrix exactly. The maximum attainable collision count then supplies a universal support lower bound.

Here N is 1,018. The six maximum collision counts are 6,650; 6,745; 6,682; 6,648; 6,640; and 6,742. They imply respective alphabet lower bounds **73,72,73,73,73,72**. Thus every direction numbering still needs at least **72 distinct input residues** in this linear-vector family. These are support bounds, not exact minimum support values; the matrix maximizing collisions need not minimize support.

This also covers an arbitrary invertible linear transformation on the current ciphertext term, because applying its inverse to all decoded residues preserves the support size. Coordinate permutations and affine changes of digit numbering preserve the family. Arbitrary nonlinear block relabeling, a singular current-symbol transformation, and higher-order feedback are not covered.

## Controls, verification, and an unsuccessful preliminary approach

- Four planted translation-set controls cover modulo 83, modulo 125, XOR, and quinary addition. Each has a known 27-element alphabet; the optimizer and independent verifier recover the exact minimum 27.
- Fifty small translation problems agree with exhaustive Cartesian-product searches over all relative shifts.
- Two generated full-message linear-quinary controls use unknown matrices and planted 27-symbol residue alphabets. Their planted decoding is reproduced and the exhaustive collision bound correctly permits 27.
- `verify_feedback_bounds.py` imports neither discovery script. For the union bounds it uses breadth-first sets of feasible unions instead of the discovery code's depth-first branch-and-bound. For matrix scores it counts all 124 nonzero, unnormalized difference vectors instead of the discovery code's 31 projective directions. All real matrix score histograms, maximizing witnesses, and generated decodings are checked.

A preliminary relaxation let each pair of predecessor groups choose its best relative shift independently. Its shifts need not be globally consistent. The resulting support bounds were only 20,21,21 for cyclic moduli 83,125,128, too weak to exclude 27. That unsuccessful approach is preserved in `feedback_collision_relaxation.py` and its JSON result. Cyclic modulo 128 in that preliminary calculation is distinct from XOR in the main table.

The independent checks passed. Results are in `checked_feedback_bounds.json`. This is a finite combinatorial proof, not a statistical significance claim, so no randomness null model is used to interpret the real-data exclusions.

## Scope and prior work

The nonlinear result requires a common feedback function across messages, a single previous ciphertext symbol as its argument, the stated output arithmetic, and one fixed plaintext-to-residue encoding. Arbitrary first body symbols are allowed. A common offset is absorbed into F. The argument does not exclude message-specific feedback tables or offsets, dependence on position or longer history, an unknown nonlinear permutation of output labels, or a plaintext encoding with many homophones, syllables, or other tokens. The number 43 counts encoded input residues, not necessarily human letters.

The corpus is `ciphertext.json`, SHA-256 `9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529`. Order is E1,W1,E2,W2,E3,W3,E4,W4,E5. We exclude the first raw symbol in every message before forming pairs, leaving 1,018 adjacent body observations. Source locations use zero-based raw indices. Existing provenance is retained; no new executable extraction was performed.

Ciphertext-autokey and nonlinear lookup-table feedback are established research avenues, not newly invented here. A [public Noita-Eyes research note](https://github.com/GarethLowe/Noita-Eyes/blob/claude/bootstrap-files-extract-myxfgl/CLAUDE.md), accessed 2026-09-07, explicitly lists nonlinear feedback as open after affine tests. Our preceding `nondeck-screen-findings.md` also tested only specified numerical families. The contribution here is the exact five-context alphabet certificate and its independently verified extensions. We have not performed an exhaustive literature review establishing global priority, and do not adopt the public note's other cipher exclusions as proven facts.

## Reproduce

From this directory with Python and NumPy installed:

```powershell
python translation_set_bound.py
python quinary_feedback_screen.py
python feedback_collision_relaxation.py
python verify_feedback_bounds.py
```

Run only the last command to verify the existing main evidence without repeating discovery. The first three scripts regenerate their result files. The quinary scan took about 54 seconds here; timing depends on hardware. All authored text uses CRLF. No project build was run.

The next useful targets are mechanisms this result distinguishes from its excluded family: nonlinear output substitution, message-dependent state, or encodings with more than 42 input residues. This result alone gives no ranking among them and no reason to return to deck research.
