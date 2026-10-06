from pathlib import Path
import re, base64, subprocess, json
SRC=Path('Nangman_Integrated_Simulator_v2_94.html'); DST=Path('Nangman_Integrated_Simulator_v2_95.html')
if not SRC.exists(): raise SystemExit('v2.94 source missing')
text=SRC.read_text(encoding='utf-8')

# 1) Replace duplicate candidate logic with conservative, verified adjacent-page collisions only.
a=text.find('function daoDeleteCandidatesV290(d){'); b=text.find('\nfunction showDaoPullRouteV290(',a)
if a<0 or b<0: raise SystemExit('duplicate candidate boundary missing')
new_dup=r'''function daoDeleteCandidatesV295(d){
 const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo && x.weight<4);
 const by=new Map();
 for(const x of pre){if(!by.has(x.id))by.set(x.id,[]);by.get(x.id).push(x)}
 const slots=+QUAL[String(d.pityState.zizhi)]?.slots||0;
 const oneLockCost=(COST?.[slots]?.[1]??0);
 const out=[];
 for(const arr of by.values()){
   for(let j=1;j<arr.length;j++){
     const prev=arr[j-1], del=arr[j];
     // Only accept the article's directly verifiable case:
     // previous copy is in the immediately preceding wash/table and is held for one roll.
     if(+del.wash!==+prev.wash+1)continue;
     out.push({id:del.id,name:del.name,lockRaw:prev.rawNo,lockWash:prev.wash,deleteRaw:del.rawNo,deleteWash:del.wash,washes:1,pills:oneLockCost});
   }
 }
 // User preference: nearest deletable duplicate to pity first; pill cost is identical for one-lock/one-roll candidates.
 return out.sort((a,b)=>b.deleteRaw-a.deleteRaw || a.pills-b.pills);
}'''
text=text[:a]+new_dup+text[b:]

# 2) Replace route function. Pity row is never a target. General rows use normal-step after pity, not rawNo gap.
a=text.find('function showDaoPullRouteV290('); b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
new_route=r'''function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 천장 이후 교체맥 표를 계산하세요.</div>';return}
 const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!row||row.kind==='천장'){
   box.innerHTML='<div class="warn"><b>기본 천장맥</b>은 잡맥법 선택 대상이 아닙니다. 아무 조작 없이 나오는 천장 결과입니다.</div>';return;
 }
 const target=row.firstDraw||targetName||'';
 const needDel=+row.shift||0;
 const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo&&x.weight<4), currentPrev=pre[pre.length-1]||null;
 if(!currentPrev){box.innerHTML='<div class="warn">현재 천장 직전 일반 자질을 찾지 못했습니다.</div>';return}
 const cand=daoDeleteCandidatesV295(d);
 let h=`<div class="good"><b>${sourceName}</b> 기준 → 교체 1 천장 후보 <b>${target}</b></div>`+
 `<div class="small" style="line-height:1.7;margin:6px 0">기본 천장: <b>#${d.firstPity.rawNo} ${d.firstPity.name}</b> (클릭 대상 아님)<br>현재 천장 직전 일반맥: #${currentPrev.rawNo} ${currentPrev.name}<br>선택한 천장 이후 일반 원시맥: #${sourceRaw} ${sourceName}<br>필요한 일반맥 생략 수: <b>${needDel}개</b> <span class="small">(천장 자맥은 원시 일반맥 순번에서 제외)</span></div>`;
 if(needDel<=0){box.innerHTML=h+'<div class="warn">기본 천장 행은 변경 대상이 아닙니다.</div>';return}
 if(needDel===1){
   if(!cand.length){box.innerHTML=h+'<div class="warn">천장 전 구간에서 한 번 잠금으로 확정 가능한 인접 테이블 중복쌍을 찾지 못했습니다.</div>';return}
   const x=cand[0];
   h+=`<div class="card" style="padding:10px"><b>확정 가능한 1회 잡맥 생략</b> · 예상 <b>${x.pills}단</b><br><span class="small">#${x.lockRaw} ${x.name}을 잠그고 1회 세수 → 다음 테이블의 #${x.deleteRaw} ${x.name}이 동일 자질 충돌로 삭제 → 잠금 해제. 천장에 가장 가까운 확정 중복쌍을 우선 선택했습니다.</span></div>`;
   box.innerHTML=h;return;
 }
 // Multi-deletion changes later table boundaries. Do not pretend independent pairs can simply be stacked.
 h+=`<div class="warn"><b>${needDel}개 연쇄 생략</b>이 필요합니다. v2.94처럼 독립 중복쌍을 비용순으로 ${needDel}개 골라 합치는 방식은 실제 테이블 경계를 바꾸므로 잘못될 수 있어 제거했습니다.<br>현재는 첫 삭제 이후 테이블을 다시 계산하지 않고는 확정 경로로 표시하지 않습니다.</div>`;
 if(cand.length){
   h+='<div class="small" style="margin-top:8px">첫 단계로 사용 가능한 가장 가까운 확정 중복: '+`#${cand[0].lockRaw} ${cand[0].name} 잠금 → #${cand[0].deleteRaw} ${cand[0].name} 삭제`+'</div>';
 }
 box.innerHTML=h;
}'''
text=text[:a]+new_route+text[b:]

