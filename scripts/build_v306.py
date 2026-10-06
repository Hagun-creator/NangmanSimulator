from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_05.html')
DST=Path('Nangman_Integrated_Simulator_v3_06.html')
if not SRC.exists(): raise SystemExit('v3.05 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.05','v3.06').replace('v3_05','v3_06')
text=re.sub(r'(?<![0-9])3\.05(?![0-9])','3.06',text)
text=re.sub(r'<script id="stable-root-url-v305">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v306">try{if(/Nangman_Integrated_Simulator_v3_06\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# v3.06: remove another stale helper dependency. The current integrated file no longer
# defines renderDaoExchangeV296(), so render the already-built pack inline and attach
# the exact same row-click route handler directly.
old='   renderDaoExchangeV296(pack);'
new=r'''   DAO_V290_WINDOW=pack.window;
   DAO_V290_ROUTE_ROWS=(pack.routeRows||[]).map(x=>({...x,draws:(x.draws||[]).map(y=>({...y}))}));
   daoExchangeWindowResult.innerHTML=pack.html;
   daoExchangeWindowResult.onclick=(ev)=>{
     const btn=ev.target.closest?.('.dao-pull-v295');
     if(!btn)return;
     ev.preventDefault();
     const source=decodeURIComponent(btn.dataset.source||'');
     const raw=Number(btn.dataset.raw||0);
     const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw);
     showDaoPullRouteV290(row?.firstDraw||'',raw,source,1);
   };'''
if old not in text: raise SystemExit('renderDaoExchangeV296(pack) call not found')
text=text.replace(old,new,1)

# There must be no remaining executable call to the missing renderer.
if 'renderDaoExchangeV296(pack);' in text: raise SystemExit('stale renderDaoExchangeV296 call remains')

for x in [
 '2. 원시 #700~천장 직전 교체맥 보기',
 'const minRaw=700;',
 "document.getElementById('daoExchangeWindowBtn')",
 '교체맥 계산 오류:',
 "const btn=ev.target.closest?.('.dao-pull-v295')",
 "showDaoPullRouteV290(row?.firstDraw||'',raw,source,1);",
 'for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||\'-\'}</td>`;'
]:
 if x not in text: raise SystemExit('v3.06 guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.06','file':'Nangman_Integrated_Simulator_v3_06.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md')
s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.06',s)
r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.06</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v306_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.06: inline exchange-table render + row click binding; no renderDaoExchangeV296 dependency')
