"""Exact unknown output-label mapping with rectangular input coordinate sets.

No plaintext or language assumptions. Nonrectangular codebooks are not covered
by prism volume bounds. Global digit renaming quotients the subset enumeration.
"""
from pathlib import Path
from collections import Counter
import itertools,json,hashlib,random,time
ROOT=Path(__file__).resolve().parent

def shapes():
    # Each digit has one of eight memberships in the three input axis sets.
    # Sorted memberships quotient a common permutation of the five digits.
    result=[]
    for memberships in itertools.combinations_with_replacement(range(8),5):
        sets=[sum(1<<d for d,m in enumerate(memberships) if m&(1<<axis)) for axis in range(3)]
        volume=1
        for s in sets:volume*=s.bit_count()
        if volume:result.append((volume,tuple(sets)))
    return sorted(result)

def codes_for(sets,signature):
    domains=[]
    for mask in signature:
        domain=31
        for axis in range(3):
            if mask&(1<<axis):domain &= sets[axis]
        domains.append([d for d in range(5) if domain&(1<<d)])
    return sum(1<<(25*a+5*b+c) for a,b,c in itertools.product(*domains))

def routes(messages,period,strip=False,reverse=False):
    masks={}
    for raw in messages:
        seq=raw[int(strip):]
        if reverse:seq=seq[::-1]
        for lo in range(0,len(seq),period):
            block=seq[lo:lo+period];n=len(block)
            for j,label in enumerate(block):
                dest=masks.setdefault(label,[0,0,0])
                for digit in range(3):dest[digit] |= 1<<((3*j+digit)//n)
    return {label:tuple(v) for label,v in masks.items()}

def matching(domains):
    owners={}
    def visit(label,seen):
        mask=domains[label]
        while mask:
            low=mask&-mask;mask-=low;code=low.bit_length()-1
            if code in seen:continue
            seen.add(code)
            if code not in owners or visit(owners[code],seen):
                owners[code]=label;return True
        return False
    for label in sorted(domains,key=lambda x:domains[x].bit_count()):
        if not visit(label,set()):return None
    return {label:code for code,label in owners.items()}

def evaluate(signature,shape_list,domain_cache):
    groups=Counter(signature.values());rejections=Counter()
    for volume,sets in shape_list:
        domains={s:domain_cache[sets,s] for s in groups}
        if any(domains[s].bit_count()<count for s,count in groups.items()):
            rejections['identical_domain_capacity']+=1;continue
        union=0
        for mask in domains.values():union|=mask
        if union.bit_count()<len(signature):
            rejections['union_capacity']+=1;continue
        witness=matching({label:domains[s] for label,s in signature.items()})
        if witness is None:rejections['matching_failure']+=1;continue
        return dict(minimum_prism_volume=volume,axis_sets=[list(d for d in range(5) if s&(1<<d)) for s in sets],
                    output_label_to_coordinate_code=witness,rejected_shapes=dict(rejections))
    raise AssertionError('The full cube must admit all observed labels.')

def scan(messages,shape_list):
    signatures={};cases=[]
    for strip in [False,True]:
        for reverse in [False,True]:
            for period in range(1,max(len(m)-int(strip) for m in messages)+1):
                r=routes(messages,period,strip,reverse)
                key=tuple(sorted(r.items()))
                signatures[key]=r
                cases.append(dict(strip_first=strip,reverse=reverse,period=period,key=key))
    required={s for r in signatures.values() for s in r.values()}
    cache={(sets,s):codes_for(sets,s) for _,sets in shape_list for s in required}
    results={key:evaluate(r,shape_list,cache) for key,r in signatures.items()}
    for case in cases:case.update(results[case.pop('key')])
    return dict(configurations=len(cases),distinct_routing_tables=len(signatures),
                minimum_prism_volume=min(c['minimum_prism_volume'] for c in cases),cases=cases)

def control(seed,period,strip,reverse):
    rng=random.Random(seed);axes=[[0,1,2],[2,3,4],[0,1,4]]
    alphabet=[25*a+5*b+c for a,b,c in itertools.product(*axes)]
    permutation=list(range(125));rng.shuffle(permutation)
    plaintext=[];ciphertext=[]
    for length in [103,113,127]:
        plain=alphabet+[rng.choice(alphabet) for _ in range(length-27)];rng.shuffle(plain)
        enc=[]
        for lo in range(0,len(plain),period):
            block=plain[lo:lo+period]
            digits=[d for axis in range(3) for v in block for d in [(v//(25,5,1)[axis])%5]]
            enc.extend(permutation[25*digits[i]+5*digits[i+1]+digits[i+2]] for i in range(0,len(digits),3))
        if reverse:enc=enc[::-1]
        if strip:enc=[rng.randrange(125)]+enc
        plaintext.append(plain);ciphertext.append(enc)
    return dict(seed=seed,period=period,strip_first=strip,reverse=reverse,axis_sets=axes,
                coordinate_code_to_output_label=permutation,plaintext=plaintext,ciphertext=ciphertext)

def main():
    started=time.monotonic();data=(ROOT/'ciphertext.json').read_bytes();raw=json.loads(data)
    shape_list=shapes()
    out=dict(status='Exact rectangular-codebook family test, not a decipherment.',
        ciphertext_sha256=hashlib.sha256(data).hexdigest(),canonical_shapes=len(shape_list),
        model='Arbitrary shared injective output-symbol mapping to 125 coordinate triples; input triples lie in A x B x C; full first blocks, shared period, short final blocks.',
        real=scan(list(raw.values()),shape_list),controls=[])
    print('Real',out['real']['minimum_prism_volume'],Counter(c['minimum_prism_volume'] for c in out['real']['cases']),flush=True)
    for args in [(907410,7,False,False),(907411,11,True,False),(907412,13,True,True)]:
        c=control(*args);c['scan']=scan(c['ciphertext'],shape_list)
        planted=next(x for x in c['scan']['cases'] if all(x[k]==c[k] for k in ['period','strip_first','reverse']))
        assert planted['minimum_prism_volume']<=27
        out['controls'].append(c)
        print('Control',c['seed'],'minimum',c['scan']['minimum_prism_volume'],'planted',planted['minimum_prism_volume'],flush=True)
    out['seconds']=time.monotonic()-started
    (ROOT/'unknown_map_prism.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
