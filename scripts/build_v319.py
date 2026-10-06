from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_18.html')
DST=Path('Nangman_Integrated_Simulator_v3_19.html')
if not SRC.exists(): raise SystemExit('v3.18 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.18','v3.19').replace('v3_18','v3_19')
text=re.sub(r'(?<![0-9])3\.18(?![0-9])','3.19',text)
text=re.sub(r'<script id="stable-root-url-v318">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v319">try{if(/Nangman_Integrated_Simulator_v3_19\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Patch only the search section inside the existing v3.18 route function.
a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]
start=route.find(' const WINDOWS=[8,16,28,40];')
end=route.find('\n if(!best){',start)
if start<0 or end<0: raise SystemExit('search block missing')

new_search=r''' const WINDOWS=[8,16,28,40];
 let best=null,checked=0,probes=0,lastCost=-1;

 function exactNearCandidate(pg,dist,lockIds,hold,win,label){
   let st=dc(pg),path=[],cost=0,ok=true;
   st.talents=st.talents.map(t=>({...t,locked:lockIds.includes(+t.id)}));
   if(st.talents.filter(t=>t.locked).length!==lockIds.length)return null;
   for(let h=1;h<=hold;h++){
     const before=dc(st);let tr;try{tr=washOnce(before)}catch(e){ok=false;break}
     st=tr.state;checked++;cost+=+tr.result.pills_used||0;
     path.push({locks:lockIds.map(id=>({id,name:nm(id)})),pills:+tr.result.pills_used||0,beforeSeed:+before.seed,afterSeed:+st.seed,talents:(tr.result.talents||[]).map(t=>nm(t.id))});
     if(tr.result?.got_gold){ok=false;break}
     st.talents=st.talents.map(t=>({...t,locked:lockIds.includes(+t.id)}));
   }
   if(!ok)return null;
   const probe=probePitySeed(st);probes++;
   if(!probe||+probe.seed!==targetSeed)return null;
   const rawSlots=dc(pg.__daoRawSlots||[]);
   const lockRawSlots=rawSlots.filter(x=>lockIds.includes(+x.id));
   const trace=traceEpisode(pg,lockIds,hold);
   const firstFree=traceFreePage(trace.cursor);
   return {cost,dist,hold,lockIds:dc(lockIds),path:dc(path),probe,checked,probes,win,
     rawStart:+pg.__daoRawStart,rawEnd:+pg.__daoRawEnd,rawSlots,lockRawSlots,trace,firstFree,label};
 }

 // DIRECT verification of the user's observed pattern:
 // within the 4 pages immediately before pity, try every 1-lock and 2-lock choice,
 // especially hold=1 then unlock and continue normally to pity. This catches routes such as
 // "two talents locked one wash -> unlock -> one normal wash -> pity" without relying on generic ordering.
 const direct=[];
 const nearLimit=Math.min(4,pages.length);
 for(let dist=0;dist<nearLimit;dist++){
   const pg=pages[pages.length-1-dist];if(!pg)continue;
   const n=Math.min(slots,(pg.talents||[]).length);
   for(let lockCount=1;lockCount<=Math.min(2,slots-1);lockCount++){
     for(let m=1;m<(1<<n);m++){
       let c=0;for(let i=0;i<n;i++)if(m&(1<<i))c++;
       if(c!==lockCount)continue;
       const lockIds=[];for(let i=0;i<n;i++)if(m&(1<<i))lockIds.push(+pg.talents[i].id);
       for(let hold=1;hold<=3;hold++){
         const cand=exactNearCandidate(pg,dist,lockIds,hold,nearLimit,'천장 직전 직접검증');
         if(cand)direct.push(cand);
       }
     }
   }
 }
 if(direct.length){
   direct.sort((x,y)=>x.cost-y.cost || x.dist-y.dist || x.hold-y.hold || x.lockIds.length-y.lockIds.length);
   best=direct[0];
 }

 // Generic cost-first progressive search remains, but now it must beat the directly verified route.
 outer:
 for(const sh of shapes){
   if(best && sh.cost>best.cost)break;
   if(sh.cost!==lastCost){lastCost=sh.cost;box.innerHTML=`<div class="warn">최소비용 탐색 · 현재 비용 <b>${sh.cost}단</b> · 잠금 ${sh.lockCount}개 × ${sh.hold}회${best?` · 직접검증 최저 ${best.cost}단`:''}</div>`;await uiYield();}

   for(const win of WINDOWS){
     const limit=Math.min(win,pages.length);
     for(let dist=0;dist<limit;dist++){
       const pg=pages[pages.length-1-dist];if(!pg)continue;
       const n=Math.min(slots,(pg.talents||[]).length);
       const masks=[];
       for(let m=1;m<(1<<n);m++){
         let c=0;for(let i=0;i<n;i++)if(m&(1<<i))c++;
         if(c===sh.lockCount)masks.push(m);
       }
       for(const m of masks){
         const lockIds=[];for(let i=0;i<n;i++)if(m&(1<<i))lockIds.push(+pg.talents[i].id);
         const cand=exactNearCandidate(pg,dist,lockIds,sh.hold,win,'비용우선 탐색');
         if(!cand)continue;
         if(!best||cand.cost<best.cost||(cand.cost===best.cost&&cand.dist<best.dist))best=cand;
       }
     }
     if(best && best.cost===sh.cost)break outer;
   }
 }
'''
route=route[:start]+new_search+route[end:]

# Add a clear note to output showing whether the winning route came from direct near-pity verification.
needle="`검사: 잠금 ${checked.toLocaleString()}회 · probe ${probes.toLocaleString()}회 · 탐색범위 ${best.win}회차 이내</div>`;"
repl="`검사: 잠금 ${checked.toLocaleString()}회 · probe ${probes.toLocaleString()}회 · 탐색범위 ${best.win}회차 이내<br>`+\n   `경로 검증: <b>${best.label||'비용우선 탐색'}</b></div>`;"
if needle not in route: raise SystemExit('output note anchor missing')
route=route.replace(needle,repl,1)

for x in ['DIRECT verification of the user\'s observed pattern','lockCount<=Math.min(2,slots-1)','hold=1 then unlock','exactNearCandidate','직접검증 최저','경로 검증']:
 if x not in route: raise SystemExit('v3.19 guard missing: '+x)
text=text[:a]+route+text[b:]

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.19','file':'Nangman_Integrated_Simulator_v3_19.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.19',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.19</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v319_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.19: direct 1/2-lock near-pity verification + generic cost comparison')
