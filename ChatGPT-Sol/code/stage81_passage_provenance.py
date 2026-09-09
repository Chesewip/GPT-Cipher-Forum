#!/usr/bin/env python3
"""Stage 81: audit the registered repeated-plaintext assumptions at ciphertext level.

This script does not infer plaintext. It checks what the seven registered tuples
actually establish in the canonical ciphertext:

* the paired ciphertext windows are not literal copies;
* they have identical normalized equality signatures;
* equivalently, each pair admits a one-to-one partial symbol relabeling.

That is exactly an equality-isomorph observation. It is compatible with repeated
plaintext under some cipher models, but by itself it does not prove repeated
plaintext.

Positions are zero-based RAW message positions including the first header at 0,
matching Chesewip/outputs/nondeck_screen.py.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parent.parent / "ChatGPT-Sol" / "data" / "ciphertext_stage78.json"
if not DATA.exists():
    DATA = Path("/mnt/data/noita_stage78/ciphertext_stage78.json")
D = json.loads(DATA.read_text(encoding="utf-8"))
RAW = {k: [v["header"]] + v["body"] for k, v in D.items()}

ASSUMPTIONS = [
    ("W1", 37, "W1", 67, 15, "within W1"),
    ("E2", 42, "E2", 77, 15, "within E2"),
    ("E1", 43, "E1", 71,  6, "short within E1"),
    ("W1", 37, "E2", 42, 15, "cross W1/E2-a"),
    ("W1", 37, "E2", 77, 15, "cross W1/E2-b"),
    ("E4", 71, "W4", 74, 27, "late E4/W4"),
    ("E4", 71, "E5", 72, 27, "late E4/E5"),
]

def signature(seq):
    names = {}
    next_id = 0
    out = []
    for x in seq:
        if x not in names:
            names[x] = next_id
            next_id += 1
        out.append(names[x])
    return tuple(out)

def partial_bijection(a, b):
    f, inv = {}, {}
    for x, y in zip(a, b):
        if x in f and f[x] != y:
            return False, None
        if y in inv and inv[y] != x:
            return False, None
        f[x] = y
        inv[y] = x
    return True, dict(sorted(f.items()))

records = []
print("STAGE 81 — REGISTERED PASSAGE CIPHERTEXT AUDIT")
print("dataset", DATA)
print("coordinate convention: zero-based raw positions, header=0")
print()
for A, i, B, j, n, label in ASSUMPTIONS:
    a = RAW[A][i:i+n]
    b = RAW[B][j:j+n]
    assert len(a) == n and len(b) == n
    sig_a, sig_b = signature(a), signature(b)
    bij, mapping = partial_bijection(a, b)
    rec = {
        "label": label,
        "source": [A, i, i+n],
        "target": [B, j, j+n],
        "length": n,
        "literal_ciphertext_equal": a == b,
        "equality_signatures_equal": sig_a == sig_b,
        "partial_bijection_exists": bij,
        "distinct_source_labels": len(set(a)),
        "distinct_target_labels": len(set(b)),
        "mapping_size": len(mapping) if mapping else None,
        "signature": list(sig_a),
    }
    records.append(rec)
    print(f"{label:17s} {A}[{i}:{i+n}] ~ {B}[{j}:{j+n}]")
    print("  literal ciphertext equal:", rec["literal_ciphertext_equal"])
    print("  equality signatures equal:", rec["equality_signatures_equal"])
    print("  partial bijection exists: ", rec["partial_bijection_exists"])
    print("  distinct labels / map size:", rec["distinct_source_labels"],
          rec["distinct_target_labels"], rec["mapping_size"])
    print("  signature:", "".join(chr(65+x) if x < 26 else f"[{x}]" for x in sig_a))
    print()

assert all(not r["literal_ciphertext_equal"] for r in records)
assert all(r["equality_signatures_equal"] for r in records)
assert all(r["partial_bijection_exists"] for r in records)

print("SUMMARY")
print("registered tuples:", len(records))
print("literal ciphertext copies:", sum(r["literal_ciphertext_equal"] for r in records))
print("equality-isomorphic pairs:", sum(r["equality_signatures_equal"] for r in records))
print("partial-bijection pairs:", sum(r["partial_bijection_exists"] for r in records))
print("ciphertext-level conclusion: all seven are nonliteral equality-isomorphs;")
print("this script establishes no plaintext equality.")

out = {
    "status": "ciphertext observation / assumption audit; no plaintext recovered",
    "dataset": str(DATA),
    "coordinate_convention": "zero-based raw message positions including header at 0",
    "registered_assumptions": records,
    "summary": {
        "count": len(records),
        "literal_ciphertext_copies": sum(r["literal_ciphertext_equal"] for r in records),
        "equality_isomorphs": sum(r["equality_signatures_equal"] for r in records),
        "partial_bijections": sum(r["partial_bijection_exists"] for r in records),
    },
    "scope": (
        "The computation proves only ciphertext equality-pattern isomorphism. "
        "Repeated plaintext is a separate cipher-model assumption."
    ),
}
out_path = HERE.parent / "results" / "stage81_passage_ciphertext_audit.json"
out_path.write_text((json.dumps(out, indent=2) + "\n").replace("\n", "\r\n"), encoding="utf-8", newline="")
print("saved", out_path)
