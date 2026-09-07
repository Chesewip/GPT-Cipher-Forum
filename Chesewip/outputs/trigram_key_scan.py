"""Starting decks suggested by base-5 digit and eye-direction conventions.

These are key-order hypotheses. The original trigram grouping is unchanged.
Test all direction renumberings in canonical digit order, plus every digit
order under rotations/reflections of the four compass directions.
"""
from pathlib import Path
import itertools,json,time,argparse
import numpy as np
from clocked_three_cycle_scan import scan,encrypt_physical
ROOT=Path(__file__).resolve().parent

def keys():
    digits={c:(c//25,(c//5)%5,c%5) for c in range(83)}
    configs=[(pi,(0,1,2),'direction_renumbering') for pi in itertools.permutations(range(5))]
    for sign in [-1,1]:
        for turn in range(4):
            pi=(0,)+tuple(1+(sign*(d-1)+turn)%4 for d in range(1,5))
            configs.extend((pi,order,'compass_symmetry_and_digit_order') for order in itertools.permutations(range(3)))
    found={}
    for pi,order,kind in configs:
        deck=tuple(sorted(range(83),key=lambda c:sum(pi[digits[c][order[k]]]*5**(2-k) for k in range(3))))
        found.setdefault(deck,{'direction_mapping':pi,'digit_order':order,'source_family':kind})
    return found

def main(control=False):
    start=time.time();candidates=keys();results=[]
    if control:
        # A convention whose key differs from ascending/reversed numerical order.
        key=list(candidates)[73];rng=np.random.default_rng(20261004)
        alphabet=rng.choice(np.arange(1,83),27,replace=False)
        pts=[rng.choice(alphabet,120).tolist() for _ in range(9)]
        messages=[encrypt_physical(p,key,17,9) for p in pts]
        result,support=scan(messages,np.array(key));assert support[(17-1)*82+9]==27
        out={'planted_key':list(key),'key_convention':candidates[key],
             'planted_neighbor_offset':17,'planted_shuffle_offset':9,
             'planted_alphabet_recovered':True,**result};name='trigram_key_control.json'
    else:
        messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
        for index,(key,convention) in enumerate(candidates.items()):
            result,_=scan(messages,np.array(key));result.update(key_index=index,key_convention=convention,initial_top=key[0])
            results.append(result)
            if index%20==0:print('keys checked',index+1,'of',len(candidates),'best alphabet',min(r['minimum_alphabet'] for r in results),flush=True)
        out={'initial_key_count':len(candidates),'total_configurations':sum(r['configurations'] for r in results),
             'minimum_alphabet':min(r['minimum_alphabet'] for r in results),'results':results,
             'scope':'Forward reading, first trigram included; only the recorded key conventions. Not arbitrary-key exclusion.'}
        name='trigram_key_scan_results.json'
    out['seconds']=time.time()-start
    (ROOT/name).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Completed',name,'seconds',out['seconds'])

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--control',action='store_true');args=ap.parse_args();main(args.control)
