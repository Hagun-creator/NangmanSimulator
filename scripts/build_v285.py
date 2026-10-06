from pathlib import Path
import re, base64, subprocess

SRC = Path('Nangman_Integrated_Simulator_v2_84.html')
DST = Path('Nangman_Integrated_Simulator_v2_85.html')
VER = 'v2.85'

if not SRC.exists():
    raise SystemExit('v2.84 source missing')

text = SRC.read_text(encoding='utf-8')
m = re.search(r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;', text)
if not m:
    raise SystemExit('equipment payload missing')
inner = base64.b64decode(m.group(1)).decode('utf-8', 'replace')

# Remove accidental literal newline tokens that can render as visible text.
for bad in ['\\n \\n', '\\n\\n', '/n /n', '/n/n']:
    inner = inner.replace(bad, '')
    text = text.replace(bad, '')

# Replace detail-back behavior. The equipment UI lives inside an iframe,
# so scroll the parent document to the actual result block after repainting.
start = inner.find('function showDetailTop233(')
end = inner.find('\nfunction paintDetail(', start)
if start < 0 or end < 0:
    raise SystemExit('detail navigation function missing')
new_fn = '''function showDetailTop233(obj,backView,initialTab){R.sel=obj;R.detailBack233=backView||R.view;R.detailTab=initialTab||'xl';const m=q('#rmain');m.innerHTML=`<button type="button" class="back218" id="dback233">← 이전 목록</button><div id="dtop233"></div>`;q('#dback233').onclick=()=>{const back=R.detailBack233||'find';open(back);if(back==='find'&&R.results.length){requestAnimationFrame(()=>requestAnimationFrame(()=>{const rr=q('#rresults');if(!rr)return;const localY=rr.getBoundingClientRect().top+window.scrollY;try{if(window.parent&&window.parent!==window&&window.frameElement){const frameY=window.frameElement.getBoundingClientRect().top+window.parent.scrollY;window.parent.scrollTo(0,Math.max(0,frameY+localY-12))}else{window.scrollTo(0,Math.max(0,localY-12))}}catch(_){rr.scrollIntoView({block:'start'})}}))}};paintDetail(q('#dtop233'),obj);window.scrollTo(0,0)}'''
inner = inner[:start] + new_fn + inner[end:]

# Bump every current release marker, including visible labels without leading v.
for a, b in [('v2.84', 'v2.85'), ('v2_84', 'v2_85')]:
    text = text.replace(a, b)
    inner = inner.replace(a, b)
text = re.sub(r'(?<![0-9])2\.84(?![0-9])', '2.85', text)
inner = re.sub(r'(?<![0-9])2\.84(?![0-9])', '2.85', inner)
# Clean stale visible previous-version labels as an extra guard.
inner = re.sub(r'(?<![0-9])v?2\.83(?![0-9])', lambda x: 'v2.85' if x.group(0).startswith('v') else '2.85', inner)

enc = base64.b64encode(inner.encode('utf-8')).decode('ascii')
text = text[:m.start()] + f'const EQUIPMENT_HTML_B64="{enc}";' + text[m.end():]
DST.write_text(text, encoding='utf-8')
Path('index.html').write_text(text, encoding='utf-8')

readme = Path('README.md')
s = readme.read_text(encoding='utf-8') if readme.exists() else '# NangmanSimulator\n'
s = re.sub(r'현재 사이트 버전:\s*v?[0-9.]+', f'현재 사이트 버전: {VER}', s)
if '현재 사이트 버전:' not in s:
    s += f'\n현재 사이트 버전: {VER}\n'
readme.write_text(s, encoding='utf-8')

# Deterministic release assertions.
if f'<title>낭만강호 통합 시뮬레이터 {VER}</title>' not in text[:7000]:
    raise SystemExit('title mismatch')
if "window.parent.scrollTo" not in inner or "q('#rresults')" not in inner:
    raise SystemExit('search-result return patch missing')
for bad in ['\\n \\n', '\\n\\n', '/n /n', '/n/n']:
    if bad in inner:
        raise SystemExit('newline artifact remains: ' + repr(bad))

# Run permanent validator if present.
validator = Path('scripts/validate_release.py')
if validator.exists():
    subprocess.check_call(['python', str(validator), VER])

print('built', DST)
