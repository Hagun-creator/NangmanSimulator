from pathlib import Path
import re, base64, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v2_97.html')
DST=Path('Nangman_Integrated_Simulator_v2_98.html')
if not SRC.exists(): raise SystemExit('v2.97 source missing')
text=SRC.read_text(encoding='utf-8')

# Restore the visible route card and delegated click handler that were accidentally
# dropped when v2.96 replaced the exchange-table renderer. Do not alter route math.
old="""h+='</tbody></table></div><div id=\"daoPullRouteV290\" style=\"margin-top:12px\"></div>';
   const pack={window:d,routeRows:DAO_V290_ROUTE_ROWS,html:h};"""
new="""h+='</tbody></table></div>' +
      '<section id=\"daoPullRouteBoxV298\" class=\"card\" style=\"margin-top:14px;padding:12px\">' +
      '<div style=\"font-weight:800;margin-bottom:8px\">잡맥법 최소 세수단 경로</div>' +
      '<div id=\"daoPullRouteV290\" class=\"small\">위 표에서 원하는 <b>원시맥</b>을 누르면 그 행의 교체 1을 기준으로 소모 루트를 계산합니다.</div>' +
      '</section>';
   const pack={window:d,routeRows:DAO_V290_ROUTE_ROWS,html:h};"""
if old not in text: raise SystemExit('v2.97 bare route tail missing')
text=text.replace(old,new,1)

old="""function renderDaoExchangeV296(pack){
 DAO_V290_WINDOW=pack.window;
 DAO_V290_ROUTE_ROWS=pack.routeRows.map(x=>({...x,draws:(x.draws||[]).map(y=>({...y}))}));
 daoExchangeWindowResult.innerHTML=pack.html;
}"""
new="""function renderDaoExchangeV296(pack){
 DAO_V290_WINDOW=pack.window;
 DAO_V290_ROUTE_ROWS=pack.routeRows.map(x=>({...x,draws:(x.draws||[]).map(y=>({...y}))}));
 daoExchangeWindowResult.innerHTML=pack.html;
 daoExchangeWindowResult.onclick=(ev)=>{
   const btn=ev.target.closest?.('.dao-pull-v295');
   if(!btn)return;
   ev.preventDefault();
   const source=decodeURIComponent(btn.dataset.source||'');
   const raw=Number(btn.dataset.raw||0);
   const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw);
   showDaoPullRouteV290(row?.firstDraw||'',raw,source,1);
 };
}"""
if old not in text: raise SystemExit('renderDaoExchangeV296 anchor missing')
text=text.replace(old,new,1)

# Version bump only; all save/equipment/daomai math remains untouched.
text=text.replace('v2.97','v2.98').replace('v2_97','v2_98')
text=re.sub(r'(?<![0-9])2\.97(?![0-9])','2.98',text)
text=re.sub(r'<script id="stable-root-url-v297">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v298">try{if(/Nangman_Integrated_Simulator_v2_98\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace')
inner=inner.replace('v2.97','v2.98').replace('v2_97','v2_98')
inner=re.sub(r'(?<![0-9])2\.97(?![0-9])','2.98',inner)
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{base64.b64encode(inner.encode()).decode()}";'+text[m.end():]

DST.write_text(text,encoding='utf-8')
Path('index.html').write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v2.98','file':'Nangman_Integrated_Simulator_v2_98.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.98',s);r.write_text(s,encoding='utf-8')

# Regression guards: preserve save loading, v2.97 same-pity recovery, and equipment behavior.
for x in [
    "sharedSaveText = await file.text()","JSON.parse(sharedSaveText)",
    'pityBeforeState','samePityWash','exchangeSequence(+pseed,branch,15)',
    'daoDeleteCandidatesV295','dao-pull-v295','showDaoPullRouteV290',
    'daoPullRouteBoxV298','잡맥법 최소 세수단 경로','daoExchangeWindowResult.onclick'
]:
    if x not in text: raise SystemExit('regression '+x)
if '<div id="daoPullRouteV290" style="margin-top:12px"></div>' in text: raise SystemExit('bare route div remains')
if DST.read_text(encoding='utf-8')!=Path('index.html').read_text(encoding='utf-8'): raise SystemExit('index/versioned mismatch')
if '<title>낭만강호 통합 시뮬레이터 v2.98</title>' not in text[:10000]: raise SystemExit('title mismatch')
if '현재 사이트 버전: v2.98' not in r.read_text(encoding='utf-8'): raise SystemExit('README mismatch')

for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v298_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:1500])
print('built v2.98 route panel restored')
