"""Positive controls and short, exact conditional exclusion certificates."""
from pathlib import Path
import json, random
from progressive_reduction import deswap, graph_certificate
from reduced_smt import encrypt
ROOT=Path(__file__).resolve().parent

def map_conflicts(messages,top):
    b=[deswap(m,top,83) for m in messages]
    # Shared internal transitions: E4[52:63], W4[54:65], E5[53:64].
    table=list(zip(b[6][52:63],b[7][54:65],b[8][53:64]))
    arrows={};conflicts=[]
    for k,(east4,west4,east5) in enumerate(table):
        for u,v,kind in [(west4,east5,'W4 to E5'),(east5,east4,'E5 to E4')]:
            witness=dict(source=u,target=v,relative_position=k,kind=kind)
            if u in arrows and arrows[u]['target']!=v:
                conflicts.append([arrows[u],witness])
            arrows[u]=witness
    return conflicts

def main():
    rng=random.Random(20260908)
    eq=[(0,52,1,54,11),(0,52,2,53,11)]
    for trial in range(100):
        n=83;top=rng.randrange(n);bottom=[i for i in range(n) if i!=top]
        shuffled=bottom[:];rng.shuffle(shuffled);q=list(range(n))
        for i,j in zip(bottom,shuffled):q[i]=j
        alphabet=rng.sample(bottom,27)
        phrase=[rng.choice(alphabet) for _ in range(11)]
        pts=[[rng.choice(alphabet) for _ in range(120)] for _ in range(3)]
        for pt,start in zip(pts,[52,54,53]):pt[start:start+11]=phrase
        cts=[encrypt(pt,q,top) for pt in pts]
        assert not graph_certificate(cts,n,top,eq)['contradiction']
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    certificates=[]
    for top in range(83):
        conflicts=map_conflicts(messages,top)
        assert conflicts,top
        certificates.append(dict(top=top,conflict=conflicts[0]))
    result=dict(positive_controls_passed=100,
                conclusion='Conditional exclusion of common-initial-deck top-swap followed by arbitrary top-fixing permutation.',
                assumptions='The 11 internal plaintext transitions at E4[52:63], W4[54:65], E5[53:64] are identical. Indices zero-based, ends excluded.',
                certificates=certificates)
    (ROOT/'reduction_certificates.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('100 repeated-phrase positive controls passed; all 83 initial-top cases have an exact contradiction certificate.')

if __name__=='__main__':main()
