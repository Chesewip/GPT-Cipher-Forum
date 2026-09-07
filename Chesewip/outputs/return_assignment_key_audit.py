"""Audit whether saved return assignments permit arbitrary decks on known runs."""
from pathlib import Path
import json
from clocked_three_cycle_scan import encrypt_physical
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent

def audit(messages,classes,assignment,owners=None):
    failures=[];runs=[]
    for mi,(ct,cl) in enumerate(zip(messages,classes)):
        t=0
        while t<len(ct):
            if cl[t] not in assignment:t+=1;continue
            start=t;owner=None if owners is None else owners[cl[t]]
            while t<len(ct) and cl[t] in assignment and (owners is None or owners[cl[t]]==owner):t+=1
            end=t;plain=[assignment[x]+1 for x in cl[start:end]];slots=encrypt_physical(plain,range(83),1,9)
            observations=list(zip(range(start,end),slots,ct[start:end]))
            if start>0:observations.insert(0,(start-1,0,ct[start-1]))
            by_slot={};by_card={};conflicts=[]
            for at,slot,card in observations:
                if slot in by_slot and by_slot[slot][1]!=card:conflicts.append({'kind':'same_slot_different_cards','positions':[by_slot[slot][0],at],'cards':[by_slot[slot][1],card],'slot':slot})
                if card in by_card and by_card[card][1]!=slot:conflicts.append({'kind':'same_card_different_slots','positions':[by_card[card][0],at],'slots':[by_card[card][1],slot],'card':card})
                by_slot.setdefault(slot,(at,card));by_card.setdefault(card,(at,slot))
            runs.append({'message':mi,'start':start,'end':end,'owner':owner,'consistent':not conflicts})
            for conflict in conflicts:failures.append({'message':mi,'known_input_run':[start,end],'owner':owner,**conflict})
    return {'runs':runs,'failures':sorted(failures,key=lambda r:(r['positions'][1]-r['positions'][0],r['message'],r['positions']))}

if __name__=='__main__':
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());out=[]
    for gap in [18,20]:
        source=json.loads((ROOT/f'component_returns_{gap}_9_free.json').read_text());classes=make_plaintexts(messages,source['assumed_equalities']);assignment={};owners={}
        for j,c in enumerate(source['components']):
            for x,p in c['selector_assignment']:assignment[tuple(x)]=p;owners[tuple(x)]=j
        all_runs=audit(messages,classes,assignment);single=audit(messages,classes,assignment,owners)
        r={'gap':gap,'all_known_runs':all_runs,'single_component_runs':single,'warning':'Contradictions reject the saved selector assignment, not the cipher family. Single-component contradictions are unchanged by rotating that component coordinate system.'}
        out.append(r);print('gap',gap,'all failures',len(all_runs['failures']),'single-component failures',len(single['failures']),'shortest',single['failures'][:2],flush=True)
    (ROOT/'return_assignment_key_audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
