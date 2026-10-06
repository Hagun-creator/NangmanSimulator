from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_25.html')
DST=Path('Nangman_Integrated_Simulator_v3_26.html')
if not SRC.exists(): raise SystemExit('v3.25 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.25','v3.26').replace('v3_25','v3_26')
text=re.sub(r'(?<![0-9])3\.25(?![0-9])','3.26',text)
text=re.sub(r'<script id="stable-root-url-v325">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v326">try{if(/Nangman_Integrated_Simulator_v3_26\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]

# Add a cheap skip-count estimator based on the already-built raw stream trace.
anchor=""" function traceFreePage(startCursor){
   let cursor=startCursor,seen=new Set(),accepted=[],skipped=[];
   while(accepted.length<slots && cursor<+d.firstPity.rawNo){
     const x=rawByNo.get(cursor);cursor++;
     if(!x)continue;
     if(seen.has(+x.id)){skipped.push(x);continue}
     seen.add(+x.id);accepted.push(x);
   }
   return {accepted,skipped,cursorAfter:cursor};
 }
"""
insert=anchor+""" function estimatedSkipCount(pg,lockIds,holdCount){
   try{
     const tr=traceEpisode(pg,lockIds,holdCount);
     return (tr.washes||[]).reduce((n,w)=>n+(w.skipped||[]).length,0);
   }catch(e){return 0}
 }
"""
if anchor not in route: raise SystemExit('traceFreePage anchor missing')
route=route.replace(anchor,insert,1)

# Replace generic search loop with skip-guided pruning before any expensive exact candidate/probe.
start=route.find(' outer:\n for(const sh of shapes){')
end=route.find('\n if(!best){',start)
if start<0 or end<0: raise SystemExit('generic outer loop boundary missing')
old=route[start:end]
new=r''' outer:
 // shift is a heuristic only. First search candidates whose actual traced duplicate skips are
 // near the clicked row's position/skip number. If none succeed, widen the tolerance gradually.
 const skipTolerances=targetShift>0?[0,1,2,4,8,Number.POSITIVE_INFINITY]:[Number.POSITIVE_INFINITY];
 let skipLayer=-1;
 for(const tol of skipTolerances){
   skipLayer++;
   for(const sh of shapes){
     if(best && sh.cost>best.cost)break;
     if(sh.cost!==lastCost || tol!==skipTolerances[Math.max(0,skipLayer-1)]){
       lastCost=sh.cost;
       box.innerHTML=`<div class="warn"><b>최소비용 탐색 중</b> · 현재 비용 <b>${sh.cost}단</b> · 잠금 ${sh.lockCount}개 × ${sh.hold}회<br>`+
         `위치/생략 목표 ${targetShift} · 스킵 허용오차 ${Number.isFinite(tol)?'±'+tol:'제한 해제'} · 우선 탐색 최대 ${dynamicMax}회차 앞${best?` · 현재 최저 ${best.cost}단`:''}</div>`;
       await uiYield();
     }
     let shapeHasPlausible=false;
     for(let di=0;di<distOrder.length;di++){
       const dist=distOrder[di],pg=pages[pages.length-1-dist];if(!pg)continue;
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
         if(targetShift>0 && Number.isFinite(tol) && Math.abs(skipEst-targetShift)>tol)continue;
         shapeHasPlausible=true;
         if(checked-lastUiChecked>=24){
           lastUiChecked=checked;
           box.innerHTML=`<div class="warn"><b>최소비용 탐색 중</b> · 현재 비용 <b>${sh.cost}단</b><br>`+
             `위치/생략 목표 ${targetShift} · 예상 실제 스킵 ${skipEst} · 허용오차 ${Number.isFinite(tol)?'±'+tol:'제한 해제'}<br>`+
             `천장에서 ${dist}회차 앞 · 페이지 ${di+1}/${distOrder.length} · 잠금 조합 ${mi+1}/${masks.length}<br>`+
             `누적 잠금 검사 <b>${checked.toLocaleString()}회</b> · 천장 probe <b>${probes.toLocaleString()}회</b>${best?` · 현재 최저 ${best.cost}단`:''}</div>`;
           await uiYield();
         }
         const cand=exactNearCandidate(pg,dist,lockIds,sh.hold,dynamicMax,'생략지표 우선 비용탐색');
         if(!cand)continue;
         cand.estimatedSkips=skipEst;cand.skipTolerance=tol;
         if(!best||cand.cost<best.cost||(cand.cost===best.cost&&cand.dist<best.dist))best=cand;
         if(best && best.cost===sh.cost)break outer;
       }
     }
     // If this whole cheap cost shape cannot even approach the target skip count in the current
     // tolerance layer, it was pruned without expensive Born-seed probes.
     if(!shapeHasPlausible && targetShift>0 && Number.isFinite(tol))continue;
   }
 }
'''
route=route[:start]+new+route[end:]

# Explain the heuristic in the result summary when available.
route=route.replace("`경로 검증: <b>${best.label||'비용우선 탐색'}</b></div>`;",
                    "`경로 검증: <b>${best.label||'비용우선 탐색'}</b>${best.estimatedSkips!=null?` · 검증 전 예상 스킵 ${best.estimatedSkips}`:''}</div>`;",1)

for x in ['function estimatedSkipCount(','skipTolerances','생략지표 우선 비용탐색','예상 실제 스킵','shapeHasPlausible']:
 if x not in route: raise SystemExit('v3.26 guard missing: '+x)
text=text[:a]+route+text[b:]

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.26','file':'Nangman_Integrated_Simulator_v3_26.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.26',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.26</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v326_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.26: skip-position heuristic prunes implausible low-cost probes; seed equality remains final success')
