from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_23.html')
DST=Path('Nangman_Integrated_Simulator_v3_24.html')
if not SRC.exists(): raise SystemExit('v3.23 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.23','v3.24').replace('v3_23','v3_24')
text=re.sub(r'(?<![0-9])3\.23(?![0-9])','3.24',text)
text=re.sub(r'<script id="stable-root-url-v323">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v324">try{if(/Nangman_Integrated_Simulator_v3_24\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Display-order fix only: pre-pity rows must render raw #600 upward.
old="const usable=[...preUsable.sort((x,y)=>y.rawNo-x.rawNo),...postCandidates];"
new="const usable=[...preUsable.sort((x,y)=>x.rawNo-y.rawNo),...postCandidates];"
if old not in text: raise SystemExit('descending pre-pity display sort not found')
text=text.replace(old,new,1)

# Regression guards: calculations/helpers/routes unchanged.
for x in [
 'function daoV296Key(',
 'function renderDaoExchangeV296(',
 'const minRaw=600;',
 'slice(0,6)',
 'class="linkBtn dao-pull-v295"',
 '잡맥법 최소 세수단 경로',
 'const usable=[...preUsable.sort((x,y)=>x.rawNo-y.rawNo),...postCandidates];'
]:
 if x not in text: raise SystemExit('v3.24 guard missing: '+x)
if 'const usable=[...preUsable.sort((x,y)=>y.rawNo-x.rawNo),...postCandidates];' in text:
 raise SystemExit('descending display sort still present')

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.24','file':'Nangman_Integrated_Simulator_v3_24.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.24',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.24</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v324_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.24: pre-pity table displays raw #600 upward; logic unchanged')
