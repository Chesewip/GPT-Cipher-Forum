from pathlib import Path
import json,hashlib,subprocess
root=Path('outputs')
p=root/'verify_scan.py'
s=p.read_text()
s=s.replace("sys.path.insert(0,str(Path('outputs').resolve()))", "ROOT=Path(__file__).resolve().parent\nsys.path.insert(0,str(ROOT))")
s=s.replace("Path('outputs/scan_control.json')", "(ROOT/'scan_control.json')")
p.write_text(s,encoding='utf-8',newline='\r\n')
refs=[]
for folder,url in [('reference','https://github.com/ngraham20/NoitaCryptographyResearch'),('wiki','https://github.com/Lymm37/eye-messages/wiki')]:
    commit=subprocess.check_output(['git','-C','work/'+folder,'rev-parse','HEAD'],text=True).strip()
    refs.append(dict(url=url,commit=commit))
p=root/'provenance.json'
p.write_text(json.dumps(dict(accessed='2026-09-06',sources=refs,ciphertext_sha256=hashlib.sha256((root/'ciphertext.json').read_bytes()).hexdigest(),crosscheck='Two published representations agree. No independent executable extraction performed.'),indent=2)+'\n',encoding='utf-8',newline='\r\n')
for p in root.iterdir():
    if p.is_file():
        s=p.read_text(encoding='utf-8-sig')
        p.write_text(s,encoding='utf-8',newline='\r\n')
        b=p.read_bytes()
        assert b.count(b'\n')==b.count(b'\r\n'),p
print('Deliverables saved with CRLF line endings.')
