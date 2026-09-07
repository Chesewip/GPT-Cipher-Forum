"""Ciphertext-only lower bounds on total changes to relative-state entries.

R_t maps labels in message A's deck to labels at the same positions in B.
An observation (a,b) forces R_t(a)=b and R_t(x)!=b for every x!=a.
For each row x, count the fewest value changes satisfying those constraints,
starting at R_-1(x)=x for a common initial deck. The row counts sum to a lower
bound on total changed entries. A plaintext difference of support at most s
can pay for at most s entries. Swapping the messages supplies another bound.
"""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parent

def row_costs(a,b,n=83,common_initial=True):
    full=(1<<n)-1;results=[]
    for row in range(n):
        possible=(1<<row) if common_initial else full;changes=0;blocks=[];start=-1 if common_initial else 0
        for t,(ca,cb) in enumerate(zip(a,b)):
            allowed=(1<<cb) if ca==row else full^(1<<cb)
            intersection=possible&allowed
            if intersection:possible=intersection
            else:
                changes+=1;blocks.append({'constraint_block_start':start,'constraint_block_end':t,'last_candidates': [x for x in range(n) if possible>>x&1],'new_allowed': [x for x in range(n) if allowed>>x&1]})
                start=t;possible=allowed
        results.append({'row':row,'minimum_entry_changes':changes,'disjoint_change_certificates':blocks})
    return {'minimum_total_entry_changes':sum(r['minimum_entry_changes'] for r in results),'rows':results}

def bound(a,b,n=83,common_initial=True):
    f=row_costs(a,b,n,common_initial);r=row_costs(b,a,n,common_initial);total=max(f['minimum_total_entry_changes'],r['minimum_total_entry_changes'])
    return {'length':min(len(a),len(b)),'common_initial_deck':common_initial,
            'forward_entry_change_bound':f['minimum_total_entry_changes'],'inverse_entry_change_bound':r['minimum_total_entry_changes'],
            'minimum_plaintext_differences_by_relative_support':{str(s):math.ceil(total/s) for s in [3,5]},
            'forward_certificate':f,'inverse_certificate':r}

if __name__=='__main__':
    raw=json.loads((ROOT/'ciphertext.json').read_text());names=list(raw);ms=list(raw.values());out={'focus':[],'all_pairs':[],'different_initial_decks':[]}
    for length in [25,29,34,35,36,37,50,99]:
        r=bound(ms[0][:length],ms[1][:length]);out['focus'].append(r);print({k:v for k,v in r.items() if 'certificate' not in k},flush=True)
    for i in range(len(ms)):
        for j in range(i+1,len(ms)):
            r=bound(ms[i],ms[j]);r['messages']=[names[i],names[j]];out['all_pairs'].append(r)
    for skip in [0,1]:
        r=bound(ms[0][skip:99],ms[1][skip:99],common_initial=False);r['first_ciphertext_omitted']=bool(skip);out['different_initial_decks'].append(r)
        print('unknown initial relation',{k:v for k,v in r.items() if 'certificate' not in k},flush=True)
    out['scope']='Necessary Hamming-distance bounds under fixed-per-letter positional permutations with a maximum relative support. No language, alphabet-size, or repeated-plaintext assumptions. All indices zero-based in certificates.'
    (ROOT/'entry_change_bounds.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
