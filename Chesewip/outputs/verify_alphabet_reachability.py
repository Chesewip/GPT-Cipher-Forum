"""Brute small-word checks and direct Hall-certificate verification."""
from pathlib import Path
import json,itertools
from alphabet_reachability import domains,matching,test
from clocked_three_cycle_scan import encrypt_physical
ROOT=Path(__file__).resolve().parent

def main():
    checks=0
    for b in range(6):
        for stride in [1,5]:
            alphabet=[1+k*stride%6 for k in range(3)]
            _,layers=domains([[0]*4],7,alphabet,b)
            for length in range(1,5):
                reached={encrypt_physical(word,list(range(7)),1,b)[-1] for word in itertools.product(alphabet,repeat=length)}
                assert layers[length-1]==sum(1<<c for c in reached);checks+=1
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    data=json.loads((ROOT/'alphabet_reachability_27_all_strides.json').read_text());proofs=0
    for r in data['results']:
        if r['status']!='excluded':continue
        alphabet=[1+k*r['alphabet_stride']%82 for k in range(r['alphabet_bound'])]
        allowed,_=domains(messages,83,alphabet,r['shuffle_offset'])
        union=0
        for label in r['labels']:union|=allowed[label]
        assert union.bit_count()<len(r['labels'])
        assert set(r['possible_initial_positions'])=={p for p in range(83) if union>>p&1}
        proofs+=1
    thresholds=[]
    for b in [0,1,41,81]:
        low=1;high=82
        while low<high:
            middle=(low+high)//2
            if test(messages,83,middle,b)['status']=='excluded':low=middle+1
            else:high=middle
        # Monotone domain inclusion makes bisection valid; verify the boundary.
        assert test(messages,83,low,b)['status']=='relaxation_survives'
        if low>1:assert test(messages,83,low-1,b)['status']=='excluded'
        thresholds.append({'shuffle_offset':b,'minimum_contiguous_alphabet_not_excluded_by_this_relaxation':low})
    out={'passed':True,'small_exhaustive_word_checks':checks,'hall_certificates_rechecked':proofs,
         'contiguous_alphabet_thresholds':thresholds}
    (ROOT/'checked_alphabet_reachability.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(out)

if __name__=='__main__':main()
