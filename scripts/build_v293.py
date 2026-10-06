from pathlib import Path
import re, base64, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v2_92.html')
DST=Path('Nangman_Integrated_Simulator_v2_93.html')
if not SRC.exists(): raise SystemExit('v2.92 source missing')
text=SRC.read_text(encoding='utf-8')

# Narrow patch: only daomai function-2 interaction/result presentation.
# 1) Replace inline onclick renderer with data attributes. Only 교체 1 is interactive.
old='''for(let i=0;i<15;i++){\n       const n=r.draws[i]?.name||'-';\n       if(i===0)h+=`<td class="q4"><button type="button" class="linkBtn" onclick="showDaoPullRouteV290(${JSON.stringify(n)},${r.rawNo},${JSON.stringify(r.name)},1)">${n}</button></td>`;\n       else h+=`<td class="q4">${n}</td>`;\n     }'''
new='''for(let i=0;i<15;i++){\n       const n=r.draws[i]?.name||'-';\n       if(i===0)h+=`<td class="q4"><button type="button" class="linkBtn dao-pull-v293" data-target="${encodeURIComponent(n)}" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}">${n}</button></td>`;\n       else h+=`<td class="q4">${n}</td>`;\n     }'''
if old not in text: raise SystemExit('v2.92 교체1 renderer missing')
text=text.replace(old,new,1)

# 2) Make a permanent result card under the table and bind by event delegation after render.
old_tail='''h+='</tbody></table></div><div id="daoPullRouteV290" style="margin-top:12px"></div>';\n   daoExchangeWindowResult.innerHTML=h;'''
new_tail='''h+='</tbody></table></div>' +\n      '<section id="daoPullRouteBoxV293" class="card" style="margin-top:14px;padding:12px">' +\n      '<div style="font-weight:800;margin-bottom:8px">잡맥법 최소 세수단 경로</div>' +\n      '<div id="daoPullRouteV290" class="small">위 표에서 각 행의 <b>교체 1</b>을 누르면 여기에 계산 결과가 표시됩니다.</div>' +\n      '</section>';\n   daoExchangeWindowResult.innerHTML=h;\n   daoExchangeWindowResult.onclick=(ev)=>{\n     const btn=ev.target.closest?.('.dao-pull-v293');\n     if(!btn)return;\n     ev.preventDefault();\n     const target=decodeURIComponent(btn.dataset.target||'');\n     const source=decodeURIComponent(btn.dataset.source||'');\n     const raw=Number(btn.dataset.raw||0);\n     showDaoPullRouteV290(target,raw,source,1);\n   };'''
if old_tail not in text: raise SystemExit('v2.92 result tail missing')
text=text.replace(old_tail,new_tail,1)

# 3) Keep results in the dedicated box; do not depend on inline handler behavior.
text=text.replace("box.innerHTML=h;box.scrollIntoView({block:'nearest'});","box.innerHTML=h;",1)

# Update explanation to clearly point to the lower result box.
text=text.replace('각 행의 <b>교체 1</b>만 잡맥법 대상입니다. 교체 1을 누르면 그 맥을 천장맥으로 당기는 최소 세수단 경로를 계산합니다. 교체 2~15는 참고용입니다.',
                  '각 행의 <b>교체 1</b>만 잡맥법 대상입니다. 교체 1을 누르면 표 아래 <b>잡맥법 최소 세수단 경로</b> 칸에 결과가 표시됩니다. 교체 2~15는 참고용입니다.',1)

# Version bump only outside this focused interaction patch.
text=text.replace('v2.92','v2.93').replace('v2_92','v2_93')
text=re.sub(r'(?<![0-9])2\\.92(?![0-9])','2.93',text)

# Remove prior stable-root script and add v2.93 one; keep bootstrap architecture intact.
text=re.sub(r'<script id="stable-root-url-v292">.*?</script>\\s*','',text,flags=re.S)
head_end=text.lower().find('</head>')
if head_end<0: raise SystemExit('head end missing')
url_script='''<script id="stable-root-url-v293">try{if(/Nangman_Integrated_Simulator_v2_93\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''
text=text[:head_end]+url_script+text[head_end:]

# Embedded equipment version labels only, no behavior changes.
pat=r'const\\s+EQUIPMENT_HTML_B64\\s*=\\s*"([A-Za-z0-9+/=]+)"\\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace')
inner=inner.replace('v2.92','v2.93').replace('v2_92','v2_93')
inner=re.sub(r'(?<![0-9])2\\.92(?![0-9])','2.93',inner)
enc=base64.b64encode(inner.encode()).decode()
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{enc}";'+text[m.end():]

DST.write_text(text,encoding='utf-8')

# Keep permanent bootstrap generic; only latest.json changes each release.
index=Path('index.html').read_text(encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v2.93','file':'Nangman_Integrated_Simulator_v2_93.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\\s*v?[0-9.]+','현재 사이트 버전: v2.93',s);r.write_text(s,encoding='utf-8')

# Regression guards: preserve unrelated working features.
for x in ["const sharedSaveInput = document.getElementById('sharedSaveFile')","sharedSaveInput?.addEventListener('change'","sharedSaveText = await file.text()","JSON.parse(sharedSaveText)"]:
    if x not in text: raise SystemExit('save loader regression: '+x)
for x in ['daoRawBeforeBtn.onclick=showDaoRawBeforeV288','daoExchangeWindowBtn.onclick=showDaoExchangeWindowV288','showDaoPullRouteV290']:
    if x not in text: raise SystemExit('daomai regression: '+x)
for x in ['dao-pull-v293','daoPullRouteBoxV293','daoExchangeWindowResult.onclick','잡맥법 최소 세수단 경로']:
    if x not in text: raise SystemExit('v2.93 interaction missing '+x)
if 'onclick="showDaoPullRouteV290' in text: raise SystemExit('old inline click handler still present')
for x in ["latest.json?ts=","cache:'no-store'","location.replace(u)"]:
    if x not in index: raise SystemExit('bootstrap regression '+x)
# JS syntax checks.
for i,js in enumerate(re.findall(r'<script\\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v293_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(f'app JS syntax error {i}: {cp.stderr[:1500]}')
if '<title>낭만강호 통합 시뮬레이터 v2.93</title>' not in text[:10000]: raise SystemExit('title mismatch')
print('built v2.93 daomai click fix')
