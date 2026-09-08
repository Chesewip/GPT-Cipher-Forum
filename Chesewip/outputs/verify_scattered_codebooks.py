"""Independent replay of heuristic witnesses and F5 exclusion certificates.

Standard library only. No discovery code is imported; no optimization repeated.
"""
from pathlib import Path
from collections import Counter
import itertools,json,math,hashlib,base64,zlib
ROOT=Path(__file__).resolve().parent
TRIPLES=list(itertools.product(range(5),repeat=3))

def body(raw,strip,reverse):
    seq=raw[int(strip):]
    return seq[::-1] if reverse else seq

def decrypt(messages,key,period,first,strip,reverse):
    output=[]
    for raw in messages:
        seq=body(raw,strip,reverse);lo=0;length=first;plain=[]
        while lo<len(seq):
            block=seq[lo:lo+length];n=len(block)
            stream=[digit for label in block for digit in TRIPLES[key[label]]]
            plain.extend(25*stream[i]+5*stream[n+i]+stream[2*n+i] for i in range(n))
            lo+=n;length=period
        output.append(plain)
    return output

def encrypt(messages,key,period,first):
    inverse={code:label for label,code in enumerate(key)};output=[]
    for plain in messages:
        lo=0;length=first;cipher=[]
        while lo<len(plain):
            block=plain[lo:lo+length];n=len(block)
            stream=[TRIPLES[code][axis] for axis in range(3) for code in block]
            cipher.extend(inverse[25*stream[j]+5*stream[j+1]+stream[j+2]] for j in range(0,len(stream),3))
            lo+=n;length=period
        output.append(cipher)
    return output

def verify_run(messages,r):
    assert sorted(r['initial_key'])==sorted(r['best_key'])==list(range(125))
    decoded=decrypt(messages,r['best_key'],r['period'],r['first_block'],r['strip_first'],r['reverse'])
    flat=sum(decoded,[]);assert flat==r['decoded']
    counts=Counter(flat);assert len(counts)==r['best_support']
    energy=sum(1-.1*n*math.log(n) for n in counts.values())
    assert abs(energy-r['best_energy'])<1e-7
    assert encrypt(decoded,r['best_key'],r['period'],r['first_block'])==[body(m,r['strip_first'],r['reverse']) for m in messages]
    assert all(b[1]<=a[1] for a,b in zip(r['trace'],r['trace'][1:]))
    return len(flat)

def rows_from_output(messages,period,strip,reverse,a,b):
    rows=[];coefficients=(a,b,1)
    for raw in messages:
        seq=body(raw,strip,reverse)
        for lo in range(0,len(seq),period):
            block=seq[lo:lo+period];n=len(block);block_rows=[{375:4} for _ in block]
            for j,label in enumerate(block):
                for digit in range(3):
                    axis,pos=divmod(3*j+digit,n);v=3*label+digit
                    block_rows[pos][v]=(block_rows[pos].get(v,0)+coefficients[axis])%5
            rows.extend(block_rows)
    return rows

def check_certificate(rows,case):
    cert=case['certificate'];assert cert is not None
    if 'coordinate_difference_weights' in cert:
        kind='coordinate_collision';weights=cert['coordinate_difference_weights']
    else:
        kind=cert['kind'];raw=zlib.decompress(base64.b64decode(cert['weights_base64_zlib'],validate=True))
        n=case['equations_used'];assert len(raw)==n*cert['weight_rows']
        assert all(x<5 for x in raw)
        weights=[list(raw[i:i+n]) for i in range(0,len(raw),n)]
    if kind=='coordinate_collision':
        assert cert['pair']==[0,1]
        targets=[{d:1,3+d:4} for d in range(3)]
    else:
        assert kind=='six_labels_on_five_point_line'
        b=case['b'];assert cert['line_b']==b
        targets=[]
        for label in range(1,6):
            targets.extend([{3*label+1:1,1:4},{3*label:b,3*label+2:1,0:(-b)%5,2:4}])
        # The two shared quantities y and b*x+z permit exactly five triples.
        assert all(sum(y==u and (b*x+z)%5==v for x,y,z in TRIPLES)==5 for u,v in itertools.product(range(5),repeat=2))
    assert len(weights)==len(targets)
    if 'targets' in cert:
        assert [{int(k):v%5 for k,v in t.items()} for t in cert['targets']]==targets
    for vector,target in zip(weights,targets):
        assert len(vector)==case['equations_used'] and len(vector)<=len(rows)
        actual=Counter()
        for coefficient,row in zip(vector,rows):
            if coefficient:
                for variable,value in row.items():actual[variable]+=coefficient*value
        actual={v:x%5 for v,x in actual.items() if x%5}
        assert actual==target
    return kind,len(weights)

