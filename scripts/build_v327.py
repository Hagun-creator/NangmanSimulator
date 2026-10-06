from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_26.html')
DST=Path('Nangman_Integrated_Simulator_v3_27.html')
if not SRC.exists(): raise SystemExit('v3.26 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.26','v3.27').replace('v3_26','v3_27')
text=re.sub(r'(?<![0-9])3\.26(?![0-9])','3.27',text)
text=re.sub(r'<script id="stable-root-url-v326">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v327">try{if(/Nangman_Integrated_Simulator_v3_27\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]

start=route.find(' outer:{\n // shift is a heuristic only.')
end=route.find('\n if(!best){',start)
if start<0 or end<0: raise SystemExit('v3.26 skip-guided block missing')

new=r''' outer:{
 // 위치/생략 N is a PRIORITY HINT, not the final success condition.
 // First pass: assume one useful skipped raw costs at least one 1-lock wash (4 pills),
 // therefore start from N*4 pills. For N=18 this means 72 pills, not 4/8/12.
 const targetSkip=Math.max(0,targetShift);
 const baselineCost=targetSkip>0?targetSkip*4:0;
 const far100to200=[];
 for(let dd=100;dd<=Math.min(200,dynamicMax);dd++)far100to200.push(dd);
 const farSet=new Set(far100to200);
 const remainingDist=distOrder.filter(dd=>!farSet.has(dd));
 const preferredDist=[...far100to200,...remainingDist];

 const exactShapes=targetSkip>0
   ? shapes.filter(sh=>sh.cost>=baselineCost).sort((a,b)=>a.cost-b.cost || a.hold-b.hold || a.lockCount-b.lockCount)
   : shapes.slice();
 const fallbackShapes=targetSkip>0
   ? shapes.slice().sort((a,b)=>Math.abs(a.cost-baselineCost)-Math.abs(b.cost-baselineCost) || a.cost-b.cost)
   : shapes.slice();

 async function runLayer(shapeList,tolerance,label){
   for(const sh of shapeList){
     if(best && sh.cost>best.cost)return true;
     // In the primary exact-skip pass, never waste probes below N*4.
     if(targetSkip>0 && tolerance===0 && sh.cost<baselineCost)continue;
     box.innerHTML=`<div class="warn"><b>최소비용 탐색 중</b> · ${label}<br>`+
       `위치/생략 목표 <b>${targetSkip}</b> · 기준 시작비용 <b>${baselineCost}단</b> · 현재 비용 <b>${sh.cost}단</b><br>`+
       `우선 구간: 천장 100~200회차 앞 · 스킵 허용오차 ${Number.isFinite(tolerance)?'±'+tolerance:'제한 해제'}<br>`+
       `누적 잠금 검사 <b>${checked.toLocaleString()}회</b> · probe <b>${probes.toLocaleString()}회</b></div>`;
     await uiYield();

     for(let di=0;di<preferredDist.length;di++){
       const dist=preferredDist[di],pg=pages[pages.length-1-dist];if(!pg)continue;
       const n=Math.min(slots,(pg.talents||[]).length);
       const masks=[];
       for(let mm=1;mm<(1<<n);mm++){
         let c=0;for(let i=0;i<n;i++)if(mm&(1<<i))c++;
         if(c===sh.lockCount)masks.push(mm);
       }
       for(let mi=0;mi<masks.length;mi++){
         const mm=masks[mi];
         const lockIds=[];for(let i=0;i<n;i++)if(mm&(1<<i))lockIds.push(+pg.talents[i].id);
         const skipEst=estimatedSkipCount(pg,lockIds,sh.hold);
         if(targetSkip>0 && Number.isFinite(tolerance) && Math.abs(skipEst-targetSkip)>tolerance)continue;

         if(checked-lastUiChecked>=24){
           lastUiChecked=checked;
           box.innerHTML=`<div class="warn"><b>최소비용 탐색 중</b> · ${label}<br>`+
             `목표 스킵 ${targetSkip} · 실제 추적 스킵 ${skipEst} · 기준 ${baselineCost}단 · 현재 ${sh.cost}단<br>`+
             `천장에서 ${dist}회차 앞 · ${di+1}/${preferredDist.length} · 잠금 조합 ${mi+1}/${masks.length}<br>`+
             `누적 잠금 검사 <b>${checked.toLocaleString()}회</b> · probe <b>${probes.toLocaleString()}회</b></div>`;
           await uiYield();
         }

         const cand=exactNearCandidate(pg,dist,lockIds,sh.hold,dynamicMax,label);
         if(!cand)continue;
         cand.estimatedSkips=skipEst;cand.skipTolerance=tolerance;cand.baselineCost=baselineCost;
         if(!best||cand.cost<best.cost||(cand.cost===best.cost&&cand.dist<best.dist))best=cand;
         // Primary purpose is to find a valid seed at the expected cost band quickly.
         if(best && best.cost===sh.cost)return true;
       }
     }
   }
   return false;
 }

 // 1) Exact target skip, starting at N*4 pills, 100~200 pages first.
 if(await runLayer(exactShapes,0,'1차 · 생략수 정확일치 / 기준비용 우선'))break outer;
 // 2) Nearby skip counts, still centered around the same realistic cost band.
 for(const tol of [1,2,4,8]){
   if(await runLayer(fallbackShapes,tol,`2차 · 생략수 근접 ±${tol}`))break outer;
 }
 // 3) Final fallback: do not require skip-count equality; exact Born seed remains authoritative.
 await runLayer(fallbackShapes,Number.POSITIVE_INFINITY,'3차 · 생략조건 해제 / seed 직접검증');
 }
'''
route=route[:start]+new+route[end:]

# Clarify result summary.
route=route.replace("`경로 검증: <b>${best.label||'비용우선 탐색'}</b>${best.estimatedSkips!=null?` · 검증 전 예상 스킵 ${best.estimatedSkips}`:''}</div>`;",
                    "`경로 검증: <b>${best.label||'비용우선 탐색'}</b>${best.baselineCost!=null?` · 위치/생략 기준비용 ${best.baselineCost}단`:''}${best.estimatedSkips!=null?` · 실제 추적 스킵 ${best.estimatedSkips}`:''}</div>`;",1)

for x in ['const baselineCost=targetSkip>0?targetSkip*4:0;','for(let dd=100;dd<=Math.min(200,dynamicMax);dd++)','1차 · 생략수 정확일치 / 기준비용 우선','if(targetSkip>0 && tolerance===0 && sh.cost<baselineCost)continue;','3차 · 생략조건 해제 / seed 직접검증']:
 if x not in route: raise SystemExit('v3.27 guard missing: '+x)
text=text[:a]+route+text[b:]

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.27','file':'Nangman_Integrated_Simulator_v3_27.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.27',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.27</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v327_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.27: N*4 baseline cost; 100-200 pages first; exact skip count then widen; exact Born seed final')
