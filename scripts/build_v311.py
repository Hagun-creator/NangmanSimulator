from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_09.html')
DST=Path('Nangman_Integrated_Simulator_v3_11.html')
if not SRC.exists(): raise SystemExit('v3.09 source missing')
text=SRC.read_text(encoding='utf-8')

# Version only. Keep all v3.09 logic intact.
text=text.replace('v3.09','v3.11').replace('v3_09','v3_11')
text=re.sub(r'(?<![0-9])3\.09(?![0-9])','3.11',text)
text=re.sub(r'<script id="stable-root-url-v309">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v311">try{if(/Nangman_Integrated_Simulator_v3_11\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# ONLY UI change: make duplicate-skip text a normal block below the wash line.
old='''${sk?`<br><span class="good">이 회차 중복 스킵: ${sk}</span>`:''}'''
new='''${sk?`<div style="margin-top:4px;display:block;position:static;clear:both;white-space:normal"><b>이 회차 중복 스킵:</b> ${sk}</div>`:''}'''
if old not in text: raise SystemExit('duplicate-skip renderer not found')
text=text.replace(old,new,1)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.11','file':'Nangman_Integrated_Simulator_v3_11.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md')
s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.11',s)
r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.11</title>' not in text[:10000]: raise SystemExit('title mismatch')
# Validate every inline script. This regex intentionally uses \b, not \\b.
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v311_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.11 from v3.09 with only duplicate-skip block layout change')
