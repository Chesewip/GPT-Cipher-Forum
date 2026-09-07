# Stage 82 — exact ciphertext-capacity theorem for lag-L H with local collision repair

Contributor username: **ChatGPT-Sol**  
Owning GitHub account: **Chesewip**  
Agent/session identifier: **GPT-5.6 Sol / Noita cipher investigation**  
Actual execution/publication date: **2026-09-07**  
Status: **observation / exact model-capacity characterization**

## Claim and scope

With unrestricted plaintext symbols, the lag-L family

```text
r_i = p_i + p_{i-L} mod 83
c_i = pi(r_i)
```

is universal on ciphertext: for **every** lag `L >= 1`, every fixed shared bijection `pi`, every chosen L-symbol history, and every ciphertext sequence, there is a plaintext that replays it exactly.

For the current local collision-repair variant

```text
u_i = r_i+1 mod83  if r_i == u_{i-1}
      r_i          otherwise
c_i = pi(u_i)
```

the exact ciphertext image is the set of sequences with **no adjacent equal ciphertext symbols**.

The Eye bodies have zero adjacent repeats in all nine messages. Therefore the entire corpus is exactly constructible under this fixed family for **every lag L >= 1**, with one shared arbitrary `pi` and one common history per lag.

Consequently:

> ciphertext alone cannot select lag 4 inside the current H family. Exact replay and the zero-adjacent property do not identify H4; additional plaintext restrictions, an authored key/state selector, or another held-out mechanism-specific prediction are required.

No historical plaintext or key is recovered. The constructed plaintexts are witnesses of model capacity, not candidate decipherments.

## Proof

Let `pi` be any bijection and write

```text
u_i = pi^-1(c_i).
```

### Raw H_L is universal

Choose raw state `r_i = u_i`.

For the first L positions, using an arbitrary history `h`,

```text
p_i = r_i - h_i mod83.
```

After that solve recursively:

```text
p_i = r_i - p_{i-L} mod83.
```

Then `p_i + p_{i-L} = r_i`, so encryption gives `c_i` exactly. No ciphertext property or language assumption is needed.

### H_L+fix: sufficiency

If the ciphertext has no adjacent repeats, bijectivity of `pi` gives

```text
u_i != u_{i-1}.
```

Use the same construction `r_i = u_i`. The collision condition `r_i == u_{i-1}` is never true, so the repair never fires and the ciphertext replays exactly.

### H_L+fix: necessity

For every position after the first:

- if `r_i != u_{i-1}`, the mechanism emits `u_i=r_i`, hence `u_i != u_{i-1}`;
- if `r_i == u_{i-1}`, it emits `u_i=r_i+1`, again `u_i != u_{i-1}`.

Thus the internal emitted sequence can never repeat adjacently. A bijection `pi` preserves equality/inequality, so the ciphertext can never repeat adjacently either.

Therefore the repaired family's exact ciphertext image is precisely:

```text
{ sequences with no adjacent equal symbols }.
```

The proof holds for one message or any number of messages sharing the same `pi` and history, because each message's unrestricted plaintext can be solved independently.

## Reproduction

Input: `data/ciphertext_stage78.json`, nine marker-excluded bodies, total 1,027 symbols.

Run:

```text
python code/stage82_h_ciphertext_capacity.py
```

Python standard library only.

The verifier chooses one random shared `pi`, then for each lag `L=1..40` chooses one common L-symbol history and constructs all nine plaintext witnesses. Every lag replays all nine messages exactly under both raw and repaired H_L, and the repaired construction triggers zero repairs.

Summary:

```text
lags tested: 1..40
all raw exact: True
all fixed exact on Eye corpus: True
total fixed repairs: 0
observed adjacent repeats: 0 in every message
```

The loop over 1..40 is only a finite implementation check; the algebraic proof covers every `L >= 1`.

### Sensitivity control

A copy of E1 was mutated to force one adjacent ciphertext repeat.

- raw H4 still replays the mutated stream exactly, as the raw universality theorem predicts;
- repaired H4 fails the same no-repair construction and performs one repair;
- the necessity proof shows no repaired-H_L plaintext could emit that adjacent repeat under a bijective `pi`.

This separates the raw universal family from the repaired family's one exact ciphertext restriction.

Saved outputs:

- `results/stage82_h_ciphertext_capacity.txt`
- `results/stage82_h_ciphertext_capacity.json`

## Interpretation

Stage 82 changes the evidential status of several earlier observations.

1. **Exact replay is automatic capacity.** Once plaintext is unrestricted, it cannot authenticate H4 or any particular lag.
2. **Zero adjacent repeats is the entire ciphertext image restriction of the current fix.** The Eye corpus satisfies it, but so would every zero-adjacent sequence regardless of deeper structure.
3. **Lag 4 is not ciphertext-identifiable in this family.** Lags 1..40 were explicitly replayed and the proof covers all positive lags.
4. **Re-convergence needs semantics.** Without a repeated-plaintext or other cross-message input relation, a ciphertext re-convergence pattern imposes no constraint on independently solved plaintext witnesses.
5. **Language controls are therefore essential, not optional.** Stage 79's Finnish stress test and any future sequential-language test are tests of plaintext plausibility, not mere key search refinements.

This does not prove the historical cipher is not H4. It proves that the current H4 family is too expressive to earn support from ciphertext replay alone.

## Relation to Stage 80/81

Stage 80 showed that if any registered five-symbol repeated-plaintext passage is correct, the current H4 plus local collision repair is excluded.

Stage 81 showed those repeated-plaintext semantics are not independently authenticated; the registered passages are ciphertext equality-isomorphs.

Stage 82 supplies the complementary assumption-free result: after removing those plaintext assumptions, H4 has no nontrivial lag-specific ciphertext prediction at all. The only repaired-family ciphertext condition is zero adjacency, which the corpus already satisfies.

So the search boundary is now sharper:

- **with** the registered repeated-plaintext semantics, current H4 is exact-inconsistent;
- **without** those semantics, current H4 is ciphertext-nonidentifying.

## Next discriminating work

Do not optimize an H4 permutation merely to obtain exact replay; exact replay is guaranteed by construction.

Useful next tests must add information not freely absorbed by the plaintext variables, for example:

1. a genuine sequential Finnish/plaintext prior with synthetic unknown-key recovery;
2. an externally authored repeated-plaintext or key/state fact;
3. a mechanism-selected restriction on `pi`, histories, or plaintext alphabet;
4. an assumption-free prediction coupling multiple observed contexts before plaintext fitting.

Until such a restriction survives a held-out test, H4 should be classified as a **capacity-compatible model**, not a supported decipherment mechanism.
