from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_24.html')
DST=Path('Nangman_Integrated_Simulator_v3_25.html')
if not SRC.exists(): raise SystemExit('v3.24 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.24','v3.25').replace('v3_24','v3_25')
text=re.sub(r'(?<![0-9])3\.24(?![0-9])','3.25',text)
text=re.sub(r'<script id="stable-root-url-v324">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v325">try{if(/Nangman_Integrated_Simulator_v3_25\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Replace ONLY the generic route-search scheduling. Keep wash/probe mechanics intact.
a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]
start=route.find(' const WINDOWS=[8,16,28,40];')
end=route.find('\n if(!best){',start)
if start<0 or end<0: raise SystemExit('old 8/16/28/40 search block missing')
old=route[start:end]

# Preserve the exactNearCandidate + direct verification helpers from the existing block,
# but replace the repeated-window generic loop after direct verification.
marker=' // Generic cost-first progressive search remains, but now it must beat the directly verified route.'
m=old.find(marker)
if m<0: raise SystemExit('generic-search marker missing')
prefix=old[:m]

new_generic=r''' // Generic cost-first search: each page is tested ONCE per operation shape.
 // The clicked table row already carries its distance from the basic pity seed. Use that only
 // as a SEARCH HEURISTIC (never as the success condition) to jump far enough back for larger shifts.
 const targetShift=Math.max(0,Number(row.shift)||0);
 const dynamicMax=Math.min(Math.max(0,pages.length-1), Math.max(40, targetShift>0 ? targetShift*12+24 : 40));
 function buildDistOrder(maxDist,shift){
   const out=[],seen=new Set();
   const add=(d)=>{d=Math.max(0,Math.min(maxDist,Math.round(d)));if(!seen.has(d)){seen.add(d);out.push(d)}};
   const band=(center,radius)=>{
     center=Math.max(0,Math.min(maxDist,Math.round(center)));
     add(center);
     for(let k=1;k<=radius;k++){add(center-k);add(center+k)}
   };
   if(shift>=8){
     // Large target movement: inspect roughly 100~200+ pages back first.
     band(Math.min(maxDist,shift*12),12);
     band(Math.min(maxDist,shift*9),10);
     band(Math.min(maxDist,shift*6),8);
   }
   band(Math.min(maxDist,40),8);
   band(Math.min(maxDist,20),6);
   band(0,4);
   // Complete the layer without duplicate pages. Far-to-near is preferable for large shifts.
   if(shift>=8){for(let d=maxDist;d>=0;d--)add(d)}else{for(let d=0;d<=maxDist;d++)add(d)}
   return out;
 }
 const distOrder=buildDistOrder(dynamicMax,targetShift);
 let lastUiChecked=-1;
 outer:
 for(const sh of shapes){
   if(best && sh.cost>best.cost)break;
   if(sh.cost!==lastCost){
     lastCost=sh.cost;
     box.innerHTML=`<div class="warn"><b>최소비용 탐색 중</b> · 현재 비용 <b>${sh.cost}단</b> · 잠금 ${sh.lockCount}개 × ${sh.hold}회<br>`+
       `목표 거리 ${targetShift} · 우선 탐색 최대 ${dynamicMax}회차 앞 · 페이지 ${distOrder.length.toLocaleString()}개 (중복 검사 없음)${best?` · 현재 최저 ${best.cost}단`:''}</div>`;
     await uiYield();
   }
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
       if(checked-lastUiChecked>=24){
         lastUiChecked=checked;
         box.innerHTML=`<div class="warn"><b>최소비용 탐색 중</b> · 현재 비용 <b>${sh.cost}단</b><br>`+
           `목표 거리 ${targetShift} · 천장에서 ${dist}회차 앞 · 페이지 ${di+1}/${distOrder.length} · 잠금 조합 ${mi+1}/${masks.length}<br>`+
           `누적 잠금 검사 <b>${checked.toLocaleString()}회</b> · 천장 probe <b>${probes.toLocaleString()}회</b>${best?` · 현재 최저 ${best.cost}단`:''}</div>`;
         await uiYield();
       }
       const cand=exactNearCandidate(pg,dist,lockIds,sh.hold,dynamicMax,'목표거리 우선 비용탐색');
       if(!cand)continue;
       if(!best||cand.cost<best.cost||(cand.cost===best.cost&&cand.dist<best.dist))best=cand;
       // shapes are sorted by cost; the first hit in this cost layer proves no more expensive
       // layer can improve pill cost. Same-cost alternatives are unnecessary for the requested route.
       if(best && best.cost===sh.cost)break outer;
     }
   }
 }
'''
new_block=prefix+new_generic
route=route[:start]+new_block+route[end:]

# Update failure wording if the old 40-page message still exists.
route=route.replace('최대 천장 전 40회차', '목표 거리 기반 동적 탐색')
route=route.replace('탐색범위 ${best.win}회차 이내', '탐색범위 ${best.win}회차 앞까지')

for x in ['const targetShift=Math.max(0,Number(row.shift)||0);','targetShift*12+24','buildDistOrder','중복 검사 없음','목표거리 우선 비용탐색']:
 if x not in route: raise SystemExit('v3.25 guard missing: '+x)
if 'const WINDOWS=[8,16,28,40];' in route: raise SystemExit('old repeated windows still present')
text=text[:a]+route+text[b:]

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.25','file':'Nangman_Integrated_Simulator_v3_25.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.25',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.25</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v325_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.25: dynamic target-distance cost search; no repeated windows')
