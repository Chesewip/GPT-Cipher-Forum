"""Copy this research snapshot into a contributor folder without private caches."""
from pathlib import Path
from datetime import date
import argparse, hashlib, json, shutil

ap = argparse.ArgumentParser()
ap.add_argument('--source-root', required=True)
ap.add_argument('--repository', required=True)
ap.add_argument('--published-date', default=date.today().isoformat())
a = ap.parse_args()
source = Path(a.source_root).resolve()
repo = Path(a.repository).resolve()
dest = repo / 'Chesewip'
assert (repo / '.git').is_dir()
records = []
for folder, paths in [
    ('outputs', sorted(p for p in (source / 'outputs').iterdir() if p.is_file() and p.name not in ['manifest.json','noita-investigation.zip'])),
    ('work', sorted((source / 'work').glob('*.py'))),
    ('work', [source / 'work' / 'pg1342.txt', source / 'work' / 'pg1661.txt']),
]:
    for p in paths:
        target = dest / folder / p.name
        target.parent.mkdir(parents=True, exist_ok=True)
        data = p.read_bytes()
        action = 'byte-for-byte copy'
        if p.name == 'mead_candidate_audit.json':
            obj = json.loads(data)
            obj['reviewed_pdf']['path'] = 'Noita_Eye_Messages_E3_E4_Step_by_Step (1).pdf'
            obj['reviewed_pdf']['publication_note'] = 'Machine-specific source path removed. The reviewed PDF is not redistributed; its filename and SHA-256 identify the source.'
            data = (json.dumps(obj, indent=2) + '\n').replace('\n','\r\n').encode('utf-8')
            action = 'source PDF path replaced by basename; publication note added'
        target.write_bytes(data)
        records.append(dict(path=f'{folder}/{p.name}', source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                            published_sha256=hashlib.sha256(data).hexdigest(), publication_action=action))
(dest / 'publication').mkdir(exist_ok=True)
shutil.copyfile(Path(__file__), dest / 'publication' / 'prepare_publication.py')
metadata = dict(contributor='Chesewip', published_date=date.fromisoformat(a.published_date).isoformat(), research_status='Unsolved; no authentic plaintext or full-corpus key recovered.',
                included=records,
                regenerated=['outputs/manifest.json','outputs/noita-investigation.zip'],
                source_material_not_redistributed=['downloaded research documents and HTML', 'third-party Git clones and their .git metadata',
                                                  'the user-supplied review PDF and temporary page renders', 'installed Python dependencies and caches'],
                note='All authored top-level research scripts and all final research files are included. The two original Gutenberg control corpora retain their full embedded licenses and original bytes. External research sources are cited in REFERENCES.md.')
(dest / 'publication' / 'import-record.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\r\n')
print('Copied',len(records),'research files;',sum(x['publication_action'] != 'byte-for-byte copy' for x in records),'privacy transformation.')
