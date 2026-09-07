"""Create or verify byte manifests and publication checks; no project build."""
from pathlib import Path
import argparse, ast, hashlib, json, re, zipfile
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'publication' / 'snapshot-manifest.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and p != MANIFEST
                  and not any(x in p.relative_to(ROOT).parts for x in ['__pycache__','pydeps','reference','wiki','.git']))


def validate():
    files = inventory()
    counts = {'files':len(files), 'python_syntax_checks':0, 'json_parse_checks':0, 'authored_CRLF_checks':0}
    patterns = [r'[A-Za-z]:[\\/]+Users[\\/]', r'gh[pousr]_[A-Za-z0-9]{30,}',
                r'github_pat_[A-Za-z0-9_]{30,}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']
    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        if path.suffix in ['.py','.md','.txt','.json']:
            text = data.decode('utf-8-sig')
            for pattern in patterns:
                assert not re.search(pattern,text), 'Private path or credential pattern: ' + rel
            if rel not in ['work/pg1342.txt','work/pg1661.txt']:
                assert b'\n' not in data.replace(b'\r\n',b''), 'Expected CRLF: ' + rel
                counts['authored_CRLF_checks'] += 1
            if path.suffix == '.py':
                ast.parse(text,filename=rel)
                counts['python_syntax_checks'] += 1
            if path.suffix == '.json':
                json.loads(text)
                counts['json_parse_checks'] += 1
    output_manifest = json.loads((ROOT/'outputs/manifest.json').read_text())
    for record in output_manifest['files']:
        p = ROOT/'outputs'/record['name']
        assert p.stat().st_size == record['bytes'] and digest(p) == record['sha256'], record['name']
    with zipfile.ZipFile(ROOT/'outputs/noita-investigation.zip') as archive:
        assert archive.testzip() is None
        expected = {r['name'] for r in output_manifest['files']} | {'manifest.json'}
        assert set(archive.namelist()) == expected
        for name in expected:
            assert archive.read(name) == (ROOT/'outputs'/name).read_bytes(),name
    imported = json.loads((ROOT/'publication/import-record.json').read_text())
    for record in imported['included']:
        assert digest(ROOT/record['path']) == record['published_sha256'], record['path']
    counts.update(output_manifest_entries=len(output_manifest['files']), zip_integrity=True,
                  zip_matches_loose_files=True, imported_research_files=len(imported['included']),
                  import_hashes_verified=True, privacy_pattern_scan=True, project_build_run=False)
    return files, counts


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    args = ap.parse_args()
    files, checks = validate()
    records = [dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in files]
    if args.verify:
        saved = json.loads(MANIFEST.read_text())
        assert saved['files'] == records, 'Snapshot differs from the manifest; review changes before regenerating.'
    else:
        MANIFEST.write_text(json.dumps(dict(status='Unsolved; no authentic plaintext or full-corpus key.',checks=checks,files=records),indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(checks,indent=2))
