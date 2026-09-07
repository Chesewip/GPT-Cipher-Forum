from pathlib import Path
p=Path('outputs/integer_return_paths.py');s=p.read_text(encoding='utf-8-sig').replace('timeout=3000,pinned=None):','timeout=3000,pinned=None,edge_subset=None):')
s=s.replace('edges=graph(ct,classes);edges=[e for e in edges if e[2]<=gap_limit]', 'edges=graph(ct,classes) if edge_subset is None else edge_subset;edges=[e for e in edges if e[2]<=gap_limit]')
p.write_text(s,encoding='utf-8',newline='\r\n')
