from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_01.html')
DST=Path('Nangman_Integrated_Simulator_v3_02.html')
if not SRC.exists(): raise SystemExit('v3.01 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.01','v3.02').replace('v3_01','v3_02')
text=re.sub(r'(?<![0-9])3\.01(?![0-9])','3.02',text)
text=re.sub(r'<script id="stable-root-url-v301">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v302">try{if(/Nangman_Integrated_Simulator_v3_02\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Replace only the route renderer/search. v3.01 pre-pity #600 table remains unchanged.
start=text.find('function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){')
end=text.find('\nasync function showDaoExchangeWindowV288(){',start)
if start<0 or end<0: raise SystemExit('showDaoPullRouteV290 block not found')
new_func=r'''function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 원시 #600~천장 직전 교체맥 표를 계산하세요.</div>';return}
 const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!row){box.innerHTML='<div class="warn">선택한 원시맥 행을 찾지 못했습니다.</div>';return}
 const target=row.firstDraw||targetName||'';
 const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo&&x.weight<4).map(x=>({...x}));
 const currentPrev=pre[pre.length-1]||null;
 if(!currentPrev){box.innerHTML='<div class="warn">현재 천장 직전 일반 자질을 찾지 못했습니다.</div>';return}
 const targetRaw=+sourceRaw;
 const tail=pre.filter(x=>+x.rawNo>targetRaw);
 let h=`<div class="good"><b>${sourceName}</b> 기준 → 천장 후보 <b>${target}</b></div>`+
 `<div class="small" style="line-height:1.7;margin:6px 0">기본 천장: <b>#${d.firstPity.rawNo} ${d.firstPity.name}</b><br>현재 천장 직전 일반맥: #${currentPrev.rawNo} ${currentPrev.name}<br>선택한 천장 전 일반 원시맥: #${sourceRaw} ${sourceName}<br>직접 없애야 할 뒤쪽 원시맥: <b>${tail.length}개</b></div>`;
 if(!tail.length){box.innerHTML=h+'<div class="good">이미 이 원시맥이 천장 직전입니다. 추가 잡맥 조작이 필요 없습니다.</div>';return}

 const slots=+QUAL[String(d.pityState.zizhi)]?.slots||0;
 const oneLockCost=+(COST?.[slots]?.[1]??0);
 if(slots<=0){box.innerHTML=h+'<div class="warn">계산용 열린 칸 수를 확인할 수 없습니다.</div>';return}

 // v3.02: branch-search on the reconstructed slot table.
 // A deletion shifts every later row left, so every branch is regrouped before the next candidate search.
 // We do NOT greedily force the nearest duplicate; earlier duplicate pairs are explored too.
 const byRaw=new Map(pre.map(x=>[+x.rawNo,x]));
 const allRaw=pre.map(x=>+x.rawNo);
 const targetTailSet=new Set(tail.map(x=>+x.rawNo));

 function remaining(delSet){return pre.filter(x=>!delSet.has(+x.rawNo));}
 function grouped(delSet){
   const a=remaining(delSet), gs=[];
   for(let i=0;i<a.length;i+=slots)gs.push(a.slice(i,i+slots));
   return gs;
 }
 function goal(delSet){
   for(const r of targetTailSet)if(!delSet.has(r))return false;
   return true;
 }
 function stateKey(delSet){return [...delSet].sort((a,b)=>a-b).join(',')}
 function candidates(delSet){
   const gs=grouped(delSet), out=[];
   for(let g=1;g<gs.length;g++){
     const prev=gs[g-1],cur=gs[g];
     for(const c of cur){
       if(+c.rawNo===targetRaw)continue;
       const matches=prev.filter(p=>+p.id===+c.id);
       for(const p of matches){
         out.push({lockRaw:+p.rawNo,lockWash:g,deleteRaw:+c.rawNo,deleteWash:g+1,id:+c.id,name:c.name});
       }
     }
   }
   // Explore target-tail deletions first for speed, but keep ALL earlier branches in the queue.
   out.sort((a,b)=>{
     const at=a.deleteRaw>targetRaw?0:1,bt=b.deleteRaw>targetRaw?0:1;
     return at-bt || b.deleteRaw-a.deleteRaw || b.lockRaw-a.lockRaw;
   });
   return out;
 }

 const maxDepth=Math.min(18,tail.length+8);
 const queue=[{del:new Set(),steps:[]}];
 const seen=new Map([["",0]]);
 let best=null,expanded=0;
 while(queue.length&&expanded<60000){
   const cur=queue.shift();expanded++;
   if(goal(cur.del)){best=cur;break}
   if(cur.steps.length>=maxDepth)continue;
   for(const c of candidates(cur.del)){
     if(cur.del.has(c.deleteRaw))continue;
     // Never delete the selected target itself. Earlier rows MAY be deleted because they can change grouping.
     const nd=new Set(cur.del);nd.add(c.deleteRaw);
     const key=stateKey(nd),depth=cur.steps.length+1;
     if(seen.has(key)&&seen.get(key)<=depth)continue;
     seen.set(key,depth);
     queue.push({del:nd,steps:cur.steps.concat([{...c,deletedBeforeTarget:c.deleteRaw<targetRaw}])});
   }
 }

 if(!best){
   h+=`<div class="warn">3칸 테이블을 삭제할 때마다 다시 구성해 <b>${expanded.toLocaleString()}개 상태</b>를 탐색했지만, 현재 확인 가능한 인접 중복 규칙만으로는 #${sourceRaw} ${sourceName}을 천장 직전까지 당기는 확정 경로를 찾지 못했습니다.<br>추정 경로는 표시하지 않습니다.</div>`;
   box.innerHTML=h;return;
 }

 const extra=best.steps.filter(s=>s.deletedBeforeTarget).length;
 const total=best.steps.length*oneLockCost;
 h+=`<div class="good"><b>확정 최소 단계 경로</b> · 잠금 세수 <b>${best.steps.length}회</b> · 추가 소모 <b>${total}단</b>`+
    (extra?`<br><span class="small">목표보다 앞쪽에서 먼저 지우는 단계 ${extra}회 포함. 앞쪽 삭제로 이후 3칸 경계를 재배치한 뒤 뒤쪽 중복을 다시 찾았습니다.</span>`:'')+
    `</div>`;
 h+='<div class="card" style="padding:10px;margin-top:8px"><b>실행 순서</b><ol style="margin:7px 0 0 20px;padding:0">';
 for(let i=0;i<best.steps.length;i++){
   const s=best.steps[i];
   h+=`<li style="margin:5px 0"><b>#${s.lockRaw} ${s.name}</b> 잠금 → 1회 세수 → 재구성된 다음 3칸에서 <b>#${s.deleteRaw} ${s.name}</b> 중복 제거 → 잠금 해제${s.deletedBeforeTarget?' <span class="small">(목표보다 앞쪽 선행 재배치)</span>':''}</li>`;
 }
 h+='</ol></div>';
 const deleted=[...best.del].sort((a,b)=>a-b).map(n=>`#${n} ${byRaw.get(n)?.name||''}`).join(', ');
 h+=`<div class="small" style="line-height:1.7;margin-top:8px">삭제된 원시맥: ${deleted}<br>`+
    `최종 목표: <b>#${sourceRaw} ${sourceName}</b>이 남은 일반맥의 마지막 행이 되어 다음 천장이 <b>${target}</b>으로 계산됩니다.<br>`+
    `탐색 방식: 각 삭제 직후 전체 남은 원시맥을 ${slots}칸 단위로 다시 묶고, 새로 생긴 이전 회차↔다음 회차 중복을 다시 탐색했습니다. 천장에 가까운 후보만 고정하지 않습니다.</div>`;
 box.innerHTML=h;
}'''
text=text[:start]+new_func+text[end:]

# Update explanatory text only; calculation table itself stays v3.01 behavior.
text=text.replace('기존 잡맥법 최소 세수단 경로를 그대로 계산합니다.','삭제마다 3칸 테이블을 재구성하는 분기 탐색으로 최소 세수단 경로를 계산합니다.')
text=text.replace('기존 잡맥법 최소 세수단 경로 계산을 그대로 사용합니다.','삭제마다 3칸 테이블을 다시 구성해 앞쪽 중복까지 포함한 최소 경로를 탐색합니다.')
text=text.replace('그 원시맥을 천장 직전으로 당기는 기존 최소소모 루트를 계산합니다.','그 원시맥을 천장 직전으로 당기는 최소소모 루트를 전체 분기 탐색합니다.')

for x in [
 '1. 천장 전 모든 원시맥 보기',
 '2. 원시 #600~천장 직전 교체맥 보기',
 'function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol)',
 'const maxDepth=Math.min(18,tail.length+8);',
 '앞쪽 삭제로 이후 3칸 경계를 재배치',
 'if(+c.rawNo===targetRaw)continue;',
 'daoRawBeforeBtn.onclick=showDaoRawBeforeV288',
 'daoExchangeWindowBtn.onclick=showDaoExchangeWindowV288'
]:
 if x not in text: raise SystemExit('v3.02 guard missing: '+x)
if '현재는 첫 삭제 이후 테이블을 다시 계산하지 않고는 확정 경로로 표시하지 않습니다.' in text:
 raise SystemExit('old incomplete multi-delete warning remains')

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.02','file':'Nangman_Integrated_Simulator_v3_02.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.02',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.02</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v302_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.02: exhaustive regrouping route search; earlier duplicate branches included')
