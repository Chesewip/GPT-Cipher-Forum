#!/usr/bin/env python3
"""Stage 80: exact five-symbol repeated-plaintext obstruction for H4.

Current H4 core (body positions only):
    r_i = p_i + p_{i-4} mod 83
    raw:   u_i = r_i
    +fix:  u_i = r_i+1 mod83 if r_i == u_{i-1}, else r_i
    c_i = pi(u_i), with one shared bijection pi.

If two plaintext blocks have the same first and fifth symbols, then their raw
r-values at the fifth positions are identical. Hence:

* raw H4 requires the fifth ciphertext symbols to be equal;
* H4+fix, if the fifth ciphertexts differ, requires exactly one repair. The
  previous emitted internal value in the repaired context then equals the
  unrepaired fifth value. Bijectivity of pi therefore requires one of two
  visible cross-equalities:
      cA[fifth] == cB[previous]  OR  cB[fifth] == cA[previous].

A repeated plaintext block of length >=5 supplies the needed first/fifth
plaintext equality. The test is independent of the unknown pi, negative-history
seeds, plaintext alphabet labeling, and the intermediate three plaintext symbols.

The passage assumptions below are copied from the forum's
Chesewip/outputs/nondeck-screen-findings.md and use zero-based RAW positions,
including the message header at position 0. H4 operates on the body, so raw
position r>=1 maps to body index r-1.
"""
import json, random
from pathlib import Path

MOD = 83
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "ciphertext_stage78.json"
if not DATA.exists():
    DATA = Path("/mnt/data/noita_stage78/ciphertext_stage78.json")
D = json.loads(DATA.read_text(encoding="utf-8"))
BODY = {k: v["body"] for k, v in D.items()}

ASSUMPTIONS = [
    ("W1", 37, "W1", 67, 15, "within W1"),
    ("E2", 42, "E2", 77, 15, "within E2"),
    ("E1", 43, "E1", 71, 6,  "short within E1"),
    ("W1", 37, "E2", 42, 15, "cross W1/E2-a"),
    ("W1", 37, "E2", 77, 15, "cross W1/E2-b"),
    ("E4", 71, "W4", 74, 27, "late E4/W4"),
    ("E4", 71, "E5", 72, 27, "late E4/E5"),
]

def c(msg, raw_pos):
    assert raw_pos >= 1
    return BODY[msg][raw_pos - 1]

def obstruction_row(A, i, B, j):
    Aprev, A5 = c(A, i + 3), c(A, i + 4)
    Bprev, B5 = c(B, j + 3), c(B, j + 4)
    raw_ok = A5 == B5
    fix_ok = raw_ok or (A5 == Bprev) or (B5 == Aprev)
    local_handler_ok = fix_ok or (Aprev == Bprev)
    return Aprev, A5, Bprev, B5, raw_ok, fix_ok, local_handler_ok

print("STAGE 80 — EXACT FIVE-SYMBOL H4 OBSTRUCTION")
print("dataset", DATA)
print("positions are zero-based RAW positions; header=0; H4 body starts at raw=1")
print()
all_raw_fail = True
all_fix_fail = True
all_local_fail = True
for A, i, B, j, n, label in ASSUMPTIONS:
    assert n >= 5
    Aprev, A5, Bprev, B5, raw_ok, fix_ok, local_ok = obstruction_row(A, i, B, j)
    all_raw_fail &= not raw_ok
    all_fix_fail &= not fix_ok
    all_local_fail &= not local_ok
    print(f"{label:17s} {A}[{i}:{i+n}] == {B}[{j}:{j+n}]")
    print(f"  previous/fifth ciphertext: {A} {i+3}:{Aprev:02d} {i+4}:{A5:02d} | "
          f"{B} {j+3}:{Bprev:02d} {j+4}:{B5:02d}")
    print(f"  raw-H4 necessary fifth equality: {raw_ok}")
    print(f"  +fix necessary condition:        {fix_ok} "
          f"(cross {A5==Bprev} / {B5==Aprev})")
    print(f"  any trigger-only local handler:  {local_ok} "
          f"(prev-equal {Aprev==Bprev}; four-distinct={len({Aprev,A5,Bprev,B5})==4})")

print("\nSUMMARY")
print("all seven assumptions individually contradict raw H4:", all_raw_fail)
print("all seven assumptions individually contradict current +1 H4 fix:", all_fix_fail)
print("all seven assumptions individually contradict any trigger-only local collision handler:", all_local_fail)

def enc(p, hist, pi, fix):
    out=[]; prev=None
    for k, x in enumerate(p):
        lag = hist[k] if k < 4 else p[k-4]
        r=(x+lag)%MOD
        u=(r+1)%MOD if fix and prev is not None and r==prev else r
        out.append(pi[u]); prev=u
    return out

def local_condition(a, b, start):
    Aprev,A5=a[start+3],a[start+4]
    Bprev,B5=b[start+3],b[start+4]
    return (A5==B5) or (A5==Bprev) or (B5==Aprev)

TRIALS=10000
rng=random.Random(80080)
raw_viol=0; fix_viol=0; four_symbol_fix_fail=0
for _ in range(TRIALS):
    n=24; start=9
    pa=[rng.randrange(MOD) for _ in range(n)]
    pb=[rng.randrange(MOD) for _ in range(n)]
    pb[start:start+5]=pa[start:start+5]
    ha=[rng.randrange(MOD) for _ in range(4)]
    hb=[rng.randrange(MOD) for _ in range(4)]
    pi=list(range(MOD)); rng.shuffle(pi)
    ra=enc(pa,ha,pi,False); rb=enc(pb,hb,pi,False)
    if ra[start+4] != rb[start+4]: raw_viol += 1
    fa=enc(pa,ha,pi,True); fb=enc(pb,hb,pi,True)
    if not local_condition(fa,fb,start): fix_viol += 1

    pc=[rng.randrange(MOD) for _ in range(n)]
    pd=[rng.randrange(MOD) for _ in range(n)]
    pd[start:start+4]=pc[start:start+4]
    if pd[start+4] == pc[start+4]: pd[start+4]=(pd[start+4]+1)%MOD
    hc=[rng.randrange(MOD) for _ in range(4)]
    hd=[rng.randrange(MOD) for _ in range(4)]
    pi2=list(range(MOD)); rng.shuffle(pi2)
    fc=enc(pc,hc,pi2,True); fd=enc(pd,hd,pi2,True)
    if not local_condition(fc,fd,start): four_symbol_fix_fail += 1

print("\nPOSITIVE / SENSITIVITY CONTROLS")
print("trials",TRIALS)
print("five-symbol raw-H4 invariant violations",raw_viol)
print("five-symbol +fix invariant violations",fix_viol)
print("four-symbol-only controls failing the five-symbol condition",four_symbol_fix_fail,
      f"({four_symbol_fix_fail/TRIALS:.4f})")
assert raw_viol == 0
assert fix_viol == 0
assert four_symbol_fix_fail > TRIALS//2
