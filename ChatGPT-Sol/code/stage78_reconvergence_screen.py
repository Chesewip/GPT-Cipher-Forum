#!/usr/bin/env python3
"""Stage 78: exact local reconvergence screen for H_L = PI(p_i+p_{i-L}).

Conditional assumption for E1/W1 body positions 0..48:
  * plaintexts are equal through 23;
  * plaintext difference delta_i is nonzero on one contiguous interval [24,b];
  * plaintexts rejoin exactly after b (delta_i=0 thereafter).

For H_L, ciphertext equality is equivalent to delta_i + delta_{i-L} = 0 mod83.
We search L=1..24 and b=24..48 exactly over F_83. This is a local structural
screen, not a plaintext claim.
"""
from pathlib import Path
import argparse,json
MOD=83

class DSU:
    # signed relation val[x] = sign * val[parent], sign in {+1,-1}
    def __init__(self,n): self.p=list(range(n)); self.s=[1]*n
    def find(self,x):
        if self.p[x]!=x:
            p=self.p[x]; r,sg=self.find(p); self.s[x]*=sg; self.p[x]=r
        return self.p[x],self.s[x]
    def union(self,a,b,rel):
        # val[a] = rel * val[b]
        ra,sa=self.find(a); rb,sb=self.find(b)
        if ra==rb: return sa==rel*sb
        self.p[ra]=rb; self.s[ra]=rel*sb*sa
        return True

def exact_solution(eq,L,b,start=24,end=48):
    idx={i:k for k,i in enumerate(range(start,b+1))}
    dsu=DSU(len(idx)); inequalities=[]
    for i in range(end+1):
        a=i if i in idx else None; j=i-L; bb=j if j in idx else None
        if eq[i]:
            if a is None and bb is None: continue
            if a is None or bb is None: return None
            if not dsu.union(idx[a],idx[bb],-1): return None
        else:
            if a is None and bb is None: return None
            if a is None or bb is None: continue
            inequalities.append((idx[a],idx[bb]))
    for a,bv in inequalities:
        ra,sa=dsu.find(a); rb,sb=dsu.find(bv)
        if ra==rb and sa==-sb: return None
    roots=sorted({dsu.find(k)[0] for k in range(len(idx))}); edges=[]
    for a,bv in inequalities:
        ra,sa=dsu.find(a); rb,sb=dsu.find(bv)
        if ra!=rb: edges.append((ra,rb,sa,sb))
    assign={}
    def bt(t):
        if t==len(roots): return True
        r=roots[t]
        for v in range(1,MOD):
            ok=True
            for ra,rb,sa,sb in edges:
                if r==ra and rb in assign and (sa*v+sb*assign[rb])%MOD==0: ok=False; break
                if r==rb and ra in assign and (sa*assign[ra]+sb*v)%MOD==0: ok=False; break
            if ok:
                assign[r]=v
                if bt(t+1): return True
                del assign[r]
        return False
    if not bt(0): return None
    ex={}
    for i,k in idx.items():
        r,sg=dsu.find(k); ex[i]=(sg*assign[r])%MOD
    # certificate check
    for i in range(end+1):
        y=(ex.get(i,0)+ex.get(i-L,0))%MOD
        assert (y==0)==eq[i],(L,b,i,y)
    return ex

def fmt_example(ex):
    if not ex:return '-'
    return ' '.join(f'{i}:{ex[i]}' for i in sorted(ex))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--ciphertext',default=str(Path(__file__).with_name('ciphertext_stage78.json')))
    args=ap.parse_args()
    data=json.loads(Path(args.ciphertext).read_text())
    a=data['E1']['body']; b=data['W1']['body']; n=min(len(a),len(b))
    eq=[a[i]==b[i] for i in range(n)]
    pref=0
    while pref<n and eq[pref]: pref+=1
    print('Stage78 E1/W1 local lag reconvergence screen')
    print('common body prefix',pref)
    print('positions 20..48 equality mask',''.join('=' if eq[i] else '!' for i in range(20,49)))
    # Raw H4 exact identity is valid for gap-4 pairs with i>=8: c_i=c_{i-4} iff p_i=p_{i-8}.
    hits=sum(1 for m in (v['body'] for v in data.values()) for i in range(8,len(m)) if m[i]==m[i-4])
    pairs=sum(max(0,len(v['body'])-8) for v in data.values())
    ratio=MOD*hits/pairs
    print('raw-H4 core-safe gap4 (i>=8): hits',hits,'pairs',pairs,'normalized ratio',round(ratio,6))
    print('=> raw H4 requires the corresponding plaintext lag8 repeat ratio to be',round(ratio,6))
    assert pref==24
    assert all(not eq[i] for i in range(24,28)) and all(eq[i] for i in range(28,32))
    assert all(not eq[i] for i in range(32,36)) and all(eq[i] for i in range(36,49))
    sols=[]
    for L in range(1,25):
        endpoints=[]
        for end in range(24,49):
            ex=exact_solution(eq,L,end)
            if ex is not None:endpoints.append(end)
        if endpoints: sols.append((L,endpoints))
    print('\nall exact (L, rejoin-endpoint b) solutions through ciphertext position 48:')
    for L,ends in sols: print('L',L,'b',ends)
    print('\ncompact solutions (plaintext rejoins before ciphertext position 36):')
    for L,ends in sols:
        for end in ends:
            if end<36:
                ex=exact_solution(eq,L,end)
                print('L',L,'b',end,'plaintext-difference support',end-24+1,'example',fmt_example(ex))
    print('\ninterpretation:')
    print('L=8 needs only delta[24..27] !=0; its delayed echo creates the second 4-symbol ciphertext difference block.')
    print('L=4 needs delta[24..27]=a,b,c,d and delta[28..31]=-a,-b,-c,-d before plaintext rejoins.')
    print('Therefore this E1/W1 event alone does not identify L=4; the global gap-spectrum evidence is needed to prefer it.')

if __name__=='__main__':main()
