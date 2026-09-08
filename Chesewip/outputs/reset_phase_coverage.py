"""Exhaust independent W1/E2 clock phases using equivalent equation masks.

This uses only the early passage hypotheses. Matrix-equivalent phase pairs
share a certificate; every period/phase pair is still represented exactly.
"""
from pathlib import Path
import json,hashlib,itertools
from periodic_reset_screen import Screen
ROOT=Path(__file__).resolve().parent

def groups(eqs,period,message):
    masks=[0]*period
    for i,e in enumerate(eqs):
        for mi,t in e['positions']:
            if mi==message:masks[(t-1)%period]|=1<<i
    same={}
    for phase,mask in enumerate(masks):same.setdefault(mask,[]).append(phase)
    return [dict(removed_mask=hex(mask),phases=phases) for mask,phases in same.items()]

def main():
    data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values());parent_bytes=(ROOT/'state_memory_comparison.json').read_bytes();parent=json.loads(parent_bytes)
    sc=Screen(messages,parent['assumption_sets']['early']);all_mask=(1<<len(sc.eqs))-1;patterns={};records=[];periods=[];survivors=[]
    limit=max(len(m)-1 for m in messages)
    for period in range(1,limit+1):
        rows,cols=[groups(sc.eqs,period,mi) for mi in [1,2]];grid=[]
        for row,col in itertools.product(rows,cols):
            active=all_mask^(int(row['removed_mask'],16)|int(col['removed_mask'],16))
            if active not in patterns:
                phases=[0]*9;phases[1]=row['phases'][0];phases[2]=col['phases'][0]
                result=sc.test(period,phases)
                patterns[active]=len(records);records.append(dict(active_mask=hex(active),result=result))
            idx=patterns[active];grid.append(idx)
            if records[idx]['result']['status']=='no_forced_collision':
                survivors.extend([period,a,b] for a,b in itertools.product(row['phases'],col['phases']))
        periods.append(dict(period=period,W1_groups=rows,E2_groups=cols,pattern_indices=grid))
    out=dict(status='Exact independent-phase coverage under early plaintext hypotheses; no decipherment.',ciphertext_sha256=hashlib.sha256(data).hexdigest(),parent_sha256=hashlib.sha256(parent_bytes).hexdigest(),equalities=parent['assumption_sets']['early'],period_limit=limit,phase_pairs_covered=sum(b*b for b in range(1,limit+1)),periods=periods,patterns=records,certificates=sc.export(),unresolved_phase_pairs=sorted(survivors))
    (ROOT/'reset_phase_coverage.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    print('Phase pairs',out['phase_pairs_covered'],'unique systems',len(records),'proofs',len(sc.proofs),'unresolved',len(survivors))
    print('Unresolved periods',sorted(set(r[0] for r in survivors)))
    print('Longest interval unresolved examples',[r for r in survivors if r[0]==max(x[0] for x in survivors)])

if __name__=='__main__':main()