# 3) Fix table generation: keep pity as a visual baseline only, blank its exchange cells, and assign shift=1..N to ordinary rows.
old="""DAO_V290_ROUTE_ROWS=rows.map(r=>({...r,firstDraw:r.draws[0]?.name||''}));"""
new="""let normalShift=0;\n   DAO_V290_ROUTE_ROWS=rows.map(r=>{\n     if(r.kind==='천장')return {...r,firstDraw:'',shift:0};\n     normalShift++;return {...r,firstDraw:r.draws[0]?.name||'',shift:normalShift};\n   });"""
if old not in text: raise SystemExit('route rows assignment missing')
text=text.replace(old,new,1)

oldrow="""h+=`<tr><td class=\"num\">${r.rawNo}</td><td class=\"num\">${r.wash}</td><td>${r.kind}</td><td class=\"${r.kind==='천장'?'q4':''}\"><button type=\"button\" class=\"linkBtn dao-pull-v294\" data-raw=\"${r.rawNo}\" data-source=\"${encodeURIComponent(r.name)}\"><b>${r.name}</b></button></td>`;\n     for(let i=0;i<15;i++){const n=r.draws[i]?.name||'-';h+=`<td class=\"q4\">${n}</td>`;}"""
newrow="""if(r.kind==='천장'){\n       h+=`<tr><td class=\"num\">${r.rawNo}</td><td class=\"num\">${r.wash}</td><td>기본 천장</td><td class=\"q4\"><b>${r.name}</b><div class=\"small\">조작 없음 · 클릭 불가</div></td>`;\n       for(let i=0;i<15;i++)h+=`<td class=\"muted\">-</td>`;\n     }else{\n       const rr=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+r.rawNo);\n       h+=`<tr><td class=\"num\">${r.rawNo}</td><td class=\"num\">${r.wash}</td><td>원시 · 생략 ${rr?.shift||'?'}개</td><td><button type=\"button\" class=\"linkBtn dao-pull-v295\" data-raw=\"${r.rawNo}\" data-source=\"${encodeURIComponent(r.name)}\"><b>${r.name}</b></button></td>`;\n       for(let i=0;i<15;i++){const n=r.draws[i]?.name||'-';h+=`<td class=\"q4\">${n}</td>`;}\n     }"""
if oldrow not in text: raise SystemExit('v294 row renderer missing')
text=text.replace(oldrow,newrow,1)
text=text.replace("const btn=ev.target.closest?.('.dao-pull-v294');","const btn=ev.target.closest?.('.dao-pull-v295');",1)

text=text.replace('각 행의 <b>원시맥</b>을 누르면 그 행의 <b>교체 1</b>을 천장 후보로 보고, 표 아래 <b>잡맥법 최소 세수단 경로</b> 칸에 결과를 표시합니다. 교체 1~15 값은 참고용입니다.','<b>기본 천장</b> 행은 조작 없이 나오는 결과라 클릭할 수 없습니다. 그 다음 <b>일반 원시맥</b> 행부터 클릭 가능하며, 천장 자맥을 제외한 일반맥 기준으로 생략 1개, 2개…를 다시 계산합니다. 각 행의 교체 1~15는 참고용입니다.',1)

# 4) Remove misleading direct-lock candidate text from selected future-row route; this mechanism is distinct and was never actually reachable in v2.94.
text=text.replace('직전 화면 잠금 보정','직전 화면 잠금 보정(선택행 경로와 별도 규칙)')

# 5) Version bump, keep permanent bootstrap architecture.
text=text.replace('v2.94','v2.95').replace('v2_94','v2_95'); text=re.sub(r'(?<![0-9])2\.94(?![0-9])','2.95',text)
text=re.sub(r'<script id="stable-root-url-v294">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>');
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v295">try{if(/Nangman_Integrated_Simulator_v2_95\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;';m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace').replace('v2.94','v2.95').replace('v2_94','v2_95'); inner=re.sub(r'(?<![0-9])2\.94(?![0-9])','2.95',inner)
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{base64.b64encode(inner.encode()).decode()}";'+text[m.end():]
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v2.95','file':'Nangman_Integrated_Simulator_v2_95.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.95',s);r.write_text(s,encoding='utf-8')

# Regression guards.
for x in ["sharedSaveText = await file.text()","JSON.parse(sharedSaveText)",'daoRawBeforeBtn.onclick=showDaoRawBeforeV288','dao-pull-v295','daoDeleteCandidatesV295','기본 천장','shift:normalShift']:
    if x not in text: raise SystemExit('regression '+x)
if 'dao-pull-v294' in text: raise SystemExit('old clickable selector remains')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v295_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:1500])
if '<title>낭만강호 통합 시뮬레이터 v2.95</title>' not in text[:10000]: raise SystemExit('title mismatch')
print('built v2.95')
