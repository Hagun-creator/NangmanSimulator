from pathlib import Path
import re, base64, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v2_99.html')
DST=Path('Nangman_Integrated_Simulator_v3_00.html')
if not SRC.exists(): raise SystemExit('v2.99 source missing')
text=SRC.read_text(encoding='utf-8')

# Version bump only outside the focused daomai rollback.
text=text.replace('v2.99','v3.00').replace('v2_99','v3_00')
text=re.sub(r'(?<![0-9])2\.99(?![0-9])','3.00',text)
text=re.sub(r'<script id="stable-root-url-v299">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v300">try{if(/Nangman_Integrated_Simulator_v3_00\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Keep embedded equipment payload behavior intact; only synchronize displayed version.
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace')
inner=inner.replace('v2.99','v3.00').replace('v2_99','v3_00')
inner=re.sub(r'(?<![0-9])2\.99(?![0-9])','3.00',inner)
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{base64.b64encode(inner.encode()).decode()}";'+text[m.end():]

# Focused rollback: restore the pre-v2.88 daomai entry point.
# The old analyzeFirstPityDaomai() engine is intentionally still present in v2.99.
old_ui='''<div id="pityPane" class="pane">\n<div class="row" style="margin-bottom:8px">\n<button id="daoRawBeforeBtn">1. 천장 전 모든 원시맥 보기</button>\n<button id="daoExchangeWindowBtn">2. 천장 포함 이후 교체맥 보기</button>\n</div>\n<div class="small" style="margin-bottom:10px">첫 원시 자맥이 천장인 경우만 계산합니다. 1번은 첫 천장 직전까지의 모든 원시맥, 2번은 천장맥 자체를 포함해 다음 원시 자맥 직전까지의 교체맥만 표시합니다.</div>\n<div id="daoRawBeforeResult"></div>\n<div id="daoExchangeWindowResult" style="margin-top:12px"></div>'''
new_ui='''<div id="pityPane" class="pane">\n<div class="row" style="margin-bottom:8px">\n<button id="daoFirstBtn">첫 자맥 천장 도맥법 보기</button>\n<span class="small">원시 #600부터 기본 천장 직전까지의 일반맥을 후보로 계산합니다. 각 후보가 천장 직전 맥이 되었을 때의 seed 기준으로 천장 자맥과 교체맥 15개를 표시합니다.</span>\n</div>\n<div id="daoFirstResult" style="margin-top:10px"></div>'''
if old_ui not in text: raise SystemExit('current v2.99 daomai UI block not found')
text=text.replace(old_ui,new_ui,1)

old_bind='nCalc.onclick=calcN;daoRawBeforeBtn.onclick=showDaoRawBeforeV288;daoExchangeWindowBtn.onclick=showDaoExchangeWindowV288;'
new_bind='nCalc.onclick=calcN;daoFirstBtn.onclick=analyzeFirstPityDaomai;'
if old_bind not in text: raise SystemExit('current v2.99 daomai binding not found')
text=text.replace(old_bind,new_bind,1)

# Guard the restored #600-before-pity calculation path.
for x in [
    'async function analyzeFirstPityDaomai()',
    'const minRaw=600;',
    '원시 #600 이후 천장 직전 일반맥별 seed → 교체맥 15개 계산 중...',
    '표는 #600부터 기본 천장 직전까지의 일반맥을 후보로 봅니다.',
    'daoFirstBtn.onclick=analyzeFirstPityDaomai;'
]:
    if x not in text: raise SystemExit('daomai rollback guard missing: '+x)
if 'daoRawBeforeBtn.onclick=showDaoRawBeforeV288' in text:
    raise SystemExit('post-pity daomai binding still active')

DST.write_text(text,encoding='utf-8')

# Permanent stable-root loader stays small; only latest.json moves to v3.00.
Path('latest.json').write_text(json.dumps({'version':'v3.00','file':'Nangman_Integrated_Simulator_v3_00.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md')
s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.00',s)
r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.00</title>' not in text[:10000]: raise SystemExit('title mismatch')
if '현재 사이트 버전: v3.00' not in r.read_text(encoding='utf-8'): raise SystemExit('README mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v300_app_{i}.js'); p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:1500])
print('built v3.00: restored pre-pity #600+ daomai table')
