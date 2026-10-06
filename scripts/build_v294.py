from pathlib import Path
import re, base64, subprocess, json
SRC=Path('Nangman_Integrated_Simulator_v2_93.html'); DST=Path('Nangman_Integrated_Simulator_v2_94.html')
if not SRC.exists(): raise SystemExit('v2.93 source missing')
text=SRC.read_text(encoding='utf-8')
# Replace route function only.
a=text.find('function showDaoPullRouteV290('); b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route function boundary missing')
new_func=r'''function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 천장 이후 교체맥 표를 계산하세요.</div>';return}
 const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo&&x.weight<4), currentPrev=pre[pre.length-1]||null;
 if(!currentPrev){box.innerHTML='<div class="warn">현재 천장 직전 일반 자질을 찾지 못했습니다.</div>';return}
 const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 const target=row?.firstDraw||targetName||'';
 const slots=+QUAL[String(d.pityState.zizhi)]?.slots||0;
 const oneLockCost=(COST?.[slots]?.[1]??0);
 const candidates=[];
 // A) 중복 삭제: 뒤 원시맥을 천장 직전 위치로 당김.
 const needDel=Math.max(0,+sourceRaw-+currentPrev.rawNo);
 const dels=daoDeleteCandidatesV290(d);
 if(needDel===0)candidates.push({kind:'현재 위치',pills:0,html:'추가 잡맥 조작 없이 현재 천장 직전 위치입니다.'});
 else if(dels.length>=needDel){
   const chosen=dels.slice(0,needDel), total=chosen.reduce((s,x)=>s+x.pills,0);
   let html=`<b>중복 삭제 잡맥법</b> · ${needDel}개 생략 · 예상 <b>${total}단</b><div class="scroll"><table><thead><tr><th>순서</th><th>잠글 원시맥</th><th>삭제되는 중복맥</th><th>유지 세수</th><th>소모</th></tr></thead><tbody>`;
   chosen.forEach((x,i)=>html+=`<tr><td>${i+1}</td><td>#${x.lockRaw} ${x.name}</td><td>#${x.deleteRaw} ${x.name}</td><td>${x.washes}회</td><td>${x.pills}단</td></tr>`);
   html+='</tbody></table></div>';
   candidates.push({kind:'중복 삭제',pills:total,html});
 }
 // B) 직전 화면 잠금 보정: 원래 천장 직전 일반맥보다 1~slots-1 앞의 맥을 천장 직전으로 만든다.
 const back=+currentPrev.rawNo-(+sourceRaw);
 if(back>=1 && back<=Math.max(0,slots-1)){
   const total=back*oneLockCost;
   candidates.push({kind:'직전 화면 잠금',pills:total,html:`<b>직전 화면 잠금 보정</b> · 천장 직전 화면에서 <b>${back}칸 잠금</b> · 예상 <b>${total}단</b><br><span class="small">아무것도 잠그지 않으면 #${currentPrev.rawNo} ${currentPrev.name} 뒤에 천장이 옵니다. 직전 화면에서 ${back}개를 잠그면 새로 소비되는 일반맥이 ${back}개 줄어 <b>#${sourceRaw} ${sourceName}</b> 뒤에 천장이 오도록 앞당깁니다. 남지의 예시의 852→851 변화와 같은 방식입니다.</span>`});
 }
 if(!candidates.length){box.innerHTML=`<div class="warn"><b>${sourceName}</b> 기준 교체 1 = <b>${target}</b><br>현재 표 범위에서 확정 가능한 중복 삭제/직전 화면 잠금 경로를 찾지 못했습니다.</div>`;return}
 candidates.sort((x,y)=>x.pills-y.pills);
 const best=candidates[0];
 let h=`<div class="good"><b>${sourceName}</b> 기준 → 천장 후보 <b>${target}</b></div>`+
 `<div class="small" style="line-height:1.7;margin:6px 0">현재 천장 직전: #${currentPrev.rawNo} ${currentPrev.name}<br>선택 원시맥: #${sourceRaw} ${sourceName}<br>추천: <b>${best.kind}</b> · 예상 <b>${best.pills}단</b></div>`;
 h+=`<div class="card" style="padding:10px">${best.html}</div>`;
 if(candidates.length>1)h+=`<details style="margin-top:8px"><summary>다른 가능한 방법 보기</summary>${candidates.slice(1).map(c=>`<div class="card" style="padding:10px;margin-top:6px">${c.html}</div>`).join('')}</details>`;
 box.innerHTML=h;
}'''
text=text[:a]+new_func+text[b:]
# Change table interaction: raw-name cell clickable, exchange1 plain.
old="""h+=`<tr><td class=\"num\">${r.rawNo}</td><td class=\"num\">${r.wash}</td><td>${r.kind}</td><td class=\"${r.kind==='천장'?'q4':''}\"><b>${r.name}</b></td>`;\n     for(let i=0;i<15;i++){\n       const n=r.draws[i]?.name||'-';\n       if(i===0)h+=`<td class=\"q4\"><button type=\"button\" class=\"linkBtn dao-pull-v293\" data-target=\"${encodeURIComponent(n)}\" data-raw=\"${r.rawNo}\" data-source=\"${encodeURIComponent(r.name)}\">${n}</button></td>`;\n       else h+=`<td class=\"q4\">${n}</td>`;\n     }"""
new="""h+=`<tr><td class=\"num\">${r.rawNo}</td><td class=\"num\">${r.wash}</td><td>${r.kind}</td><td class=\"${r.kind==='천장'?'q4':''}\"><button type=\"button\" class=\"linkBtn dao-pull-v294\" data-raw=\"${r.rawNo}\" data-source=\"${encodeURIComponent(r.name)}\"><b>${r.name}</b></button></td>`;\n     for(let i=0;i<15;i++){const n=r.draws[i]?.name||'-';h+=`<td class=\"q4\">${n}</td>`;}"""
if old not in text: raise SystemExit('v293 row renderer missing')
text=text.replace(old,new,1)
text=text.replace("const btn=ev.target.closest?.('.dao-pull-v293');","const btn=ev.target.closest?.('.dao-pull-v294');",1)
text=text.replace("const target=decodeURIComponent(btn.dataset.target||'');\n     const source=decodeURIComponent(btn.dataset.source||'');\n     const raw=Number(btn.dataset.raw||0);\n     showDaoPullRouteV290(target,raw,source,1);","const source=decodeURIComponent(btn.dataset.source||'');\n     const raw=Number(btn.dataset.raw||0);\n     const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw);\n     showDaoPullRouteV290(row?.firstDraw||'',raw,source,1);",1)
text=text.replace('각 행의 <b>교체 1</b>만 잡맥법 대상입니다. 교체 1을 누르면 표 아래 <b>잡맥법 최소 세수단 경로</b> 칸에 결과가 표시됩니다. 교체 2~15는 참고용입니다.','각 행의 <b>원시맥</b>을 누르면 그 행의 <b>교체 1</b>을 천장 후보로 보고, 표 아래 <b>잡맥법 최소 세수단 경로</b> 칸에 결과를 표시합니다. 교체 1~15 값은 참고용입니다.',1)
text=text.replace('위 표에서 각 행의 <b>교체 1</b>을 누르면 여기에 계산 결과가 표시됩니다.','위 표에서 원하는 <b>원시맥</b>을 누르면 그 행의 교체 1을 천장 후보로 계산합니다.',1)
# version bump and stable loader
text=text.replace('v2.93','v2.94').replace('v2_93','v2_94'); text=re.sub(r'(?<![0-9])2\.93(?![0-9])','2.94',text)
text=re.sub(r'<script id="stable-root-url-v293">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>'); text=text[:he]+'''<script id="stable-root-url-v294">try{if(/Nangman_Integrated_Simulator_v2_94\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;';m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace').replace('v2.93','v2.94').replace('v2_93','v2_94'); inner=re.sub(r'(?<![0-9])2\.93(?![0-9])','2.94',inner)
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{base64.b64encode(inner.encode()).decode()}";'+text[m.end():]
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v2.94','file':'Nangman_Integrated_Simulator_v2_94.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.94',s);r.write_text(s,encoding='utf-8')
for x in ["sharedSaveText = await file.text()","JSON.parse(sharedSaveText)",'daoRawBeforeBtn.onclick=showDaoRawBeforeV288','dao-pull-v294','직전 화면 잠금 보정']:
    if x not in text: raise SystemExit('regression '+x)
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v294_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:1500])
print('built v2.94')
