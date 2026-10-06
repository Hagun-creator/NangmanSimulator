from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_27.html')
DST=Path('Nangman_Integrated_Simulator_v3_28.html')
if not SRC.exists(): raise SystemExit('v3.27 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.27','v3.28').replace('v3_27','v3_28')
text=re.sub(r'(?<![0-9])3\.27(?![0-9])','3.28',text)
text=re.sub(r'<script id="stable-root-url-v327">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v328">try{if(/Nangman_Integrated_Simulator_v3_28\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]
start=route.find(' outer:{\n // 위치/생략 N is a PRIORITY HINT')
end=route.find('\n if(!best){',start)
if start<0 or end<0: raise SystemExit('v3.27 engine block missing')

new=r''' outer:{
 // v3.28 indexed daomai/kamek engine.
 // Build an occurrence index first; do NOT brute-force every page x mask x hold combination.
 const targetSkip=Math.max(0,targetShift);
 const baselineCost=targetSkip>0?targetSkip*4:0;
 const occById=new Map();
 for(const [rawNo,x] of [...rawByNo.entries()].sort((a,b)=>a[0]-b[0])){
   if(!occById.has(+x.id))occById.set(+x.id,[]);
   occById.get(+x.id).push(+rawNo);
 }
 function occurrencesAfter(id,rawNo){
   const a=occById.get(+id)||[];let lo=0,hi=a.length;
   while(lo<hi){const m=(lo+hi)>>1;if(a[m]<=rawNo)lo=m+1;else hi=m}
   return a.slice(lo);
 }
 function indexedHoldCandidates(pg,lockIds){
   const free=Math.max(1,slots-lockIds.length),set=new Set([1]);
   const maxHold=Math.min(90,Math.max(12,targetSkip*4+18));
   // Every future occurrence of a locked id is a possible collision boundary.
   for(const id of lockIds){
     const occ=occurrencesAfter(id,+pg.__daoRawEnd).filter(n=>n<+d.firstPity.rawNo);
     for(const no of occ.slice(0,Math.max(8,targetSkip+6))){
       const gap=Math.max(1,no-(+pg.__daoRawEnd));
       const h=Math.max(1,Math.ceil(gap/free));
       for(const z of [h-1,h,h+1])if(z>=1&&z<=maxHold)set.add(z);
     }
   }
   // N*4 is the user's first baseline: for one-lock pages this starts around N washes.
   if(targetSkip>0){
     for(const z of [targetSkip-2,targetSkip-1,targetSkip,targetSkip+1,targetSkip+2])if(z>=1&&z<=maxHold)set.add(z);
   }
   return [...set].sort((x,y)=>x-y);
 }
 function indexedPlans(){
   const plans=[];
   // 100~200 pages are explicitly preferred, then the rest of the dynamic range.
   const order=[],seenDist=new Set();
   const addDist=(x)=>{if(x>=0&&x<pages.length&&x<=dynamicMax&&!seenDist.has(x)){seenDist.add(x);order.push(x)}};
   for(let x=100;x<=Math.min(200,dynamicMax);x++)addDist(x);
   for(const x of distOrder)addDist(x);
   for(const dist of order){
     const pg=pages[pages.length-1-dist];if(!pg)continue;
     const n=Math.min(slots,(pg.talents||[]).length);
     for(let lockCount=1;lockCount<=Math.min(2,slots-1);lockCount++){
       for(let mm=1;mm<(1<<n);mm++){
         let c=0;for(let i=0;i<n;i++)if(mm&(1<<i))c++;
         if(c!==lockCount)continue;
         const lockIds=[];for(let i=0;i<n;i++)if(mm&(1<<i))lockIds.push(+pg.talents[i].id);
         // Reject masks whose locked ids never reappear before pity: they cannot be useful kamek collisions.
         const futureHits=lockIds.reduce((s,id)=>s+occurrencesAfter(id,+pg.__daoRawEnd).filter(no=>no<+d.firstPity.rawNo).length,0);
         if(targetSkip>0&&futureHits===0)continue;
         for(const hold of indexedHoldCandidates(pg,lockIds)){
           const skipEst=estimatedSkipCount(pg,lockIds,hold);
           if(targetSkip>0&&skipEst===0&&futureHits===0)continue;
           const unit=(COST?.[slots]?.[lockCount]??(lockCount===1?4:8));
           const estCost=unit*hold;
           const farPriority=(dist>=100&&dist<=200)?0:1;
           plans.push({pg,dist,lockIds,lockCount,hold,skipEst,futureHits,estCost,farPriority});
         }
       }
     }
   }
   // First: exact/near skip count. Then realistic N*4 cost band. Then 100~200 page preference.
   plans.sort((a,b)=>
     Math.abs(a.skipEst-targetSkip)-Math.abs(b.skipEst-targetSkip) ||
     Math.abs(a.estCost-baselineCost)-Math.abs(b.estCost-baselineCost) ||
     a.farPriority-b.farPriority ||
     a.estCost-b.estCost || a.dist-b.dist || a.lockCount-b.lockCount);
   return plans;
 }
 const plans=indexedPlans();
 const layers=targetSkip>0?[0,1,2,4,8,Number.POSITIVE_INFINITY]:[Number.POSITIVE_INFINITY];
 let testedPlans=0;
 for(const tol of layers){
   // Only a compact shortlist reaches expensive washOnce/probe verification.
   let layerSeen=0;
   for(let pi=0;pi<plans.length;pi++){
     const p=plans[pi];
     if(Number.isFinite(tol)&&Math.abs(p.skipEst-targetSkip)>tol)continue;
     // Exact first layer starts at N*4; do not waste exact-skip probes on obviously cheaper bands.
     if(targetSkip>0&&tol===0&&p.estCost<baselineCost)continue;
     layerSeen++;testedPlans++;
     if(layerSeen>420)break;
     if(testedPlans===1||testedPlans%12===0){
       box.innerHTML=`<div class="warn"><b>잡맥 인덱스 탐색 중</b><br>`+
         `위치/생략 목표 <b>${targetSkip}</b> · 기준비용 <b>${baselineCost}단</b> · 허용오차 ${Number.isFinite(tol)?'±'+tol:'제한 해제'}<br>`+
         `후보 ${pi+1}/${plans.length} · 천장에서 ${p.dist}회차 앞 · 잠금 ${p.lockCount}개 × ${p.hold}회 · 예상 ${p.estCost}단<br>`+
         `인덱스 재등장 ${p.futureHits}개 · 실제 추적 스킵 ${p.skipEst} · seed 검증 ${testedPlans.toLocaleString()}회</div>`;
       await uiYield();
     }
     const cand=exactNearCandidate(p.pg,p.dist,p.lockIds,p.hold,dynamicMax,'잡맥 반복인덱스 → Born seed 검증');
     if(!cand)continue;
     cand.estimatedSkips=p.skipEst;cand.baselineCost=baselineCost;cand.indexFutureHits=p.futureHits;
     if(!best||cand.cost<best.cost||(cand.cost===best.cost&&cand.dist<best.dist))best=cand;
     // Plans are already ranked by skip/cost/distance. A valid exact layer seed is the preferred route.
     if(Number.isFinite(tol)&&tol<=2)break outer;
   }
 }
 }
'''
route=route[:start]+new+route[end:]
route=route.replace("`경로 검증: <b>${best.label||'비용우선 탐색'}</b>${best.baselineCost!=null?` · 위치/생략 기준비용 ${best.baselineCost}단`:''}${best.estimatedSkips!=null?` · 실제 추적 스킵 ${best.estimatedSkips}`:''}</div>`;",
                    "`경로 검증: <b>${best.label||'비용우선 탐색'}</b>${best.baselineCost!=null?` · 위치/생략 기준비용 ${best.baselineCost}단`:''}${best.estimatedSkips!=null?` · 실제 추적 스킵 ${best.estimatedSkips}`:''}${best.indexFutureHits!=null?` · 잠금맥 재등장 ${best.indexFutureHits}개`:''}</div>`;",1)

for x in ['const occById=new Map();','function indexedHoldCandidates(','function indexedPlans()','잡맥 인덱스 탐색 중','잡맥 반복인덱스 → Born seed 검증','layerSeen>420']:
 if x not in route: raise SystemExit('v3.28 guard missing: '+x)
text=text[:a]+route+text[b:]

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.28','file':'Nangman_Integrated_Simulator_v3_28.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.28',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.28</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v328_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.28: indexed daomai/kamek collision engine; UI and other modules unchanged')
