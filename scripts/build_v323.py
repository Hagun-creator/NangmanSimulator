from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_22.html')
DST=Path('Nangman_Integrated_Simulator_v3_23.html')
if not SRC.exists(): raise SystemExit('v3.22 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.22','v3.23').replace('v3_22','v3_23')
text=re.sub(r'(?<![0-9])3\.22(?![0-9])','3.23',text)
text=re.sub(r'<script id="stable-root-url-v322">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v323">try{if(/Nangman_Integrated_Simulator_v3_23\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Restore the missing exchange helpers only. Do not alter table or route calculations.
anchor='async function showDaoExchangeWindowV288(){'
if anchor not in text: raise SystemExit('exchange function anchor missing')
helper='''function renderDaoExchangeV296(pack){\n const out=document.getElementById('daoExchangeWindowResult');\n if(!out)throw new Error('daoExchangeWindowResult not found');\n DAO_V290_WINDOW=pack.window;\n DAO_V290_ROUTE_ROWS=(pack.routeRows||[]).map(x=>({...x,draws:(x.draws||[]).map(y=>({...y}))}));\n out.innerHTML=pack.html||'';\n out.onclick=(ev)=>{\n   const btn=ev.target.closest?.('.dao-pull-v295');\n   if(!btn)return;\n   ev.preventDefault();\n   const source=decodeURIComponent(btn.dataset.source||'');\n   const raw=Number(btn.dataset.raw||0);\n   const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw);\n   Promise.resolve(showDaoPullRouteV290(row?.firstDraw||'',raw,source,1)).catch(e=>{\n     const box=document.getElementById('daoPullRouteV290');\n     if(box)box.innerHTML='<div class="warn">최소루트 계산 오류: '+String(e&&e.message||e)+'</div>';\n     console.error(e);\n   });\n };\n}\n'''
if 'function renderDaoExchangeV296(' not in text:
    text=text.replace(anchor,helper+anchor,1)

# Guard both helpers as concrete function definitions, not just call sites.
if 'function daoV296Key(' not in text: raise SystemExit('daoV296Key definition missing in v3.22 baseline')
if 'function renderDaoExchangeV296(' not in text: raise SystemExit('renderDaoExchangeV296 definition still missing')
if 'renderDaoExchangeV296(pack);' not in text and 'renderDaoExchangeV296(DAO_V296_EXCHANGE_CACHE.pack)' not in text:
    raise SystemExit('renderer call missing')
if 'daoV296Key()' not in text: raise SystemExit('cache key call missing')

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.23','file':'Nangman_Integrated_Simulator_v3_23.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.23',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.23</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v323_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.23: restored renderDaoExchangeV296 and guarded exchange helpers')
