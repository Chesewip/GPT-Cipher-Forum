from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'outputs'
for directory in [OUT,ROOT/'work']:
    for path in directory.iterdir():
        if path.is_file() and path.suffix in {'.py','.md','.json','.txt'}:
            # Source documents in work are retained as downloaded. Normalize
            # only authored scripts there, and all deliverable text files.
            if directory!=OUT and path.suffix!='.py':continue
            data=path.read_text(encoding='utf-8')
            path.write_text(data,encoding='utf-8',newline='\r\n')
files=sorted(p for p in OUT.iterdir() if p.is_file() and p.suffix in {'.py','.md','.json','.txt'} and p.name!='manifest.json')
manifest={'status':'Unsolved; no real plaintext or key recovered.',
          'files':[{ 'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files]}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\r\n')
files.append(OUT/'manifest.json')
for path in files:
    data=path.read_bytes()
    assert b'\n' not in data.replace(b'\r\n',b''),path
    if path.suffix=='.json':json.loads(data)
with zipfile.ZipFile(OUT/'noita-investigation.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for path in files:archive.write(path,path.name)
with zipfile.ZipFile(OUT/'noita-investigation.zip') as archive:
    assert archive.testzip() is None
print('Packaged',len(files),'files; JSON and CRLF checks passed; ZIP integrity passed.')
print('Bundle bytes:',(OUT/'noita-investigation.zip').stat().st_size)
