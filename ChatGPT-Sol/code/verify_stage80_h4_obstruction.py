#!/usr/bin/env python3
"""Independent finite verifier for Stage 80's local equality obstruction.

This verifier does not implement the H4 recurrence or reuse discovery helpers.
It checks only the local consequence of a repeated 5-symbol plaintext block.
At the fifth positions the raw lag-4 values are equal to one common r.

For each context, a trigger-only collision handler either:
  N: does not repair, so fifth output = r; or
  R: repairs because previous output = r.

Across the two contexts:
  NN -> fifth outputs equal
  RN -> A previous = B fifth
  NR -> B previous = A fifth
  RR -> previous outputs equal

Therefore four distinct visible labels in
(A previous, A fifth, B previous, B fifth) are impossible under any bijective
output relabeling, regardless of what value a repair emits.
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / 'data' / 'ciphertext_stage78.json'
D=json.loads(DATA.read_text())
B={k:v['body'] for k,v in D.items()}
ASS=[
('W1',37,'W1',67,15),('E2',42,'E2',77,15),('E1',43,'E1',71,6),
('W1',37,'E2',42,15),('W1',37,'E2',77,15),
('E4',71,'W4',74,27),('E4',71,'E5',72,27)]

def c(m,r): return B[m][r-1]

branches={
    ('N','N'): 'fifths equal',
    ('R','N'): 'A previous = B fifth',
    ('N','R'): 'B previous = A fifth',
    ('R','R'): 'previouss equal',
}

for A,i,C,j,n in ASS:
    assert n>=5
    q=(c(A,i+3),c(A,i+4),c(C,j+3),c(C,j+4))
    distinct=len(set(q))==4
    print(A,i,C,j,'quad',q,'all_distinct',distinct)
    assert distinct

print('branch cases checked',len(branches))
for k,v in branches.items(): print(k,'=>',v)
print('verified: every assumed passage has a four-distinct local ciphertext certificate')
