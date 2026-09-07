from pathlib import Path
for source,dest in [('work/relative_earliest.py','outputs/relative_cycle_earliest.py'),('work/check_integer_cycles.py','outputs/verify_relative_cycle_integer.py')]:
    p=Path(source);s=p.read_text(encoding='utf-8-sig')
    s=s.replace("sys.path.insert(0,'outputs')", "ROOT=Path(__file__).resolve().parent\nsys.path.insert(0,str(ROOT))")
    s=s.replace("Path('outputs/ciphertext.json')", "(ROOT/'ciphertext.json')")
    s=s.replace("Path('outputs/relative_cycle_earliest.json')", "(ROOT/'relative_cycle_earliest.json')")
    s=s.replace("Path('outputs/checked_relative_cycle_integer.json')", "(ROOT/'checked_relative_cycle_integer.json')")
    Path(dest).write_text(s,encoding='utf-8',newline='\r\n')
