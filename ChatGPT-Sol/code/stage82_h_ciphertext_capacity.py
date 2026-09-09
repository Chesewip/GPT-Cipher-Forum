#!/usr/bin/env python3
"""Stage 82: exact ciphertext-capacity theorem for lag-L H with local +1 repair.

Family over Z_83:
    r_i = p_i + p_{i-L}
    fixed: u_i = r_i+1 if r_i == u_{i-1}, else r_i
    c_i = pi(u_i)

For i-L < 0, p_{i-L} is supplied by an arbitrary L-symbol history h.

The theorem:
1) Raw H_L (without repair) can replay ANY ciphertext stream exactly for any
   lag L>=1, any shared bijection pi, and any chosen history: take
   u_i=pi^-1(c_i), r_i=u_i and solve p_i=r_i-p_{i-L}.
2) H_L+fix can replay EVERY ciphertext stream with no adjacent equal symbols,
   by the same construction. Since u_i != u_{i-1}, the repair never triggers.
3) Conversely H_L+fix can NEVER emit adjacent equal ciphertext symbols: if
   r_i == u_{i-1} it increments, otherwise u_i=r_i != u_{i-1}. A bijection pi
   preserves inequality.

Hence the exact ciphertext image of H_L+fix, with unrestricted plaintext, is
the set of sequences with no adjacent repeats. Lag L is not identifiable from
ciphertext alone inside this family.
"""
import json, random
from pathlib import Path

N=83
HERE=Path(__file__).resolve().parent
DATA=HERE.parent.parent/"ChatGPT-Sol"/"data"/"ciphertext_stage78.json"
if not DATA.exists():
    DATA=Path("/mnt/data/noita_stage78/ciphertext_stage78.json")
D=json.loads(DATA.read_text(encoding="utf-8"))
MS={k:v["body"] for k,v in D.items()}
ORDER=["E1","W1","E2","W2","E3","W3","E4","W4","E5"]

def invperm(pi):
    inv=[None]*N
    for i,x in enumerate(pi): inv[x]=i
    return inv

def construct_plaintext(c, L, pi_inv, hist):
    """Construct p for the no-repair path r_i=u_i=pi^-1(c_i)."""
    p=[]
    for i,x in enumerate(c):
        u=pi_inv[x]
        lag=hist[i] if i<L else p[i-L]
        p.append((u-lag)%N)
    return p

def encrypt(p,L,pi,hist,fix):
    out=[]; prev=None; repairs=0
    for i,x in enumerate(p):
        lag=hist[i] if i<L else p[i-L]
        r=(x+lag)%N
        u=r
        if fix and prev is not None and r==prev:
            u=(r+1)%N
            repairs+=1
        out.append(pi[u]); prev=u
    return out,repairs

def adjacent(seq):
    return sum(a==b for a,b in zip(seq,seq[1:]))

print("STAGE 82 — H_L CIPHERTEXT CAPACITY / IDENTIFIABILITY")
print("dataset",DATA)
print("messages", {k:len(MS[k]) for k in ORDER})
print("observed adjacent repeats", {k:adjacent(MS[k]) for k in ORDER})
assert all(adjacent(MS[k])==0 for k in ORDER)

rng=random.Random(820082)
pi=list(range(N)); rng.shuffle(pi); inv=invperm(pi)

rows=[]
for L in range(1,41):
    hist=[rng.randrange(N) for _ in range(L)]  # one common history for all messages
    raw_ok=fix_ok=True
    total_repairs=0
    for k in ORDER:
        p=construct_plaintext(MS[k],L,inv,hist)
        c_raw,_=encrypt(p,L,pi,hist,False)
        c_fix,r=encrypt(p,L,pi,hist,True)
        raw_ok &= c_raw==MS[k]
        fix_ok &= c_fix==MS[k]
        total_repairs += r
    rows.append((L,raw_ok,fix_ok,total_repairs))
    print(f"L={L:02d} raw_exact={raw_ok} fix_exact={fix_ok} repairs={total_repairs}")
    assert raw_ok and fix_ok and total_repairs==0

# Sensitivity / converse check. Force an adjacent ciphertext repeat in a copy.
mut={k:list(v) for k,v in MS.items()}
mut["E1"][10]=mut["E1"][9]
assert adjacent(mut["E1"])>=1
L=4
hist=[rng.randrange(N) for _ in range(L)]
p=construct_plaintext(mut["E1"],L,inv,hist)
raw_mut,_=encrypt(p,L,pi,hist,False)
fix_mut,fix_repairs=encrypt(p,L,pi,hist,True)
print()
print("ADJACENT-REPEAT SENSITIVITY CONTROL")
print("forced E1 adjacent repeats",adjacent(mut["E1"]))
print("raw H4 construction exact on mutated stream",raw_mut==mut["E1"])
print("fixed H4 same construction exact",fix_mut==mut["E1"])
print("fixed H4 repairs",fix_repairs)
assert raw_mut==mut["E1"]
assert fix_mut!=mut["E1"]
assert fix_repairs>=1

print()
print("THEOREM CHECK SUMMARY")
print("lags tested",len(rows),"range",rows[0][0],rows[-1][0])
print("all raw exact",all(r[1] for r in rows))
print("all fixed exact on Eye corpus",all(r[2] for r in rows))
print("all fixed repairs on Eye corpus",sum(r[3] for r in rows))
print("ciphertext-only fixed-family invariant: adjacent ciphertext repeats must be zero")
print("Eye corpus satisfies that invariant, so every tested lag 1..40 has an exact construction.")
print("Algebra proves the same for every L>=1; ciphertext alone cannot select lag 4.")

out={
 "status":"exact model-capacity characterization; no plaintext recovered",
 "modulus":N,
 "dataset":str(DATA),
 "message_adjacent_repeats":{k:adjacent(MS[k]) for k in ORDER},
 "construction":{"shared_pi_seed":820082,"tested_lags":[1,40],
                 "one_common_history_per_lag":True,
                 "all_raw_exact":all(r[1] for r in rows),
                 "all_fixed_exact":all(r[2] for r in rows),
                 "total_fixed_repairs":sum(r[3] for r in rows)},
 "sensitivity":{"forced_message":"E1","forced_positions":[9,10],
                "raw_exact":raw_mut==mut["E1"],
                "fixed_exact":fix_mut==mut["E1"],
                "fixed_repairs":fix_repairs},
 "theorem":(
   "With unrestricted plaintext, raw H_L is universal on ciphertext sequences. "
   "H_L+fix has exact image equal to sequences with no adjacent repeats. "
   "Therefore the Eye corpus is exactly replayable for every L>=1 and lag 4 "
   "has no ciphertext-only identifiability inside this family."
 )
}
op=HERE.parent/"results"/"stage82_h_ciphertext_capacity.json"
op.write_text((json.dumps(out,indent=2)+"\n").replace("\n","\r\n"),encoding="utf-8",newline="")
print("saved",op)
