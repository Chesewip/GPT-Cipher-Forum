"""Exhaustive base-5 coordinate fractionation with short boundary blocks.

Alphabet-support test, no plaintext passages or language model. All authored
outputs retain the canonical corpus and explicitly bounded reading conventions.
"""
from pathlib import Path
from collections import Counter
import itertools,json,hashlib,random,time
ROOT=Path(__file__).resolve().parent
ORDERS=list(itertools.permutations(range(3)))

def digits(c):return (c//25,(c//5)%5,c%5)
def code(v):return 25*v[0]+5*v[1]+v[2]

def blocks(n,period,first):
    start=0;length=first
    while start<n:
        end=min(n,start+length)
        yield start,end
        start=end;length=period

def decode(seq,period,first,order):
    out=[]
    for start,end in blocks(len(seq),period,first):
        flat=[digits(c)[i] for c in seq[start:end] for i in order]
        n=end-start
        out.extend(25*flat[i]+5*flat[n+i]+flat[2*n+i] for i in range(n))
    return out

def encrypt(seq,period,first,order):
    out=[]
    for start,end in blocks(len(seq),period,first):
        plain=[digits(c) for c in seq[start:end]]
        flat=[v[i] for i in range(3) for v in plain]
        for i in range(0,len(flat),3):
            v=[0,0,0]
            for j in range(3):v[order[j]]=flat[i+j]
            out.append(code(v))
    return out

def scan_view(seq,order):
    n=len(seq);flat=[digits(c)[i] for c in seq for i in order]
    # Cache each decoded interval's symbol set, represented as a 125-bit mask.
    masks={}
    for start in range(n):
        for length in range(1,n-start+1):
            s=3*start;mask=0
            for i in range(length):
                mask|=1<<(25*flat[s+i]+5*flat[s+length+i]+flat[s+2*length+i])
            masks[start,length]=mask
    histogram=Counter();best=126;witnesses=[];period_bounds=[]
    for period in range(1,n+1):
        pbest=126;pfirst=None
        for first in range(1,period+1):
            union=0
            for start,end in blocks(n,period,first):union|=masks[start,end-start]
            support=union.bit_count();histogram[support]+=1
            if support<pbest:pbest=support;pfirst=first
            if support<best:best=support;witnesses=[]
            if support==best and len(witnesses)<24:witnesses.append([period,first])
        period_bounds.append([pbest,pfirst])
    period,first=witnesses[0]
    decoded=decode(seq,period,first,order)
    assert len(set(decoded))==best
    return dict(symbols=n,configurations=n*(n+1)//2,minimum_support=best,
                first_minimizers=witnesses,minimizer_list_capped_at=24,
                first_witness_decoded=decoded,per_period_minimum_and_first_block=period_bounds,
                support_histogram=dict(sorted(histogram.items())))

def scan_message(raw):
    results=[]
    for strip in [False,True]:
        for reverse in [False,True]:
            seq=raw[int(strip):]
            if reverse:seq=seq[::-1]
            for order in ORDERS:
                result=scan_view(seq,order)
                result.update(strip_first=strip,reverse=reverse,coordinate_order=order)
                results.append(result)
    return dict(raw_symbols=len(raw),minimum_support=min(r['minimum_support'] for r in results),
                configurations=sum(r['configurations'] for r in results),views=results)

def standard_shared(messages):
    cases=[]
    for strip in [False,True]:
        for reverse in [False,True]:
            seqs=[m[int(strip):][::-1] if reverse else m[int(strip):] for m in messages]
            for order in ORDERS:
                sizes=[]
                for period in range(1,max(map(len,seqs))+1):
                    symbols=set()
                    for seq in seqs:symbols.update(decode(seq,period,period,order))
                    sizes.append(len(symbols))
                cases.append(dict(strip_first=strip,reverse=reverse,coordinate_order=order,
                                  support_by_period=sizes,minimum_support=min(sizes)))
    return cases

def control(seed,length,period,first,order,strip,reverse):
    rng=random.Random(seed);alphabet=rng.sample(range(125),27)
    plaintext=alphabet+[rng.choice(alphabet) for _ in range(length-27)];rng.shuffle(plaintext)
    ciphertext=encrypt(plaintext,period,first,order)
    assert decode(ciphertext,period,first,order)==plaintext
    raw=ciphertext[::-1] if reverse else ciphertext
    if strip:raw=[rng.randrange(125)]+raw
    result=scan_message(raw)
    assert result['minimum_support']<=27
    correct=next(r for r in result['views'] if r['strip_first']==strip and r['reverse']==reverse and tuple(r['coordinate_order'])==order)
    assert correct['per_period_minimum_and_first_block'][period-1][0]<=27
    # Verify global direction renumbering changes recovered labels bijectively,
    # preserving equality/support for every one of the 120 possible numberings.
    renumberings=0
    for pi in itertools.permutations(range(5)):
        changed=[code(tuple(pi[d] for d in digits(c))) for c in ciphertext]
        expected=[code(tuple(pi[d] for d in digits(c))) for c in plaintext]
        assert decode(changed,period,first,order)==expected;renumberings+=1
    return dict(seed=seed,raw_ciphertext=raw,planted_plaintext=plaintext,planted_alphabet=alphabet,
                period=period,first_block=first,coordinate_order=order,strip_first=strip,reverse=reverse,
                unknown_parameter_scan=result,direction_renumberings_checked=renumberings)

def main():
    start=time.monotonic();path=ROOT/'ciphertext.json';raw=json.loads(path.read_text(encoding='utf-8'))
    out=dict(status='Finite-family support test; cipher remains unsolved.',
        corpus_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),message_order=list(raw),
        model='Raw base-5 coordinate Trifid-style fractionation; no keyed output-symbol substitution.',
        boundary_model='First block length 1..period, then full periods and an unpadded short final block. Periods above message length add no new partitions.',
        views='First raw symbol retained or omitted; forward or reversed body; all six within-trigram coordinate orders. Choices may differ between messages for the relaxed bound.',
        messages=[],controls=[])
    target=ROOT/'fractionation_boundary_screen.json'
    def save():target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    for name,seq in raw.items():
        r=scan_message(seq);r['name']=name;out['messages'].append(r);save()
        print(name,'minimum alphabet',r['minimum_support'],'configurations',r['configurations'],flush=True)
    out['independent_message_support_lower_bound']=max(r['minimum_support'] for r in out['messages'])
    out['standard_shared_cases']=standard_shared(list(raw.values()));save()
    for args in [(907400,103,7,7,(0,1,2),False,False),
                 (907401,113,11,3,(2,0,1),True,False),
                 (907402,127,13,5,(1,2,0),True,True)]:
        out['controls'].append(control(*args));save()
        print('Control',args[0],'minimum',out['controls'][-1]['unknown_parameter_scan']['minimum_support'],flush=True)
    out['seconds']=time.monotonic()-start;save()

if __name__=='__main__':main()
