from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_29.html')
DST=Path('Nangman_Integrated_Simulator_v3_30.html')
if not SRC.exists(): raise SystemExit('v3.29 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.29','v3.30').replace('v3_29','v3_30')
text=re.sub(r'(?<![0-9])3\.29(?![0-9])','3.30',text)
text=re.sub(r'<script id="stable-root-url-v329">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v330">try{if(/Nangman_Integrated_Simulator_v3_30\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]
start=route.find(' outer:{\n // v3.29 occurrence-tail daomai/kamek engine.')
end=route.find('\n if(!best){',start)
if start<0 or end<0: raise SystemExit('v3.29 engine block missing')

new=r''' outer:{
 // v3.30 multi-episode daomai/kamek engine.
 // Guide model: consume MANY duplicate raws by short lock -> wash -> unlock episodes,
 // possibly using different talent IDs. Never assume one talent stays locked all the way to pity.
 const targetSkip=Math.max(0,targetShift);
 const baselineCost=targetSkip>0?targetSkip*4:0;
 const pageIndex=new Map();for(let i=0;i<pages.length;i++)pageIndex.set(pages[i],i);

 function makeEpisodes(){
   const eps=[],seen=new Set();
   const maxHold=Math.min(28,Math.max(6,targetSkip+6));
   for(let i=0;i<pages.length;i++){
     const pg=pages[i],vis=(pg.__daoRawSlots||[]).slice(0,slots);
     // Primary guide action: lock ONE visible talent only as long as needed to consume the next duplicate(s), then unlock.
     for(const x of vis){
       let lastSkip=0;
       for(let h=1;h<=maxHold;h++){
         const sk=estimatedSkipCount(pg,[+x.id],h);
         if(sk<=lastSkip)continue;
         lastSkip=sk;
         const tr=traceEpisode(pg,[+x.id],h),endRaw=Math.max(+pg.__daoRawEnd,...(tr.washes||[]).flatMap(w=>[(w.cursorAfter||0)-1]));
         const cost=(COST?.[slots]?.[1]??4)*h;
         const key=[i,+x.id,sk].join('|');if(seen.has(key))continue;seen.add(key);
         eps.push({start:i,end:Math.min(pages.length,i+h),pg,lockIds:[+x.id],hold:h,skip:sk,cost,endRaw,kind:'1잠금 짧은 잡맥'});
         if(sk>=Math.max(targetSkip+2,4))break;
       }
     }
     // Secondary short two-lock action: only 1~3 washes, for the guide's 2-lock page adjustment cases.
     for(let a=0;a<vis.length;a++)for(let c=a+1;c<vis.length;c++){
       const ids=[+vis[a].id,+vis[c].id];let lastSkip=0;
       for(let h=1;h<=3;h++){
         const sk=estimatedSkipCount(pg,ids,h);if(sk<=lastSkip)continue;lastSkip=sk;
         const cost=(COST?.[slots]?.[2]??8)*h,key=[i,ids.slice().sort((u,v)=>u-v).join(','),sk].join('|');
         if(seen.has(key))continue;seen.add(key);
         eps.push({start:i,end:Math.min(pages.length,i+h),pg,lockIds:ids,hold:h,skip:sk,cost,kind:'2잠금 짧은 보정'});
       }
     }
   }
   // Pareto preference: cheap per consumed raw, then earlier availability.
   eps.sort((a,b)=>(a.cost/a.skip)-(b.cost/b.skip)||a.cost-b.cost||a.start-b.start||a.hold-b.hold);
   return eps;
 }

 function pushTop(bucket,st,K=10){
   const sig=st.eps.map(e=>`${e.start}:${e.lockIds.join('+')}:${e.hold}`).join('/');
   if(bucket.some(x=>x.sig===sig))return;
   st.sig=sig;bucket.push(st);bucket.sort((a,b)=>a.cost-b.cost||a.eps.length-b.eps.length);
   if(bucket.length>K)bucket.length=K;
 }

 function composeRoutes(episodes,want){
   const n=pages.length,MAX=Math.max(want+3,3),K=10;
   const byStart=Array.from({length:n+1},()=>[]);for(const e of episodes)if(e.start<=n)byStart[e.start].push(e);
   const dp=Array.from({length:n+1},()=>Array.from({length:MAX+1},()=>[]));
   dp[0][0].push({cost:0,eps:[],sig:''});
   for(let i=0;i<n;i++){
     for(let s=0;s<=MAX;s++)for(const st of dp[i][s]){
       pushTop(dp[i+1][s],{cost:st.cost,eps:st.eps.slice()},K);
       for(const e of byStart[i]){
         const ns=Math.min(MAX,s+e.skip),j=Math.max(i+1,Math.min(n,e.end));
         pushTop(dp[j][ns],{cost:st.cost+e.cost,eps:[...st.eps,e]},K);
       }
     }
   }
   const out=[];for(const s of [want,want-1,want+1,want-2,want+2].filter(x=>x>=0&&x<=MAX))for(const st of dp[n][s])out.push({...st,totalSkip:s});
   out.sort((a,b)=>Math.abs(a.totalSkip-want)-Math.abs(b.totalSkip-want)||a.cost-b.cost||a.eps.length-b.eps.length);
   return out.slice(0,48);
 }

 function validateMulti(routePlan){
   const es=routePlan.eps;if(!es.length)return null;
   let st=dc(es[0].pg),cur=es[0].start,total=0,steps=[];
   for(let ei=0;ei<es.length;ei++){
     const e=es[ei];
     const gap=Math.max(0,e.start-cur);
     for(let g=0;g<gap;g++){
       st=unlocked(st);let tr;try{tr=washOnce(st)}catch(_){return null}st=tr.state;
       if(tr.result?.got_gold)return null;
     }
     const visible=new Set((st.talents||[]).map(t=>+t.id));if(!e.lockIds.every(id=>visible.has(+id)))return null;
     st.talents=st.talents.map(t=>({...t,locked:e.lockIds.includes(+t.id)}));
     const epSteps=[];
     for(let h=0;h<e.hold;h++){
       const before=dc(st);let tr;try{tr=washOnce(before)}catch(_){return null}st=tr.state;
       if(tr.result?.got_gold)return null;
       total+=+tr.result.pills_used||0;
       epSteps.push({beforeSeed:+before.seed,afterSeed:+st.seed,pills:+tr.result.pills_used||0,talents:(tr.result.talents||[]).map(t=>nm(t.id))});
       st.talents=st.talents.map(t=>({...t,locked:e.lockIds.includes(+t.id)}));
     }
     st=unlocked(st);steps.push({episode:e,steps:epSteps});cur=e.start+e.hold;
   }
   const probe=probePitySeed(st);probes++;if(!probe||+probe.seed!==targetSeed)return null;
   const first=es[0],rawSlots=dc(first.pg.__daoRawSlots||[]),lockRawSlots=rawSlots.filter(x=>first.lockIds.includes(+x.id));
   return {cost:total,dist:pages.length-1-first.start,hold:first.hold,lockIds:first.lockIds.slice(),path:steps[0]?.steps||[],probe,checked,probes,win:pages.length,
     rawStart:+first.pg.__daoRawStart,rawEnd:+first.pg.__daoRawEnd,rawSlots,lockRawSlots,trace:traceEpisode(first.pg,first.lockIds,first.hold),firstFree:null,
     label:'다중 잡맥 에피소드 DP → 실제 연속 검증',estimatedSkips:routePlan.totalSkip,baselineCost,multiEpisodes:steps,episodeCount:es.length};
 }

 const episodes=makeEpisodes();
 const routes=composeRoutes(episodes,targetSkip);
 box.innerHTML=`<div class="warn"><b>잡맥 에피소드 조합 계산</b><br>`+
   `목표 생략 <b>${targetSkip}</b> · 기준 ${baselineCost}단 · 짧은 잠금 에피소드 ${episodes.length.toLocaleString()}개<br>`+
   `DP 경로 후보 ${routes.length}개 · 서로 다른 맥 잠금/해제를 조합한 뒤 실제 seed를 검증합니다.</div>`;await uiYield();
 for(let ri=0;ri<routes.length;ri++){
   if(ri===0||ri%4===0){box.innerHTML=`<div class="warn"><b>잡맥 에피소드 실제 검증 중</b><br>`+
     `목표 생략 ${targetSkip} · 후보 ${ri+1}/${routes.length} · 예상 생략 ${routes[ri].totalSkip} · 예상 추가비용 ${routes[ri].cost}단<br>`+
     `에피소드 ${routes[ri].eps.length}개 · seed 검증 ${probes.toLocaleString()}회</div>`;await uiYield();}
   const cand=validateMulti(routes[ri]);if(!cand)continue;
   if(!best||cand.cost<best.cost)best=cand;
   // DP is cost ordered inside the nearest skip layer; first exact-seed route is the preferred practical result.
   if(routes[ri].totalSkip===targetSkip)break;
 }
 }
'''
route=route[:start]+new+route[end:]

# Multi-episode actionable output, while preserving legacy single-episode rendering as fallback.
out_anchor=" const lockNames=best.lockRawSlots.length?best.lockRawSlots.map(x=>`#${x.rawNo} ${x.name}`).join(' + '):best.lockIds.map(id=>nm(id)).join(' + ');"
pos=route.find(out_anchor)
if pos<0: raise SystemExit('route output anchor missing')
route=route[:pos]+r''' if(best.multiEpisodes&&best.multiEpisodes.length){
   let h=`<div class="good"><b>목표 seed 도달 잡맥 최소경로</b> · 목표 seed <b>${targetSeed}</b> · 추가 잠금 소모 <b>${best.cost.toLocaleString()}단</b></div>`+
     `<div class="small" style="line-height:1.8;margin:6px 0">예상/구성 생략: <b>${best.estimatedSkips}</b> · 잠금 에피소드 <b>${best.multiEpisodes.length}개</b><br>`+
     `경로 검증: <b>${best.label}</b></div><div class="card" style="padding:10px"><b>실제 실행 순서</b><ol style="margin:7px 0 0 20px;padding:0">`;
   for(const m of best.multiEpisodes){
     const e=m.episode,names=e.lockIds.map(id=>nm(id)).join(' + ');
     h+=`<li><b>${names}</b> 잠금 → 세수 <b>${e.hold}회</b> (${m.steps.reduce((s,x)=>s+x.pills,0)}단) → <b>즉시 잠금 해제</b>`+
        `<br><span class="small">이 에피소드 예상 잡맥 ${e.skip}개 · 시작 원시 #${e.pg.__daoRawStart}~#${e.pg.__daoRawEnd}</span></li>`;
   }
   h+=`<li>마지막 잠금 해제 후 무잠금 세수를 계속하여 천장 직전 Born seed <b>${best.probe.seed}</b> 확인</li></ol></div>`;
   box.innerHTML=h;return;
 }
''' + route[pos:]

for x in ['function makeEpisodes()','function composeRoutes(','function validateMulti(','다중 잡맥 에피소드 DP → 실제 연속 검증','즉시 잠금 해제','best.multiEpisodes']:
 if x not in route: raise SystemExit('v3.30 guard missing: '+x)
if 'v3.29 occurrence-tail daomai/kamek engine' in route: raise SystemExit('old v3.29 engine remains')
text=text[:a]+route+text[b:]

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.30','file':'Nangman_Integrated_Simulator_v3_30.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.30',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.30</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v330_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.30: multi-episode kamek DP engine; short lock/wash/unlock actions; exact sequential seed validation')
