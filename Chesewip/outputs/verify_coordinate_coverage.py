"""Independent coordinate-coverage proof and unknown-map control replay.

Imports no discovery code. Routes each INPUT coordinate back to its source and
checks pigeonhole witnesses by explicit enumeration of all 125 output triples.
"""
from pathlib import Path
from collections import Counter
import itertools,json,hashlib
ROOT=Path(__file__).resolve().parent
TRIPLES=list(itertools.product(range(5),repeat=3))

def interval(seq):
    masks={label:[0,0,0] for label in seq};n=len(seq)
    for axis in range(3):
        for pos in range(n):
            source,digit=divmod(axis*n+pos,3)
            masks[seq[source]][axis]|=1<<digit
    return masks

def capacities():
    out={}
    for chosen in range(1,256):
        allowed=[]
        for triple in TRIPLES:
            if any(chosen&(1<<mask) and all(triple[d]!=0 for d in range(3) if mask&(1<<d)) for mask in range(8)):
                allowed.append(triple)
        out[chosen]=len(allowed)
    return out

def decode(raw,mapping,period,strip,reverse):
    seq=raw[int(strip):]
    if reverse:seq=seq[::-1]
    out=[]
    for lo in range(0,len(seq),period):
        block=[TRIPLES[mapping[label]] for label in seq[lo:lo+period]];n=len(block)
        for i in range(n):
            out.append(tuple(block[(axis*n+i)//3][(axis*n+i)%3] for axis in range(3)))
    return out

def main():
    data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values())
    certificates=json.loads((ROOT/'coordinate_coverage_certificates.json').read_text(encoding='utf-8'))
    discovery=json.loads((ROOT/'unknown_map_prism.json').read_text(encoding='utf-8'))
    assert certificates['ciphertext_sha256']==discovery['ciphertext_sha256']==hashlib.sha256(data).hexdigest()
    expected=[[int(s),int(r),b,f] for s in [False,True] for r in [False,True]
              for b in range(2,max(len(x)-int(s) for x in messages)+1) for f in range(1,b+1)]
    assert [row[:4] for row in certificates['records']]==expected
    assert not certificates['incomplete_cases']
    cap=capacities();checked=0;margins=Counter();views=None;cache=[];lengths=[]
    for strip,reverse,period,first,*witnesses in certificates['records']:
        if views!=(strip,reverse):
            seqs=[raw[strip:][::-1] if reverse else raw[strip:] for raw in messages]
            cache=[{(lo,hi):interval(seq[lo:hi]) for lo in range(len(seq)) for hi in range(lo+1,len(seq)+1)} for seq in seqs]
            lengths=list(map(len,seqs));views=(strip,reverse)
        combined={}
        for blocks,n in zip(cache,lengths):
            ends=[0,min(first,n)]
            while ends[-1]<n:ends.append(min(n,ends[-1]+period))
            for lo,hi in zip(ends,ends[1:]):
                for label,axes in blocks[lo,hi].items():
                    dest=combined.setdefault(label,[0,0,0])
                    for axis in range(3):dest[axis]|=axes[axis]
        for axis,chosen in enumerate(witnesses):
            assert isinstance(chosen,int) and 1<=chosen<=255
            selected=[label for label,axes in combined.items() if chosen&(1<<axes[axis])]
            assert len(selected)>cap[chosen],(strip,reverse,period,first,axis)
            margins[len(selected)-cap[chosen]]+=1;checked+=1
    # Full-first-block prism results follow from these axis certificates.
    assert discovery['real']['configurations']==546
    for case in discovery['real']['cases']:
        assert case['minimum_prism_volume']==(100 if case['period']==1 else 125)
        mapping={int(k):v for k,v in case['output_label_to_coordinate_code'].items()}
        assert len(set(mapping.values()))==len(mapping)
        for raw in messages:
            decoded=decode(raw,mapping,case['period'],case['strip_first'],case['reverse'])
            assert all(all(d in case['axis_sets'][axis] for axis,d in enumerate(t)) for t in decoded)
    control_cases=0;control_symbols=0
    for c in discovery['controls']:
        inverse={label:code for code,label in enumerate(c['coordinate_code_to_output_label'])}
        for raw,plain in zip(c['ciphertext'],c['plaintext']):
            decoded=decode(raw,inverse,c['period'],c['strip_first'],c['reverse'])
            assert decoded==[TRIPLES[x] for x in plain];control_symbols+=len(plain)
        best=min(x['minimum_prism_volume'] for x in c['scan']['cases'])
        minimizers=[x for x in c['scan']['cases'] if x['minimum_prism_volume']==best]
        assert best==27 and len(minimizers)==1
        assert all(minimizers[0][k]==c[k] for k in ['period','strip_first','reverse'])
        for case in c['scan']['cases']:
            mapping={int(k):v for k,v in case['output_label_to_coordinate_code'].items()}
            assert len(set(mapping.values()))==len(mapping)
            assert all(0<=v<125 for v in mapping.values())
            assert len(case['axis_sets'][0])*len(case['axis_sets'][1])*len(case['axis_sets'][2])==case['minimum_prism_volume']
            for raw in c['ciphertext']:
                decoded=decode(raw,mapping,case['period'],case['strip_first'],case['reverse'])
                assert all(all(d in case['axis_sets'][axis] for axis,d in enumerate(t)) for t in decoded)
            control_cases+=1
    scattered=json.loads((ROOT/'scattered_coordinate_control.json').read_text(encoding='utf-8'))
    inverse={label:code for code,label in enumerate(scattered['coordinate_code_to_output_label'])}
    assert len(inverse)==125
    observed_inputs=set();observed_outputs=set();combined={}
    for raw,plain in zip(scattered['ciphertext'],scattered['plaintext']):
        assert decode(raw,inverse,7,False,False)==[TRIPLES[x] for x in plain]
        observed_inputs.update(plain);observed_outputs.update(raw)
        for lo in range(0,len(raw),7):
            for label,axes in interval(raw[lo:lo+7]).items():
                dest=combined.setdefault(label,[0,0,0])
                for axis in range(3):dest[axis]|=axes[axis]
    assert len(observed_inputs)==27 and len(observed_outputs)==125
    for axis,chosen in enumerate(scattered['axis_coverage_certificates']):
        assert sum(bool(chosen&(1<<v[axis])) for v in combined.values())>cap[chosen]
        assert {TRIPLES[x][axis] for x in observed_inputs}==set(range(5))
    out=dict(status='Verified all-axis coverage under the stated shared routing; no plaintext recovered.',
             configurations=len(expected),pigeonhole_certificates_checked=checked,
             minimum_certificate_margin=min(margins),standard_prism_cases_verified=546,
             control_mapping_witnesses_replayed=control_cases,planted_control_symbols_replayed=control_symbols,
             control_parameter_minimizers_checked=3,scattered_27_symbol_scope_counterexample_verified=True,
             scope='Independent exhaustive routing/certificate check for real ciphertext. Control mappings and planted encodings replayed; discovery control global optimality not independently exhaustive-searched.')
    (ROOT/'checked_coordinate_coverage.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
