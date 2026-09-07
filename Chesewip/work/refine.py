from pathlib import Path
p=Path('outputs/analyze.py')
s=p.read_text(encoding='utf-8-sig')
start=s.index("csvpath=")
end=s.index('def ioc')
s=s[:start]+"data=json.loads((ROOT/'ciphertext.json').read_text(encoding='utf-8'))\nnames=list(data)\nmsgs=list(data.values())\n"+s[end:]
s=s.replace("'crosscheck':'GitHub ngraham20 CSV equals Lymm37 wiki ASCII data'", "'crosscheck':'GitHub ngraham20 CSV equals Lymm37 wiki ASCII data'")
s=s.replace("res['graph']['all_exact_isomorphs']=analyze_graph(msgs,equalities)","res['graph']['full_output_plaintext_assumption']=analyze_graph(msgs,equalities)\ntransition_equalities=[(i,s+1,j,t+1,n-1) for i,s,j,t,n in equalities]\nres['graph']['internal_transition_plaintext_assumption']=analyze_graph(msgs,transition_equalities)\nres['boundary_audit']=[dict(ciphertext_match=e,preceding_output_preserves_pattern=signature(msgs[i][s-1:s+n])==signature(msgs[j][t-1:t+n])) for e in equalities for i,s,j,t,n in [e]]")
s=s.replace("print(json.dumps(res,indent=2))", "print('Verified corpus:',res['data']['total'],'symbols; observed alphabet size:',len(res['data']['alphabet']))\nprint('Positive controls:',res['positive_controls'])\nprint('Corrected transition assumptions:',res['graph']['internal_transition_plaintext_assumption'])\nprint('Move-to-front minimum selection alphabet:',res['move_to_front']['minimum_plaintext_symbols'])")
p.write_text(s,encoding='utf-8',newline='\r\n')
p=Path('outputs/deck_scan.py');s=p.read_text(encoding='utf-8-sig');idx=s.index('res={}\n');s=s[:idx]+"if __name__=='__main__':\n"+'\n'.join('    '+line for line in s[idx:].splitlines())+'\n';p.write_text(s,encoding='utf-8',newline='\r\n')
