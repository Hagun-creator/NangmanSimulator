from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_28.html')
DST=Path('Nangman_Integrated_Simulator_v3_29.html')
if not SRC.exists(): raise SystemExit('v3.28 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.28','v3.29').replace('v3_28','v3_29')
text=re.sub(r'(?<![0-9])3\.28(?![0-9])','3.29',text)
text=re.sub(r'<script id="stable-root-url-v328">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v329">try{if(/Nangman_Integrated_Simulator_v3_29\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]
needle=route.find(' const targetSkip=Math.max(0,targetShift);')
start=route.rfind(' outer:{',0,needle) if needle>=0 else -1
end=route.find('\n if(!best){',needle)
if start<0 or end<0: raise SystemExit('v3.28 engine block missing')

new=r''' outer:{
 // v3.29 occurrence-tail daomai/kamek engine.
 // Core rule from the guide: choose WHICH occurrence of the same talent to lock.
 const targetSkip=Math.max(0,targetShift);
 const baselineCost=targetSkip>0?targetSkip*4:0;
 const occById=new Map();
 const pageByRaw=new Map();
 for(const pg of pages){
   for(const x of (pg.__daoRawSlots||[]))pageByRaw.set(+x.rawNo,pg);
 }
 for(const [rawNo,x] of [...rawByNo.entries()].sort((a,b)=>a[0]-b[0])){
   if(!occById.has(+x.id))occById.set(+x.id,[]);
   occById.get(+x.id).push(+rawNo);
 }
 function holdToReach(pg,lockCount,targetRaw,expectedSkips){
   const free=Math.max(1,slots-lockCount);
   const gap=Math.max(1,+targetRaw-(+pg.__daoRawEnd));
   return Math.max(1,Math.ceil(Math.max(1,gap-Math.max(0,expectedSkips))/free));
 }
 function addPlan(out,seen,pg,dist,lockIds,hold,kind,want){
   if(!pg||hold<1)return;
   const key=[+pg.__daoRawStart,lockIds.slice().sort((a,b)=>a-b).join(','),hold].join('|');
   if(seen.has(key))return;seen.add(key);
   const skipEst=estimatedSkipCount(pg,lockIds,hold);
   const unit=(COST?.[slots]?.[lockIds.length]??(lockIds.length===1?4:8));
   out.push({pg,dist,lockIds:lockIds.slice(),hold,skipEst,estCost:unit*hold,kind,want});
 }
 function occurrencePlans(want){
   const out=[],seen=new Set();
   for(const [id,arr0] of occById.entries()){
     const arr=arr0.filter(n=>n<+d.firstPity.rawNo);
     if(want<=0||arr.length<=want)continue;
     const latestIdx=arr.length-want-1;
     for(const back of [0,1,2]){
       const si=latestIdx-back;if(si<0)continue;
       const raw=arr[si],pg=pageByRaw.get(raw);if(!pg)continue;
       if(!(pg.__daoRawSlots||[]).some(x=>+x.id===+id))continue;
       const kthIdx=si+want;if(kthIdx>=arr.length)continue;
       const targetRaw=arr[kthIdx];
       const baseHold=holdToReach(pg,1,targetRaw,want);
       const dist=pages.length-1-pages.indexOf(pg);
       for(const dh of [-1,0,1,2])addPlan(out,seen,pg,dist,[+id],baseHold+dh,'단일 반복맥',want);
     }
   }
   const seedPages=[];const seenPg=new Set();
   for(const p of out){const k=+p.pg.__daoRawStart;if(!seenPg.has(k)){seenPg.add(k);seedPages.push(p.pg)}}
   for(const pg of seedPages){
     const vis=(pg.__daoRawSlots||[]).slice(0,slots);
     for(let i=0;i<vis.length;i++)for(let j=i+1;j<vis.length;j++){
       const a=+vis[i].id,b=+vis[j].id;
       const aa=(occById.get(a)||[]).filter(n=>n>+pg.__daoRawEnd&&n<+d.firstPity.rawNo);
       const bb=(occById.get(b)||[]).filter(n=>n>+pg.__daoRawEnd&&n<+d.firstPity.rawNo);
       if(!aa.length&&!bb.length)continue;
       for(const kA of [0,Math.floor(want/2),Math.ceil(want/2),want]){
         const kB=want-kA;if(kA>aa.length||kB>bb.length)continue;
         const endA=kA?aa[kA-1]:+pg.__daoRawEnd;
         const endB=kB?bb[kB-1]:+pg.__daoRawEnd;
         const targetRaw=Math.max(endA,endB);
         const baseHold=holdToReach(pg,2,targetRaw,want);
         const dist=pages.length-1-pages.indexOf(pg);
         for(const dh of [-1,0,1])addPlan(out,seen,pg,dist,[a,b],baseHold+dh,'2잠금 반복맥',want);
       }
     }
   }
   out.sort((x,y)=>
     Math.abs(x.skipEst-want)-Math.abs(y.skipEst-want) ||
     Math.abs(x.estCost-baselineCost)-Math.abs(y.estCost-baselineCost) ||
     x.estCost-y.estCost || x.dist-y.dist || x.lockIds.length-y.lockIds.length);
   return out;
 }
 const skipTargets=targetSkip>0?[targetSkip,targetSkip-1,targetSkip+1,targetSkip-2,targetSkip+2]:[0];
 let testedPlans=0,totalGenerated=0;
 for(let ti=0;ti<skipTargets.length;ti++){
   const want=Math.max(0,skipTargets[ti]);
   const plans=occurrencePlans(want);totalGenerated+=plans.length;
   const cap=(ti===0?120:70);
   for(let pi=0;pi<plans.length&&pi<cap;pi++){
     const p=plans[pi];testedPlans++;
     if(testedPlans===1||testedPlans%8===0){
       box.innerHTML=`<div class="warn"><b>잡맥 출현열 탐색 중</b><br>`+
         `위치/생략 목표 <b>${targetSkip}</b> · 현재 잡맥 목표 <b>${want}</b> · 기준비용 ${baselineCost}단<br>`+
         `후보 ${pi+1}/${Math.min(plans.length,cap)} (생성 ${plans.length}) · ${p.kind}<br>`+
         `천장에서 ${p.dist}회차 앞 · 잠금 ${p.lockIds.length}개 × ${p.hold}회 · 예상 ${p.estCost}단 · 추적 스킵 ${p.skipEst}<br>`+
         `seed 검증 <b>${testedPlans}</b>회 · 누적 생성 ${totalGenerated}</div>`;
       await uiYield();
     }
     const cand=exactNearCandidate(p.pg,p.dist,p.lockIds,p.hold,dynamicMax,'잡맥 출현열 → Born seed 검증');
     if(!cand)continue;
     cand.estimatedSkips=p.skipEst;cand.baselineCost=baselineCost;cand.planKind=p.kind;cand.generatedPlans=totalGenerated;
     best=cand;break outer;
   }
 }
 if(!best){
   const loose=[];
   for(const want of [Math.max(1,targetSkip-4),targetSkip+4])loose.push(...occurrencePlans(want).slice(0,24));
   loose.sort((a,b)=>Math.abs(a.estCost-baselineCost)-Math.abs(b.estCost-baselineCost)||a.estCost-b.estCost);
   for(let i=0;i<Math.min(36,loose.length);i++){
     const p=loose[i];testedPlans++;
     const cand=exactNearCandidate(p.pg,p.dist,p.lockIds,p.hold,dynamicMax,'잡맥 출현열 제한 fallback');
     if(!cand)continue;
     cand.estimatedSkips=p.skipEst;cand.baselineCost=baselineCost;cand.planKind=p.kind;cand.generatedPlans=totalGenerated;
     best=cand;break outer;
   }
 }
 }
'''
route=route[:start]+new+route[end:]
route=route.replace("`경로 검증: <b>${best.label||'비용우선 탐색'}</b>${best.baselineCost!=null?` · 위치/생략 기준비용 ${best.baselineCost}단`:''}${best.estimatedSkips!=null?` · 실제 추적 스킵 ${best.estimatedSkips}`:''}${best.indexFutureHits!=null?` · 잠금맥 재등장 ${best.indexFutureHits}개`:''}</div>`;",
                    "`경로 검증: <b>${best.label||'비용우선 탐색'}</b>${best.baselineCost!=null?` · 위치/생략 기준비용 ${best.baselineCost}단`:''}${best.estimatedSkips!=null?` · 실제 추적 스킵 ${best.estimatedSkips}`:''}${best.planKind?` · ${best.planKind}`:''}${best.generatedPlans!=null?` · 생성후보 ${best.generatedPlans}`:''}</div>`;",1)
for x in ['function occurrencePlans(want)','const latestIdx=arr.length-want-1;','잡맥 출현열 탐색 중','단일 반복맥','2잠금 반복맥','잡맥 출현열 → Born seed 검증','const cap=(ti===0?120:70);']:
 if x not in route: raise SystemExit('v3.29 guard missing: '+x)
if 'for(let x=100;x<=Math.min(200,dynamicMax);x++)' in route: raise SystemExit('old 100-200 priority loop remains')
text=text[:a]+route+text[b:]
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.29','file':'Nangman_Integrated_Simulator_v3_29.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.29',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.29</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v329_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.29: occurrence-tail engine; no 100-200 page priority; compact seed verification shortlist')
