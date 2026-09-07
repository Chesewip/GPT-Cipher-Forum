from pathlib import Path
p=Path('outputs/integer_return_paths.py');s=p.read_text(encoding='utf-8').replace('assert selection[vals[t]]==u\n    return out','assert selection[vals[t]]==u\n        out[\'selector_assignment\']=[[x,v] for x,v in selection.items()]\n    return out')
s=s.replace('results.append(r);print(r,flush=True)', "results.append(r);print({k:v for k,v in r.items() if k!='selector_assignment'},flush=True)")
p.write_text(s,encoding='utf-8',newline='\r\n')
p=Path('outputs/component_return_paths.py');s=p.read_text(encoding='utf-8').replace('print(r,flush=True)', "print({k:v for k,v in r.items() if k!='selector_assignment'},flush=True)");p.write_text(s,encoding='utf-8',newline='\r\n')
