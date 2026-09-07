"""Independent review of Dr0pflux's bounded cyclic-homophone certificates.

Fix the phase of the longest observed projection, infer forced period cells,
then complete only unobserved cells. No collaborator code is imported.
"""
from pathlib import Path
from itertools import product,combinations
import hashlib,json
ROOT=Path(__file__).resolve().parent

def compatible(projections,r):
    longest=max(projections,key=len,default='')
    for length in range(2,2*r+1):
        forced=[None]*length
        for i,bit in enumerate(longest):
            j=i%length
            if forced[j] is not None and forced[j]!=bit:break
            forced[j]=bit
        else:
            free=[i for i,v in enumerate(forced) if v is None]
            for fill in product('01',repeat=len(free)):
                word=forced.copy()
                for i,bit in zip(free,fill):word[i]=bit
                word=''.join(word)
                if not (1<=word.count('0')<=r and 1<=word.count('1')<=r):continue
                if all(p in word*((len(p)+length-1)//length+1) for p in projections):return True
    return False

def brute(projections,r):
    for length in range(2,2*r+1):
        for bits in product('01',repeat=length):
            if not (1<=bits.count('0')<=r and 1<=bits.count('1')<=r):continue
            if all(any(all(bit==bits[(phase+i)%length] for i,bit in enumerate(p)) for phase in range(length)) for p in projections):return True
    return False

def main():
    record=json.loads((ROOT/'peer_cycle_claims.json').read_text(encoding='utf-8'))
    data=(ROOT/'ciphertext.json').read_bytes();assert hashlib.sha256(data).hexdigest()==record['ciphertext_sha256']
    messages=[row[1:] for row in json.loads(data).values()]
    short=[''.join(bits) for n in range(4) for bits in product('01',repeat=n)]
    small_checks=0
    for r in [1,2,3]:
        for a,b in product(short,repeat=2):
            assert compatible([a,b],r)==brute([a,b],r);small_checks+=1
    out=dict(status='Independent confirmation of the cited contributor claims, not a decipherment.',
             original_author=record['author'],source_result_sha256=record['source_result_sha256'],
             small_exhaustive_algorithm_comparisons=small_checks,claims=[])
    allpairs=list(combinations(range(83),2));projections={}
    for a,b in allpairs:
        projections[a,b]=[''.join('0' if c==a else '1' for c in row if c==a or c==b) for row in messages]
    certificate_pairs=0
    for claim in record['claims']:
        r=claim['multiplicity'];edges={pair for pair in allpairs if compatible(projections[pair],r)}
        assert len(edges)==claim['compatible_pair_count']
        labels=claim['incompatible_labels'];assert len(set(labels))==len(labels)==claim['class_lower_bound']
        for a,b in combinations(labels,2):assert tuple(sorted((a,b))) not in edges;certificate_pairs+=1
        # Each control is an actual repeated word under independent phases.
        word='0'*r+'1'*r
        positive=[(word*12)[phase:phase+7*len(word)] for phase in range(len(word))]
        assert compatible(positive,r)
        assert not compatible(['0'*(r+1)+'1'+'0'*(r+1)+'1'],r)
        out['claims'].append(dict(multiplicity=r,compatible_pairs=len(edges),verified_class_lower_bound=len(labels)))
        print('Reviewed multiplicity',r,'bound',len(labels),flush=True)
    assert certificate_pairs==6199
    out['certificate_pair_checks']=certificate_pairs;out['all_pair_compatibility_checks']=len(allpairs)*len(record['claims'])
    out['scope']='Fixed class membership and cycle, per-label multiplicity bound, one advancement per occurrence, independent initial phases. No plaintext-equality assumptions.'
    (ROOT/'checked_peer_cycle_claims.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