def main():
    raw_bytes=(ROOT/'ciphertext.json').read_bytes();eyes=list(json.loads(raw_bytes).values())
    controls=json.loads((ROOT/'scattered_map_recovery_controls.json').read_text(encoding='utf-8'))
    real=json.loads((ROOT/'scattered_map_recovery_eyes.json').read_text(encoding='utf-8'))
    assert real['ciphertext_sha256']==hashlib.sha256(raw_bytes).hexdigest()
    replays=0;symbols=0;repairs=Counter();blind=[]
    for c in controls['controls']:
        key=c['true_output_label_to_code'];assert sorted(key)==list(range(125))
        assert decrypt(c['ciphertext'],key,7,7,False,False)==c['plaintext']
        assert len(set(sum(c['plaintext'],[])))==27
        for r in c['runs']:
            symbols+=verify_run(c['ciphertext'],r);replays+=1
            if r['initialization']=='blind random permutation':blind.append(r['best_support'])
            else:
                assert r['initial_wrong_key_entries']==sum(a!=b for a,b in zip(r['initial_key'],key))
                assert r['final_wrong_key_entries']==sum(a!=b for a,b in zip(r['best_key'],key))
                if r['best_key']==key:repairs[r['initial_perturbation_swaps']]+=1
    for r in real['runs']:symbols+=verify_run(eyes,r);replays+=1
    old_control=json.loads((ROOT/'scattered_coordinate_control.json').read_text(encoding='utf-8'))
    for filename in ['scattered_map_adjacent_calibration.json','scattered_map_calibrate.json']:
        old=json.loads((ROOT/filename).read_text(encoding='utf-8'))
        assert old['control_sha256']==hashlib.sha256((ROOT/'scattered_coordinate_control.json').read_bytes()).hexdigest()
        for r in old['runs']:symbols+=verify_run(old_control['ciphertext'],r);replays+=1
    symbols+=verify_run(old_control['ciphertext'],json.loads((ROOT/'scattered_map_cold_pilot.json').read_text(encoding='utf-8')));replays+=1
    result=json.loads((ROOT/'affine_plane_codebook.json').read_text(encoding='utf-8'))
    assert result['ciphertext_sha256']==hashlib.sha256(raw_bytes).hexdigest()
    expected=[(s,r,p,a,b) for s in [False,True] for r in [False,True]
              for p in range(2,min(result['max_period'],max(map(len,eyes))-int(s))+1)
              for a,b in itertools.product(range(1,5),repeat=2)]
    assert [(c['strip_first'],c['reverse'],c['period'],c['a'],c['b']) for c in result['cases']]==expected
    kinds=Counter();identities=0
    for i,case in enumerate(result['cases']):
        rows=rows_from_output(eyes,case['period'],case['strip_first'],case['reverse'],case['a'],case['b'])
        kind,n=check_certificate(rows,case);kinds[kind]+=1;identities+=n
        if (i+1)%1024==0:print('Verified affine cases',i+1,flush=True)
    for c in result['controls']:
        key=c['true_label_to_code'];assert sorted(key)==list(range(125))
        assert decrypt(c['ciphertext'],key,c['period'],c['period'],False,False)==c['plaintext']
        assert len(set(sum(c['plaintext'],[])))==25
        assert all((c['a']*TRIPLES[v][0]+c['b']*TRIPLES[v][1]+TRIPLES[v][2])%5==c['rhs'] for row in c['plaintext'] for v in row)
    # Retain and verify the earlier partial screen, including its unresolved cases.
    pilot=json.loads((ROOT/'affine_plane_codebook_pilot.json').read_text(encoding='utf-8'));pilot_checked=0
    for case in pilot['cases']:
        if case['certificate'] is None:continue
        rows=rows_from_output(eyes,case['period'],case['strip_first'],False,case['a'],case['b'])
        check_certificate(rows,case);pilot_checked+=1
    out=dict(status='Verified finite-family certificates and heuristic witnesses; no decipherment.',
        heuristic_key_witnesses_replayed=replays,heuristic_symbols_reencrypted=symbols,
        exact_warm_repairs_by_initial_swap_count=dict(repairs),blind_control_support_range=[min(blind),max(blind)],
        best_eye_witness_support=min(r['best_support'] for r in real['runs']),
        affine_plane_configurations=len(expected),affine_certificate_kinds=dict(kinds),
        weighted_equation_identities_checked=identities,affine_generated_controls_verified=len(result['controls']),
        earlier_partial_affine_certificates_verified=pilot_checked,
        scope='Replays and equation identities are verified, not optimality of heuristic minima. Affine exclusions require all three nonzero coefficients and the stated shared full-first-block schedule.')
    (ROOT/'checked_scattered_codebooks.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
