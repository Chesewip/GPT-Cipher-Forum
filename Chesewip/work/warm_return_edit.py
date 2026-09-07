from pathlib import Path
p=Path('outputs/integer_return_paths.py');s=p.read_text(encoding='utf-8').replace('eliminate_free=False):','eliminate_free=False,warm=None):')
s=s.replace("status=str(solver.check());out=", "if warm:\n        for x,v in p.items():\n            if x in warm:solver.set_initial_value(v,z3.IntVal(warm[x]))\n    status=str(solver.check());out=")
p.write_text(s,encoding='utf-8',newline='\r\n')
