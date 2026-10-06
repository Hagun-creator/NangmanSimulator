from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_06.html')
DST=Path('Nangman_Integrated_Simulator_v3_07.html')
if not SRC.exists(): raise SystemExit('v3.06 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.06','v3.07').replace('v3_06','v3_07')
text=re.sub(r'(?<![0-9])3\.06(?![0-9])','3.07',text)
text=re.sub(r'<script id="stable-root-url-v306">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v307">try{if(/Nangman_Integrated_Simulator_v3_07\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Display #700 -> pity-predecessor in ascending raw order.
old='const usable=candidates.filter(x=>+x.rawNo<=+currentPrev.rawNo).sort((a,b)=>b.rawNo-a.rawNo);'
new='const usable=candidates.filter(x=>+x.rawNo<=+currentPrev.rawNo).sort((a,b)=>a.rawNo-b.rawNo);'
if old not in text: raise SystemExit('descending usable sort not found')
text=text.replace(old,new,1)

text=text.replace('천장에 가까운 원시맥부터 처리합니다.','원시 #700부터 순서대로 처리합니다.',1)

for x in [
 '2. 원시 #700~천장 직전 교체맥 보기',
 'const minRaw=700;',
 'sort((a,b)=>a.rawNo-b.rawNo)',
 'for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||\'-\'}</td>`;',
 "showDaoPullRouteV290(row?.firstDraw||'',raw,source,1);"
]:
 if x not in text: raise SystemExit('v3.07 guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.07','file':'Nangman_Integrated_Simulator_v3_07.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md')
s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.07',s)
r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.07</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v307_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.07: exchange table displayed ascending from raw #700')
