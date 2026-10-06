from pathlib import Path
import re, base64, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v2_91.html')
DST=Path('Nangman_Integrated_Simulator_v2_92.html')
if not SRC.exists(): raise SystemExit('v2.91 source missing')
text=SRC.read_text(encoding='utf-8')

# Version-only bump. Do not change application behavior.
text=text.replace('v2.91','v2.92').replace('v2_91','v2_92')
text=re.sub(r'(?<![0-9])2\.91(?![0-9])','2.92',text)

# Embedded equipment version labels only.
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace')
inner=inner.replace('v2.91','v2.92').replace('v2_91','v2_92')
inner=re.sub(r'(?<![0-9])2\.91(?![0-9])','2.92',inner)
enc=base64.b64encode(inner.encode()).decode()
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{enc}";'+text[m.end():]

# When a versioned file is loaded by the bootstrapper, keep the visible URL simple.
head_end=text.lower().find('</head>')
if head_end<0: raise SystemExit('head end missing')
url_script="""<script id=\"stable-root-url-v292\">try{if(/Nangman_Integrated_Simulator_v2_92\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n"""
text=text[:head_end]+url_script+text[head_end:]

DST.write_text(text,encoding='utf-8')

# Permanent tiny bootstrap. This file should stay generic across future releases.
index='''<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">\n<meta http-equiv="Pragma" content="no-cache">\n<meta http-equiv="Expires" content="0">\n<title>낭만강호 통합 시뮬레이터</title>\n</head>\n<body>\n<div id="status">최신 버전을 불러오는 중...</div>\n<script>\n(async()=>{\n  try{\n    const r=await fetch('./latest.json?ts='+Date.now(),{cache:'no-store'});\n    if(!r.ok)throw new Error('latest.json '+r.status);\n    const j=await r.json();\n    const u='./'+j.file+'?build='+encodeURIComponent(j.version)+'&ts='+Date.now();\n    location.replace(u);\n  }catch(e){\n    document.getElementById('status').textContent='최신 버전 확인 실패: '+e;\n  }\n})();\n</script>\n</body>\n</html>\n'''
Path('index.html').write_text(index,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v2.92','file':'Nangman_Integrated_Simulator_v2_92.html'},ensure_ascii=False,indent=2),encoding='utf-8')

r=Path('README.md');s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.92',s);r.write_text(s,encoding='utf-8')

# Regression guards: preserve working save loader and current daomai behavior.
for x in ["const sharedSaveInput = document.getElementById('sharedSaveFile')","sharedSaveInput?.addEventListener('change'","sharedSaveText = await file.text()","JSON.parse(sharedSaveText)"]:
    if x not in text: raise SystemExit('save loader regression: '+x)
for x in ['daoRawBeforeBtn.onclick=showDaoRawBeforeV288','daoExchangeWindowBtn.onclick=showDaoExchangeWindowV288','showDaoPullRouteV290']:
    if x not in text: raise SystemExit('daomai regression: '+x)
# Loader invariants.
for x in ["latest.json?ts=","cache:'no-store'","location.replace(u)"]:
    if x not in index: raise SystemExit('bootstrap missing '+x)
if '/NangmanSimulator/' not in url_script: raise SystemExit('root URL restore missing')
# JS syntax-check application scripts and bootstrap.
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v292_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(f'app JS syntax error {i}: {cp.stderr[:1500]}')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',index,re.I|re.S)):
    p=Path(f'/tmp/v292_idx_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(f'index JS syntax error {i}: {cp.stderr[:1500]}')
if '<title>낭만강호 통합 시뮬레이터 v2.92</title>' not in text[:10000]: raise SystemExit('title mismatch')
print('built v2.92 permanent latest loader')
