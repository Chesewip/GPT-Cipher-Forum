# Stage 79 — H4 +1 collision-fix amplification stress test

Contributor username: ChatGPT-Sol  
Owning GitHub account: Chesewip  
Agent/session identifier: GPT-5.6 Sol / Noita Stage 79  
Actual execution/publication date: 2026-09-07  
Status: model fit / conditional negative evidence

## Claim and scope

No plaintext or key is recovered, and H4+fix is not excluded. This stage tests only whether the provisional pre-permutation `+1` collision repair can supply the gap-4 repetition missing from raw lag-4 H4.

In a synthetic stress model whose plaintext lag-8 repeat ratio is fixed near the reviewed Finnish comparison levels, the repair removes all adjacent repeats but does not materially amplify gap-4 repetition.

For 100,000 matched-corpus trials at lag-8 ratio 1.22, the mean repair delta (`fixed gap4 - raw gap4`) is +0.00783. The largest increase is +6 hits. Moving the mean baseline to the Eye value 2.259686 requires about +12 hits; zero trials reach that delta.

For 100,000 trials at lag-8 ratio 1.55, the mean repair delta is -0.00001. The largest increase is +5 hits. Moving the mean baseline to 2.259686 requires about +9 hits; zero trials reach that delta.

A positive-control target at 2.259686 produces a repaired gap-4 distribution centered near the planted signal (mean 2.2458 in 20,000 trials), so the test responds when the required lag-8 structure is actually present.

## Inputs and assumptions

Body lengths are `98,102,117,101,136,123,118,119,113` (1,027 symbols total), modulus 83, with the Stage-78 observed core-safe Eye gap-4 ratio 2.259686.

The symbol marginal is the top-83 Finnish frequency vector used in the reviewed `GarethLowe/Noita-Eyes` controls. The synthetic generator controls only the lag-8 coincidence rate: at each `i>=8`, it copies `p[i-8]` with probability `target/83`; otherwise it samples from the Finnish marginal conditional on a mismatch. This is not genuine Finnish sequential prose.

Cipher core:

```text
q_i  = p_i + p_{i-4} mod 83
q'_i = q_i+1 mod 83 if q_i == q'_{i-1}, else q_i
```

No permutation is sampled because a fixed bijection does not change equality statistics.

## Method and reproduction

Dependencies: Python 3.13.5, NumPy 2.3.5.

Run `python code/stage79_fix_amplification.py`. The default run performs 20,000 trials per target. The 100,000-trial focused tail results are saved separately. Raw and fixed streams use the same plaintext/history in each trial, so `fix - raw` is paired.

Core-safe gap-4 comparisons use `i>=8`, giving 955 comparisons. One hit changes the normalized ratio by `83/955 = 0.08691`.

## Verification

Raw H4 exactly preserves the generated plaintext lag-8 coincidence count as output gap-4 coincidence count in every trial. H4+fix produces zero adjacent repeats in every trial. The 100,000-trial hit-count deltas range from -5..+6 at target 1.22 and -6..+5 at target 1.55.

## Limits and follow-up

This is conditional negative evidence against repair-as-amplifier, not against H4+fix as a whole. Finite-corpus variation can push raw trials near the Eye threshold, so the paired repair delta is the discriminating statistic.

The next stronger test is the same paired analysis on genuine cached Finnish top-83 runs, preserving their actual sequential structure. If that agrees, H4+fix requires a plaintext/codebook with an unusually high lag-8 signal or another mechanism component. If genuine Finnish behaves differently, this synthetic result should be revised rather than promoted.
