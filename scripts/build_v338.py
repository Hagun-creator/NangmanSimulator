from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_37.html')
DST=Path('Nangman_Integrated_Simulator_v3_38.html')
if not SRC.exists(): raise SystemExit('v3.37 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.37','v3.38').replace('v3_37','v3_38')
text=re.sub(r'(?<![0-9])3\.37(?![0-9])','3.38',text)
text=re.sub(r'<script id="stable-root-url-v337">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v338">try{if(/Nangman_Integrated_Simulator_v3_38\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Remove the remaining visible drop token from summary-style separator text.
# Do not touch the drop-cleanup script's regex, because that script is what keeps old drop UI hidden.
before=text
text=re.sub(r'\s*·\s*드랍\s*·\s*', ' · ', text)
text=re.sub(r'\s*·\s*드롭\s*·\s*', ' · ', text)
if text==before: raise SystemExit('no visible drop separator token found')
if re.search(r'세수[^<\n]{0,300}·\s*(?:드랍|드롭)\s*·[^<\n]{0,300}세이브 데이터 준비 전',text):
    raise SystemExit('drop token still remains in top summary')

if '낭만강호 시뮬레이터 v3.38' not in text[:12000]: raise SystemExit('title/version mismatch')
for tok in ['remove-drop-ui-v337','solutionCostFloor=Math.max(0,goalNeed*4)','BEAM_PER_CELL=8']:
    if tok not in text: raise SystemExit('regression guard missing: '+tok)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.38','file':'Nangman_Integrated_Simulator_v3_38.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.38',s);r.write_text(s,encoding='utf-8')

scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)
if not scripts: raise SystemExit('no scripts')
for i,js in enumerate(scripts):
    if not js.strip(): continue
    p=Path(f'/tmp/v338_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
print('built v3.38: removed remaining visible drop token from summary text')
