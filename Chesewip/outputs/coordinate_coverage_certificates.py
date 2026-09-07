"""Pigeonhole certificates for an arbitrary output substitution before routing.

Tests omission of one digit in one input axis; does NOT bound plaintext support.
The first block may be short, independently of the final block, but B and R are
shared across messages. Certificate witnesses are sets of routing-mask types.
"""
from pathlib import Path
from collections import Counter
import itertools,json,hashlib,time
ROOT=Path(__file__).resolve().parent

def candidate_witnesses():
    result=[]
    domains=[]
    for constrained in range(8):
        domains.append({25*a+5*b+c for a,b,c in itertools.product(range(5),repeat=3)
                        if all(d!=0 for j,d in enumerate((a,b,c)) if constrained&(1<<j))})
    for selected in range(1,256):
        # Include all types with narrower domains at no increase in capacity.
        if any(selected&(1<<m) and not selected&(1<<n) for m in range(8) for n in range(8) if m&n==m):continue
        allowed=set().union(*(domains[m] for m in range(8) if selected&(1<<m)))
        result.append((selected,len(allowed)))
    return sorted(result,key=lambda x:x[1])

def interval_routes(seq,lo,hi):
    n=hi-lo;out={}
    for j,label in enumerate(seq[lo:hi]):
        masks=out.setdefault(label,[0,0,0])
        for digit in range(3):masks[digit]|=1<<((3*j+digit)//n)
    return out

def case_routes(caches,lengths,period,first):
    out={}
    for cache,n in zip(caches,lengths):
        lo=0;size=first
        while lo<n:
            hi=min(n,lo+size)
            for label,v in cache[lo,hi].items():
                dest=out.setdefault(label,[0,0,0])
                for digit in range(3):dest[digit]|=v[digit]
            lo=hi;size=period
    return out

def certify(routes,candidates):
    result=[]
    for axis in range(3):
        counts=Counter(sum(1<<digit for digit,v in enumerate(masks) if v&(1<<axis)) for masks in routes.values())
        witness=next((selected for selected,capacity in candidates
                      if sum(count for mask,count in counts.items() if selected&(1<<mask))>capacity),None)
        result.append(witness)
    return result

def main():
    started=time.monotonic();raw_bytes=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(raw_bytes).values())
    candidates=candidate_witnesses();records=[];failures=[];stats=Counter()
    for strip in [False,True]:
        for reverse in [False,True]:
            seqs=[raw[int(strip):][::-1] if reverse else raw[int(strip):] for raw in messages]
            caches=[{(lo,hi):interval_routes(seq,lo,hi) for lo in range(len(seq)) for hi in range(lo+1,len(seq)+1)} for seq in seqs]
            lengths=list(map(len,seqs))
            for period in range(2,max(lengths)+1):
                for first in range(1,period+1):
                    cert=certify(case_routes(caches,lengths,period,first),candidates)
                    row=[int(strip),int(reverse),period,first]+cert
                    if any(x is None for x in cert):failures.append(row)
                    records.append(row)
                    stats.update(x for x in cert if x is not None)
            print('View',strip,reverse,'cases',len(records),'cases missing an axis certificate',len(failures),flush=True)
    out=dict(status='Coordinate-coverage certificates, not a plaintext alphabet-size bound.',
             ciphertext_sha256=hashlib.sha256(raw_bytes).hexdigest(),
             model='Shared injective output-label mapping to base-5 triples; common period B >= 2 and first-block length R in 1..B; short final blocks; common first-symbol omission and body reversal.',
             candidate_type_sets=[list(x) for x in candidates],
             record_columns=['strip_first','reverse','period','first_block','axis0_type_set','axis1_type_set','axis2_type_set'],
             records=records,incomplete_cases=failures,certificate_type_counts=dict(stats),seconds=time.monotonic()-started)
    (ROOT/'coordinate_coverage_certificates.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
