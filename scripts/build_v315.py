from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_14.html')
DST=Path('Nangman_Integrated_Simulator_v3_15.html')
if not SRC.exists(): raise SystemExit('v3.14 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.14','v3.15').replace('v3_14','v3_15')
text=re.sub(r'(?<![0-9])3\.14(?![0-9])','3.15',text)
text=re.sub(r'<script id="stable-root-url-v314">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v315">try{if(/Nangman_Integrated_Simulator_v3_15\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Replace only the route-search function. Table/UI from v3.14 stays intact.
a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
new_route=r'''async function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 자맥 구간별 교체맥 표를 계산하세요.</div>';return}
 const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!row){box.innerHTML='<div class="warn">선택한 원시맥 행을 찾지 못했습니다.</div>';return}
 if(!SAVE||!roleObj()){box.innerHTML='<div class="warn">세이브와 캐릭터를 먼저 선택하세요.</div>';return}
 const targetSeed=+(row.luckStart??row.seedAfter??0);
 if(!targetSeed){box.innerHTML='<div class="warn">선택 행의 목표 seed를 찾지 못했습니다.</div>';return}

 let base=unlockAll(stateFromSave(SAVE,roleObj(),+vipSel.value,rawCalcZizhi()));
 base.bag_pills=999999999;base.has_bag_pills=true;
 const slots=+QUAL[String(base.zizhi)]?.slots||0;
 if(slots<=0){box.innerHTML='<div class="warn">열린 슬롯이 없습니다.</div>';return}

 box.innerHTML=`<div class="warn"><b>${sourceName}</b> 목표 seed <b>${targetSeed}</b> 최소 세수단 경로 탐색 중...<br><span class="small">천장에 가까운 후보부터 잠금 구간만 실제 재생하고, 잠금을 푼 뒤 기본 세수로 천장까지 진행했을 때 Born seed가 정확히 맞는지 검사합니다.</span></div>`;
 await uiYield();

 function unlocked(st){const x=dc(st);x.talents=(x.talents||[]).map(t=>({...t,locked:false}));return x}
 function lockCombos(n){
   const out=[];
   for(let m=1;m<(1<<n);m++){
     const idx=[];for(let i=0;i<n;i++)if(m&(1<<i))idx.push(i);
     if(idx.length<slots)out.push(idx);
   }
   // Cheaper/simpler lock counts first.
   out.sort((a,b)=>a.length-b.length);
   return out;
 }
 function probePitySeed(st,max=500){
   let s=unlocked(st);
   for(let i=0;i<max;i++){
     const before=dc(s),tr=washOnce(before);s=tr.state;
     if(tr.result?.was_pity)return {seed:+before.seed,state:dc(s),washes:i+1};
     if(tr.result?.got_gold)return null;
   }
   return null;
 }

 // Baseline no-lock pages up to the default pity. These are candidate lock-start pages.
 const pages=[];let scan=unlocked(base),guard=3000;
 while(guard-->0){
   const tr=washOnce(scan);scan=tr.state;
   if(tr.result?.got_gold)break;
   pages.push(unlocked(scan));
 }
 if(guard<=0){box.innerHTML='<div class="warn">기본 천장 이전 상태 재현 한도를 초과했습니다.</div>';return}

 let best=null,checked=0,probeCount=0;
 const MAX_NEAR_PAGES=Math.min(140,pages.length),MAX_HOLD=24;

 // 1) Closest-to-pity first to obtain a cheap upper bound quickly.
 // 2) After a route is found, farther candidates are only explored while they can beat that cost.
 for(let dist=0;dist<MAX_NEAR_PAGES;dist++){
   const pg=pages[pages.length-1-dist];if(!pg)break;
   const n=Math.min(slots,(pg.talents||[]).length);
   const combos=lockCombos(n);
   for(const idxs of combos){
     const lockIds=idxs.map(i=>+pg.talents[i].id);
     let st=dc(pg),lockCost=0,path=[];
     st.talents=st.talents.map(t=>({...t,locked:lockIds.includes(+t.id)}));
     if(st.talents.filter(t=>t.locked).length!==idxs.length)continue;
     for(let hold=1;hold<=MAX_HOLD;hold++){
       let tr,before=dc(st);try{tr=washOnce(before)}catch(e){break}
       st=tr.state;const edge=+tr.result.pills_used||0;lockCost+=edge;checked++;
       path.push({locks:lockIds.map(id=>({id,name:nm(id)})),pills:edge,beforeSeed:+before.seed,afterSeed:+st.seed,talents:(tr.result.talents||[]).map(t=>nm(t.id))});
       if(tr.result?.got_gold)break;

       // If this partial route already cannot beat the best known cost, stop extending it.
       if(best && lockCost>best.cost)break;

       const probe=probePitySeed(st);probeCount++;
       if(probe && +probe.seed===targetSeed){
         const cand={cost:lockCost,dist,hold,lockIds:dc(lockIds),path:dc(path),probe,checked,probeCount};
         if(!best || cand.cost<best.cost || (cand.cost===best.cost && cand.dist<best.dist))best=cand;
         break;
       }

       // Keep the SAME actual locked IDs for the next held wash.
       st.talents=st.talents.map(t=>({...t,locked:lockIds.includes(+t.id)}));
     }
   }
   if(dist%8===7){
     box.innerHTML=`<div class="warn">천장 가까운 순서로 탐색 중 · ${dist+1}/${MAX_NEAR_PAGES}회차 범위 · 잠금 후보 ${checked.toLocaleString()}개${best?` · 현재 최저 ${best.cost}단`:''}</div>`;
     await uiYield();
   }

   // Once we have reached a reasonable near-pity band and found a route, continue only far enough
   // to prove no cheaper 1-step/low-cost candidate exists. Cost pruning above makes this cheap.
   if(best && dist>=31){
     const minEdge=Math.min(...Object.values(COST?.[slots]||{}).filter(x=>+x>0).map(Number));
     if(best.cost<=minEdge)break;
   }
 }

 if(!best){
   box.innerHTML=`<div class="warn"><b>${sourceName}</b> 목표 seed ${targetSeed}에 대해 천장 가까운 ${MAX_NEAR_PAGES}개 회차에서 잠금 후보 ${checked.toLocaleString()}개를 검사했지만 경로를 찾지 못했습니다.<br>틀린 장기 잠금 경로를 임의로 표시하지 않습니다.</div>`;
   return;
 }

 const lockNames=best.lockIds.map(id=>nm(id)).join(' + ');
 let h=`<div class="good"><b>목표 seed 도달 최소비용 경로</b> · 목표 seed <b>${targetSeed}</b> · 추가 잠금 세수 소모 <b>${best.cost.toLocaleString()}단</b></div>`+
   `<div class="small" style="line-height:1.7;margin:6px 0">천장에서 ${best.dist}회차 앞 페이지에서 시작 · 잠금 유지 ${best.hold}회 · 검사 후보 ${checked.toLocaleString()}개<br>`+
   `잠금 구간 종료 후 <b>잠금 해제</b> → 기본 세수로 천장까지 진행 · 천장 직전 Born seed <b>${best.probe.seed}</b> 확인</div>`;
 h+='<div class="card" style="padding:10px"><b>실행 순서</b><ol style="margin:7px 0 0 20px;padding:0">';
 h+=`<li><b>${lockNames}</b> 잠금</li>`;
 for(let i=0;i<best.path.length;i++){
   const p=best.path[i];
   h+=`<li>잠금 유지 ${i+1}회차 세수 · ${p.pills}단 · Born ${p.beforeSeed} → ${p.afterSeed}<br><span class="small">결과: ${p.talents.join(' · ')}</span></li>`;
 }
 h+=`<li><b>잠금 해제</b> 후 기본 세수 <b>${best.probe.washes}회</b> → 천장 직전 Born seed <b>${best.probe.seed}</b> 도달</li>`;
 h+='</ol></div>';
 box.innerHTML=h;
}'''
text=text[:a]+new_route+text[b:]

# Guards: keep v3.14 UI changes, remove the bad "hold lock until pity" success model.
route=text[a:a+len(new_route)]
for x in ['probePitySeed(st)','잠금 해제','lockIds.includes(+t.id)','추가 잠금 세수 소모','천장 가까운 순서로 탐색 중']:
 if x not in route: raise SystemExit('v3.15 guard missing: '+x)
if 'goal(before,st,tr)' in route or 'tr.result.was_pity && +before.seed===targetSeed' in route:
 raise SystemExit('old hold-until-pity goal remains')

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.15','file':'Nangman_Integrated_Simulator_v3_15.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.15',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.15</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v315_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.15: short lock episode -> unlock -> probe pity seed, with cost pruning')
