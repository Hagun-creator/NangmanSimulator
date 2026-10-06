from pathlib import Path
import re, base64, subprocess

OUTER_SRC=Path('Nangman_Integrated_Simulator_v2_84.html')
INNER_SRC=Path('Nangman_Integrated_Simulator_v2_85.html')
DST=Path('Nangman_Integrated_Simulator_v2_87.html')
VER='v2.87'

if not OUTER_SRC.exists() or not INNER_SRC.exists(): raise SystemExit('required source missing')
outer=OUTER_SRC.read_text(encoding='utf-8')
v285=INNER_SRC.read_text(encoding='utf-8')
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
mo=re.search(pat,outer); mi=re.search(pat,v285)
if not mo or not mi: raise SystemExit('equipment payload missing')
inner=base64.b64decode(mi.group(1)).decode('utf-8','replace')

# Keep latest equipment fixes while advancing visible version labels.
inner=inner.replace('v2.85','v2.87').replace('v2_85','v2_87')
inner=re.sub(r'(?<![0-9])2\.85(?![0-9])','2.87',inner)
for bad in ['\\n \\n','\\n\\n','/n /n','/n/n']:
    inner=inner.replace(bad,'')

# Known-good outer shell/save loader from v2.84.
outer=outer.replace('v2.84','v2.87').replace('v2_84','v2_87')
outer=re.sub(r'(?<![0-9])2\.84(?![0-9])','2.87',outer)

# Prevent stale root HTML from being reused after the browser has fetched this release once.
cache_meta='''<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">\n<meta http-equiv="Pragma" content="no-cache">\n<meta http-equiv="Expires" content="0">'''
if 'http-equiv="Cache-Control"' not in outer:
    outer=outer.replace('<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">', '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'+cache_meta,1)

enc=base64.b64encode(inner.encode('utf-8')).decode('ascii')
outer=outer[:mo.start()]+f'const EQUIPMENT_HTML_B64="{enc}";'+outer[mo.end():]
DST.write_text(outer,encoding='utf-8')
Path('index.html').write_text(outer,encoding='utf-8')

r=Path('README.md'); s=r.read_text(encoding='utf-8') if r.exists() else '# NangmanSimulator\n'
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+',f'현재 사이트 버전: {VER}',s)
if '현재 사이트 버전:' not in s:s+=f'\n현재 사이트 버전: {VER}\n'
r.write_text(s,encoding='utf-8')

# Save loader regression guards.
required=[
 "const sharedSaveInput = document.getElementById('sharedSaveFile')",
 "sharedSaveInput?.addEventListener('change'",
 "sharedSaveText = await file.text()",
 "JSON.parse(sharedSaveText)",
]
for x in required:
    if x not in outer: raise SystemExit('save loader regression: '+x)

# Equipment fixes and artifact guards.
if "window.parent.scrollTo" not in inner or "q('#rresults')" not in inner:
    raise SystemExit('search-result return regression')
for bad in ['\\n \\n','\\n\\n','/n /n','/n/n']:
    if bad in inner: raise SystemExit('newline artifact remains '+repr(bad))

if f'<title>낭만강호 통합 시뮬레이터 {VER}</title>' not in outer[:8000]: raise SystemExit('title mismatch')
if f'현재 사이트 버전: {VER}' not in s: raise SystemExit('README mismatch')
if 'http-equiv="Cache-Control"' not in outer[:8000]: raise SystemExit('cache-control meta missing')

# Syntax-check every executable script block.
scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',outer,re.I|re.S)
for i,js in enumerate(scripts):
    p=Path(f'/tmp/nangman_v287_script_{i}.js'); p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode!=0:
        raise SystemExit(f'JS syntax error script {i}: {cp.stderr[:1200]}')

print('built',DST,'scripts',len(scripts))
