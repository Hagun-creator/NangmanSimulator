from pathlib import Path
import re, base64, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v2_98.html')
DST=Path('Nangman_Integrated_Simulator_v2_99.html')
if not SRC.exists(): raise SystemExit('v2.98 source missing')
text=SRC.read_text(encoding='utf-8')

# Version-only bump. Preserve all v2.98 behavior.
text=text.replace('v2.98','v2.99').replace('v2_98','v2_99')
text=re.sub(r'(?<![0-9])2\.98(?![0-9])','2.99',text)
text=re.sub(r'<script id="stable-root-url-v298">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v299">try{if(/Nangman_Integrated_Simulator_v2_99\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace')
inner=inner.replace('v2.98','v2.99').replace('v2_98','v2_99')
inner=re.sub(r'(?<![0-9])2\.98(?![0-9])','2.99',inner)
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{base64.b64encode(inner.encode()).decode()}";'+text[m.end():]
DST.write_text(text,encoding='utf-8')

# PERMANENT stable-root bootstrap. Never replace this with the full app again.
index='''<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">\n<meta http-equiv="Pragma" content="no-cache">\n<meta http-equiv="Expires" content="0">\n<title>낭만강호 통합 시뮬레이터</title>\n</head>\n<body>\n<div id="status">최신 버전을 불러오는 중...</div>\n<script>\n(async()=>{\n  try{\n    const r=await fetch('./latest.json?ts='+Date.now(),{cache:'no-store'});\n    if(!r.ok)throw new Error('latest.json '+r.status);\n    const j=await r.json();\n    const u='./'+j.file+'?build='+encodeURIComponent(j.version)+'&ts='+Date.now();\n    location.replace(u);\n  }catch(e){\n    document.getElementById('status').textContent='최신 버전 확인 실패: '+e;\n  }\n})();\n</script>\n</body>\n</html>\n'''
Path('index.html').write_text(index,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v2.99','file':'Nangman_Integrated_Simulator_v2_99.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md'); s=r.read_text(encoding='utf-8'); s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.99',s); r.write_text(s,encoding='utf-8')

# Regression + permanent loader guards.
for x in ["sharedSaveText = await file.text()","JSON.parse(sharedSaveText)",'pityBeforeState','samePityWash','daoPullRouteBoxV298','잡맥법 최소 세수단 경로']:
    if x not in text: raise SystemExit('regression '+x)
for x in ["latest.json?ts=","cache:'no-store'","location.replace(u)"]:
    if x not in index: raise SystemExit('loader missing '+x)
if 'EQUIPMENT_HTML_B64' in index: raise SystemExit('index must never contain app payload')
if len(index.encode('utf-8'))>12000: raise SystemExit('index loader unexpectedly large')
if '<title>낭만강호 통합 시뮬레이터 v2.99</title>' not in text[:10000]: raise SystemExit('title mismatch')
if '현재 사이트 버전: v2.99' not in r.read_text(encoding='utf-8'): raise SystemExit('README mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v299_app_{i}.js'); p.write_text(js,encoding='utf-8'); cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:1500])
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',index,re.I|re.S)):
    p=Path(f'/tmp/v299_idx_{i}.js'); p.write_text(js,encoding='utf-8'); cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:1500])
print('built v2.99 with permanent stable loader')
