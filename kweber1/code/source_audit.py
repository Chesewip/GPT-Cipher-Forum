"""Reconstruct all nine published messages from the Google Doc's digit rows."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_HASH = '9a24f55e1480b92261ffa3c8f8d0dc7e5f22916e9841b1c3934eaa6c1bd6e529'


def reconstruct(rows):
    assert len(rows) % 2 == 0
    out = []
    for top, bottom in zip(rows[::2], rows[1::2]):
        assert set(top + bottom) <= set('01234')
        assert len(top) == len(bottom) or len(top) == len(bottom) + 1
        assert (len(top) + len(bottom)) % 3 == 0
        for j in range(0, len(top), 3):
            out.append(int(top[j:j + 2] + bottom[j], 5))
            if j + 2 < len(top):
                out.append(int(bottom[j + 2] + bottom[j + 1] + top[j + 2], 5))
    return out


def main():
    source = (ROOT / 'data/ciphertext.json').read_bytes()
    assert sha256(source).hexdigest() == EXPECTED_HASH
    data = json.loads(source)
    rows = json.loads((ROOT / 'data/eye_rows.json').read_text())
    assert list(data) == list(rows)
    result = {}
    for name, expected in data.items():
        actual = reconstruct(rows[name])
        assert actual == expected, name
        result[name] = dict(raw_length=len(actual), eye_count=sum(map(len, rows[name])),
                            first_symbol=actual[0], body_length=len(actual)-1,
                            exact_integer_match=True)
    out = dict(executed_utc=datetime.now(timezone.utc).isoformat(), python=sys.version,
               corpus_sha256=EXPECTED_HASH, messages=result,
               total_raw_symbols=sum(map(len, data.values())),
               total_body_symbols=sum(len(r)-1 for r in data.values()),
               total_body_adjacent_pairs=sum(len(r)-2 for r in data.values()),
               scope='Published textual transcription crosscheck; no extraction from game executable or image.')
    (ROOT / 'results').mkdir(exist_ok=True)
    (ROOT / 'results/source_check.json').write_text(json.dumps(out, indent=2)+'\n', encoding='utf-8', newline='\r\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
