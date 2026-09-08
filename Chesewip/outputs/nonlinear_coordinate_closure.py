"""Coordinate dependency closure, allowing an unknown nonlinear codebook.

For Latin codebooks, any two input coordinates determine the third. For a
single function graph, only the specified pair-to-coordinate rule is assumed.
No coordinate values or plaintext guesses are supplied to closure.
"""
from pathlib import Path
import json,itertools,hashlib,time,random,argparse
ROOT=Path(__file__).resolve().parent

def routed_triples(messages,period,first,strip=False,reverse=False):
    triples=[]
    for raw in messages:
        seq=raw[int(strip):]
        if reverse:seq=seq[::-1]
        lo=0;length=first
        while lo<len(seq):
            block=seq[lo:lo+length];n=len(block)
            for i in range(n):
                row=[]
                for axis in range(3):
                    j,d=divmod(axis*n+i,3);row.append(3*block[j]+d)
                triples.append(tuple(row))
            lo+=n;length=period
    return triples

class UnionFind:
    def __init__(self):self.parent=list(range(375))
    def root(self,x):
        while self.parent[x]!=x:
            self.parent[x]=self.parent[self.parent[x]];x=self.parent[x]
        return x
    def merge(self,a,b):
        a=self.root(a);b=self.root(b)
        if a==b:return False
        self.parent[max(a,b)]=min(a,b);return True

def closure(triples,labels,axes=(0,1,2),assumptions=()):
    uf=UnionFind();proof=[]
    for a,b in assumptions:uf.merge(a,b)
    while True:
        changed=False;seen={}
        for i,row in enumerate(triples):
            for axis in axes:
                others=[j for j in range(3) if j!=axis]
                key=(axis,uf.root(row[others[0]]),uf.root(row[others[1]]))
                if key in seen:
                    j=seen[key]
                    # Old representatives may have merged since insertion;
                    # equal dictionary keys still supply valid equalities.
                    if uf.merge(row[axis],triples[j][axis]):
                        proof.append([j,i,axis]);changed=True
                else:seen[key]=i
        signatures={}
        for label in labels:
            key=tuple(uf.root(3*label+d) for d in range(3))
            if key in signatures:
                return dict(status='forced_output_collision',pair=[signatures[key],label],proof=proof),uf
            signatures[key]=label
        if not changed:
            return dict(status='closure_survives',proof=proof,coordinate_classes=len({uf.root(v) for row in triples for v in row})),uf

def main():
    started=time.monotonic();raw_bytes=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(raw_bytes).values())
    out=dict(status='Coordinate functional-dependency screen; no decipherment.',ciphertext_sha256=hashlib.sha256(raw_bytes).hexdigest(),cases=[])
    for strip in [False,True]:
        for reverse in [False,True]:
            labels=sorted(set(x for m in messages for x in m[int(strip):]))
            for period in range(2,max(map(len,messages))-int(strip)+1):
                triples=routed_triples(messages,period,period,strip,reverse)
                result,_=closure(triples,labels)
                result.update(strip_first=strip,reverse=reverse,period=period)
                out['cases'].append(result)
            print('View',strip,reverse,'collisions',sum(c['status']=='forced_output_collision' for c in out['cases']),'/',len(out['cases']),flush=True)
    out['seconds']=time.monotonic()-started
    (ROOT/'nonlinear_coordinate_closure.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
