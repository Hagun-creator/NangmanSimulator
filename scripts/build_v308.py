from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_07.html')
DST=Path('Nangman_Integrated_Simulator_v3_08.html')
if not SRC.exists(): raise SystemExit('v3.07 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.07','v3.08').replace('v3_07','v3_08')
text=re.sub(r'(?<![0-9])3\.07(?![0-9])','3.08',text)
text=re.sub(r'<script id="stable-root-url-v307">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v308">try{if(/Nangman_Integrated_Simulator_v3_08\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

start=text.find('function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){')
end=text.find('\nasync function showDaoExchangeWindowV288(){',start)
if start<0 or end<0: raise SystemExit('route function not found')
new_func=r'''function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 원시 #700~천장 직전 교체맥 표를 계산하세요.</div>';return}
 const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!row){box.innerHTML='<div class="warn">선택한 원시맥 행을 찾지 못했습니다.</div>';return}
 const target=row.firstDraw||targetName||'';
 const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo&&x.weight<4).map(x=>({...x}));
 const currentPrev=pre[pre.length-1]||null;
 if(!currentPrev){box.innerHTML='<div class="warn">현재 천장 직전 일반 자질을 찾지 못했습니다.</div>';return}
 const targetRaw=+sourceRaw;
 const needDel=Math.max(0,(+currentPrev.rawNo)-targetRaw);
 let h=`<div class="good"><b>${sourceName}</b> 기준 → 천장 후보 <b>${target}</b></div>`+
 `<div class="small" style="line-height:1.7;margin:6px 0">기본 천장: <b>#${d.firstPity.rawNo} ${d.firstPity.name}</b><br>현재 천장 직전 일반맥: #${currentPrev.rawNo} ${currentPrev.name}<br>선택한 천장 전 일반 원시맥: #${sourceRaw} ${sourceName}<br>필요한 일반맥 생략 수: <b>${needDel}개</b></div>`;
 if(needDel<=0){box.innerHTML=h+'<div class="good">이미 필요한 원시맥 수에 도달해 추가 잡맥 조작이 필요 없습니다.</div>';return}

 const slots=+QUAL[String(d.pityState.zizhi)]?.slots||0;
 const oneLockCost=+(COST?.[slots]?.[1]??0);
 if(slots<=0){box.innerHTML=h+'<div class="warn">계산용 열린 칸 수를 확인할 수 없습니다.</div>';return}

 const deleted=new Set();
 const steps=[];
 function remaining(){return pre.filter(x=>!deleted.has(+x.rawNo));}
 function grouped(){
   const a=remaining(),gs=[];
   for(let i=0;i<a.length;i+=slots)gs.push(a.slice(i,i+slots));
   return gs;
 }
 function nearestCandidate(){
   const gs=grouped();
   // Every successful duplicate deletion reduces the total accepted normal-raw count by one.
   // Search closest to pity first, regroup after each deletion, and stop as soon as needDel deletions succeed.
   for(let g=gs.length-1;g>=1;g--){
     const prev=gs[g-1];
     const cur=[...gs[g]].sort((a,b)=>b.rawNo-a.rawNo);
     for(const c of cur){
       if(+c.rawNo===targetRaw)continue;
       const matches=[...prev].filter(p=>+p.id===+c.id).sort((a,b)=>b.rawNo-a.rawNo);
       if(matches.length)return {lock:matches[0],del:c,group:g};
     }
   }
   return null;
 }

 while(steps.length<needDel){
   const c=nearestCandidate();
   if(!c)break;
   deleted.add(+c.del.rawNo);
   steps.push({lockRaw:+c.lock.rawNo,deleteRaw:+c.del.rawNo,name:c.del.name});
 }

 if(steps.length<needDel){
   h+=`<div class="warn">천장에 가까운 중복부터 재구성했지만 <b>${steps.length}/${needDel}개</b>까지만 실제 중복 제거가 가능했습니다. 필요한 ${needDel}개 제거를 완성할 다음 중복을 찾지 못했습니다.</div>`;
   if(steps.length)h+='<div class="small" style="margin-top:8px">확인된 단계: '+steps.map((s,i)=>`${i+1}) #${s.lockRaw} ${s.name} 잠금 → #${s.deleteRaw} ${s.name} 제거`).join(' / ')+'</div>';
   box.innerHTML=h;return;
 }

 const beforeCount=pre.length;
 const afterCount=beforeCount-steps.length;
 const total=steps.length*oneLockCost;
 h+=`<div class="good"><b>잡맥법 ${needDel}개 제거 성공</b> · 총 일반 원시맥 <b>${beforeCount} → ${afterCount}개</b> · 잠금 세수 <b>${steps.length}회</b> · 추가 소모 <b>${total}단</b></div>`;
 h+='<div class="card" style="padding:10px;margin-top:8px"><b>실행 순서</b><ol style="margin:7px 0 0 20px;padding:0">';
 for(const s of steps){
   h+=`<li style="margin:5px 0"><b>#${s.lockRaw} ${s.name}</b> 잠금 → 1회 세수 → 중복 <b>#${s.deleteRaw} ${s.name}</b> 제거 → 잠금 해제</li>`;
 }
 h+='</ol></div>';
 h+=`<div class="small" style="line-height:1.7;margin-top:8px">판정 기준은 특정 #${targetRaw+1}, #${targetRaw+2} 원시맥을 직접 지우는 것이 아니라, <b>천장 전 전체 일반 원시맥에서 실제 중복 제거가 ${needDel}회 발생했는지</b>입니다.<br>각 제거 직후 남은 원시맥을 ${slots}칸 단위로 다시 묶고, 다시 천장에 가장 가까운 중복 1개를 찾아 다음 단계로 사용합니다.</div>`;
 box.innerHTML=h;
}'''
text=text[:start]+new_func+text[end:]

for x in [
 '2. 원시 #700~천장 직전 교체맥 보기',
 'sort((a,b)=>a.rawNo-b.rawNo)',
 'const needDel=Math.max(0,(+currentPrev.rawNo)-targetRaw);',
 '잡맥법 ${needDel}개 제거 성공',
 'steps.length<needDel',
 '천장 전 전체 일반 원시맥에서 실제 중복 제거가 ${needDel}회 발생했는지',
 "showDaoPullRouteV290(row?.firstDraw||'',raw,source,1);"
]:
 if x not in text: raise SystemExit('v3.08 guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.08','file':'Nangman_Integrated_Simulator_v3_08.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md')
s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.08',s)
r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.08</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v308_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.08: route success is total duplicate-removal count; nearest-first regrouping stops at needDel')
