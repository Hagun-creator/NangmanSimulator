from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_21.html')
DST=Path('Nangman_Integrated_Simulator_v3_22.html')
if not SRC.exists(): raise SystemExit('v3.21 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.21','v3.22').replace('v3_21','v3_22')
text=re.sub(r'(?<![0-9])3\.21(?![0-9])','3.22',text)
text=re.sub(r'<script id="stable-root-url-v321">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v322">try{if(/Nangman_Integrated_Simulator_v3_22\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# v3.21 calls daoV296Key() but the helper was dropped in an earlier refactor.
# Restore it immediately before the exchange-window function using explicit DOM lookups.
anchor='async function showDaoExchangeWindowV288(){'
if anchor not in text: raise SystemExit('exchange function anchor missing')
helper='''function daoV296Key(){\n const role=document.getElementById('roleSel');\n const vip=document.getElementById('vipSel');\n return [role?.value||'',vip?.value||'',rawCalcZizhi(),JSON.stringify(SPECIAL_STATE||{})].join('|');\n}\n'''
if 'function daoV296Key(){' not in text:
    text=text.replace(anchor,helper+anchor,1)

# Bump cache suffix so stale v3.21 data can never be reused.
text=text.replace("|raw600-post6-v321","|raw600-post6-v322")

for x in [
 'function daoV296Key(){',"document.getElementById('roleSel')", "document.getElementById('vipSel')",
 'async function showDaoExchangeWindowV288(){','|raw600-post6-v322',
 '2. 원시 #600~천장 이후 6개 교체맥 보기','const minRaw=600;','slice(0,6)',
 '잡맥법 최소 세수단 경로'
]:
 if x not in text: raise SystemExit('v3.22 guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.22','file':'Nangman_Integrated_Simulator_v3_22.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.22',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.22</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v322_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.22: restore daoV296Key with explicit DOM lookups')
