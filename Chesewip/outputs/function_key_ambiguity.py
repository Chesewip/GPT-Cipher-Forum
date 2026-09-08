"""Find a compact known-table control ambiguity, not an Eye decipherment."""
from pathlib import Path
from collections import Counter,defaultdict
import json,itertools,hashlib
from scattered_map_search import dependencies,decoded_values
ROOT=Path(__file__).resolve().parent

def main():
    source_bytes=(ROOT/'one_coordinate_function_screen.json').read_bytes();source=json.loads(source_bytes)
    control=next(c for c in source['controls'] if c['seed']==908210)
    key=control['true_label_to_code'];axis=control['axis'];other=[d for d in range(3) if d!=axis]
    messages=control['ciphertext'];sources,dep=dependencies(messages,2,2)
    plain=decoded_values(key,sources);freq=Counter(sum(messages,[]));valid=[];best=None;tested=0
    for a,b in itertools.combinations(range(125),2):
        if a not in freq and b not in freq:continue
        tested+=1;positions={pos for label in [a,b] for d in range(3) for pos,_ in dep[3*label+d]};changed={}
        for pos in positions:
            point=[]
            for cell in sources[pos]:
                label,d=divmod(cell,3);code=key[b] if label==a else key[a] if label==b else key[label]
                point.append((code//[25,5,1][d])%5)
            if point[axis]!=control['table'][point[other[0]]][point[other[1]]]:break
            value=25*point[0]+5*point[1]+point[2]
            if value!=plain[pos]:changed[pos]=value
        else:
            if not changed:continue
            candidate=list(plain)
            for pos,value in changed.items():candidate[pos]=value
            images=defaultdict(set)
            for old,new in zip(plain,candidate):images[old].add(new)
            split=next((old for old,targets in images.items() if len(targets)>1),None)
            if split is None:continue
            record=[a,b,len(changed),freq[a],freq[b]];valid.append(record)
            score=(min(freq[a],freq[b]),len(changed),-a,-b)
            if best is None or score>best[0]:best=(score,a,b,candidate,changed,split)
    assert best is not None
    _,a,b,candidate,changed,split=best;candidate_key=list(key);candidate_key[a],candidate_key[b]=candidate_key[b],candidate_key[a]
    locations=[];base=0
    for message,row in enumerate(messages):
        for pos in range(len(row)):
            if base+pos in changed:locations.append([message,pos,plain[base+pos],changed[base+pos]])
        base+=len(row)
    examples=[]
    for pos,(old,new) in enumerate(zip(plain,candidate)):
        if old==split and (not examples or new!=examples[0][2]):examples.append([pos,old,new])
        if len(examples)==2:break
    out=dict(status='Generated known-table ambiguity; not a model fit to the eyes.',
        control_source_sha256=hashlib.sha256(source_bytes).hexdigest(),control_seed=908210,
        two_entry_swaps_tested=tested,valid_nonrenaming_swaps=len(valid),valid_swap_columns=['label_a','label_b','changed_positions','frequency_a','frequency_b'],
        valid_swaps=valid,selected_labels=[a,b],selected_label_frequencies=[freq[a],freq[b]],
        alternative_key=candidate_key,alternative_decoded=candidate,changed_locations=locations,
        nonrenaming_witness=examples)
    (ROOT/'function_key_ambiguity.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('Valid swaps',len(valid),'of',tested,'selected',a,b,'frequencies',freq[a],freq[b],'changed positions',len(changed),flush=True)

if __name__=='__main__':main()
