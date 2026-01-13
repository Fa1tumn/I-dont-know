from pathlib import Path
import json

src = Path(__file__).parent / 'extracted_captions.json'
if not src.exists():
    print('extracted_captions.json not found')
    raise SystemExit(1)
arr = json.loads(src.read_text(encoding='utf-8'))
if not arr:
    print('no captions')
    raise SystemExit(1)

sample = [arr[0]]
dst = Path(__file__).parent / 'sample_one.json'
dst.write_text(json.dumps(sample, ensure_ascii=False, indent=2), encoding='utf-8')
print('Wrote', dst)
