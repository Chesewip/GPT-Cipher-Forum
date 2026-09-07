from pathlib import Path
p=Path('outputs/return_displacement.py');s=p.read_text(encoding='utf-8-sig').replace('(t-r)*b','(t-r-1)*b').replace('1+gap*b','1+(gap-1)*b');p.write_text(s,encoding='utf-8',newline='\r\n')
