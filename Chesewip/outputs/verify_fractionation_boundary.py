"""Independent critical-message exhaustive check and fractionation witnesses.

Uses direct coordinate addressing and frozenset unions. Does not import the
fractionation discovery script or use its bit masks/flattened-stream cache.
"""
from pathlib import Path
from collections import Counter
import hashlib,itertools,json
ROOT=Path(__file__).resolve().parent

def triple(c):return c//25,(c%25)//5,c%5

def block_decode(seq,order):
    n=len(seq);triples=[triple(c) for c in seq];out=[]
    for i in range(n):
        coords=[]
        for axis in range(3):
            source=axis*n+i
            coords.append(triples[source//3][order[source%3]])
        out.append(coords[0]*25+coords[1]*5+coords[2])
    return out

def decode(seq,period,first,order):
    out=block_decode(seq[:first],order);cursor=min(first,len(seq))
    while cursor<len(seq):
        out.extend(block_decode(seq[cursor:cursor+period],order));cursor+=period
    return out

def verify_view(seq,view):
    n=len(seq);order=view['coordinate_order'];cache={}
    for lo in range(n):
        for hi in range(lo+1,n+1):cache[lo,hi]=frozenset(block_decode(seq[lo:hi],order))
    hist=Counter();bounds=[]
    for period in range(1,n+1):
        supports=[]
        for first in range(1,period+1):
            used=set(cache[0,first]);cursor=first
            while cursor<n:
                used.update(cache[cursor,min(n,cursor+period)]);cursor+=period
            supports.append(len(used));hist[len(used)]+=1
        bounds.append([min(supports),supports.index(min(supports))+1])
    assert bounds==view['per_period_minimum_and_first_block']
    assert dict(hist)=={int(k):v for k,v in view['support_histogram'].items()}
    assert min(hist)==view['minimum_support']
    return sum(hist.values())

def main():
    raw_bytes=(ROOT/'ciphertext.json').read_bytes();raw=json.loads(raw_bytes)
    result=json.loads((ROOT/'fractionation_boundary_screen.json').read_text(encoding='utf-8'))
    assert result['corpus_sha256']==hashlib.sha256(raw_bytes).hexdigest()
    assert result['message_order']==list(raw)
    # A single message proves the relaxed whole-corpus alphabet bound.
    decisive=max(result['messages'],key=lambda m:m['minimum_support'])
    assert decisive['name']=='East 3'
    checked=0;witnesses=0
    for message in result['messages']:
        assert len(message['views'])==24
        assert set((v['strip_first'],v['reverse'],tuple(v['coordinate_order'])) for v in message['views'])==set(itertools.product([False,True],[False,True],itertools.permutations(range(3))))
        for view in message['views']:
            seq=raw[message['name']][int(view['strip_first']):]
            if view['reverse']:seq=seq[::-1]
            p,f=view['first_minimizers'][0]
            decoded=decode(seq,p,f,view['coordinate_order'])
            assert decoded==view['first_witness_decoded']
            assert len(set(decoded))==view['minimum_support'];witnesses+=1
            if message is decisive:checked+=verify_view(seq,view)
    assert checked==225228
    assert decisive['minimum_support']==result['independent_message_support_lower_bound']==64
    standard=0
    for case in result['standard_shared_cases']:
        sizes=[]
        for period in range(1,len(case['support_by_period'])+1):
            used=set()
            for row in raw.values():
                seq=row[int(case['strip_first']):]
                if case['reverse']:seq=seq[::-1]
                used.update(decode(seq,period,period,case['coordinate_order']))
            sizes.append(len(used));standard+=1
        assert sizes==case['support_by_period']
    assert min(min(c['support_by_period']) for c in result['standard_shared_cases'])==83
    # Re-encode controls using an independently constructed coordinate routing.
    renumberings=0
    for c in result['controls']:
        plain=c['planted_plaintext'];p=c['period'];first=c['first_block'];order=c['coordinate_order']
        enc=[];lo=0;length=first
        while lo<len(plain):
            block=plain[lo:lo+length];n=len(block);encoded_digits=[[None]*3 for _ in block]
            for i,v in enumerate(block):
                for axis,d in enumerate(triple(v)):
                    target=axis*n+i;encoded_digits[target//3][order[target%3]]=d
            enc.extend(25*v[0]+5*v[1]+v[2] for v in encoded_digits);lo+=n;length=p
        observed=c['raw_ciphertext'][int(c['strip_first']):]
        if c['reverse']:observed=observed[::-1]
        assert observed==enc and decode(enc,p,first,order)==plain
        assert len(set(plain))==27
        for pi in itertools.permutations(range(5)):
            changed=[25*pi[triple(v)[0]]+5*pi[triple(v)[1]]+pi[triple(v)[2]] for v in enc]
            expected=[25*pi[triple(v)[0]]+5*pi[triple(v)[1]]+pi[triple(v)[2]] for v in plain]
            assert decode(changed,p,first,order)==expected;renumberings+=1
        assert c['unknown_parameter_scan']['minimum_support']==27
        for v in c['unknown_parameter_scan']['views']:
            seq=c['raw_ciphertext'][int(v['strip_first']):]
            if v['reverse']:seq=seq[::-1]
            period,first=v['first_minimizers'][0]
            assert decode(seq,period,first,v['coordinate_order'])==v['first_witness_decoded']
            assert len(set(v['first_witness_decoded']))==v['minimum_support']
    out=dict(status='Verified ciphertext-only bound; no plaintext recovered.',
             decisive_message='East 3',independent_message_support_lower_bound=64,
             decisive_message_configurations_reenumerated=checked,
             all_real_view_witnesses_redecoded=witnesses,standard_shared_configurations_reenumerated=standard,
             standard_shared_minimum_support=83,generated_control_encodings_replayed=len(result['controls']),
             generated_direction_renumberings_verified=renumberings,
             scope='All critical-message configurations and standard shared configurations independently reenumerated; other message/control minima have witness checks, not a second exhaustive optimality search.')
    (ROOT/'checked_fractionation_boundary.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
