from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_16.html')
DST=Path('Nangman_Integrated_Simulator_v3_17.html')
if not SRC.exists(): raise SystemExit('v3.16 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.16','v3.17').replace('v3_16','v3_17')
text=re.sub(r'(?<![0-9])3\.16(?![0-9])','3.17',text)
text=re.sub(r'<script id="stable-root-url-v316">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v317">try{if(/Nangman_Integrated_Simulator_v3_17\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

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
 const pityAt=+QUAL[String(base.zizhi)]?.base_pity||0;
 if(slots<=0){box.innerHTML='<div class="warn">열린 슬롯이 없습니다.</div>';return}

 box.innerHTML=`<div class="warn"><b>${sourceName}</b> 목표 seed <b>${targetSeed}</b> 빠른 최소비용 탐색 중...<br><span class="small">가까운 순서가 아니라 <b>추가 세수단 비용이 싼 순서</b>로 검사합니다. 같은 비용에서는 천장에 가까운 후보부터 봅니다.</span></div>`;
 await uiYield();

 function unlocked(st){const x=dc(st);x.talents=(x.talents||[]).map(t=>({...t,locked:false}));return x}
 function probeKey(st){return [st.seed,st.born_talent_rc||0,st.tal_lucky,st.luck_seed||0,st.luck_seed_inited?1:0,st.gold_count||0,st.pity_count||0].join('|')}
 const probeCache=new Map();
 function probePitySeed(st){
   const u=unlocked(st),key=probeKey(u);if(probeCache.has(key))return probeCache.get(key);
   let s=u;const need=Math.max(0,pityAt-(+s.tal_lucky||0));const normalPages=Math.ceil(need/slots);const max=Math.min(48,normalPages+3);
   let out=null;
   for(let i=0;i<max;i++){
     const before=dc(s),tr=washOnce(before);s=tr.state;
     if(tr.result?.was_pity){out={seed:+before.seed,state:dc(s),washes:i+1};break}
     if(tr.result?.got_gold){out=null;break}
   }
   probeCache.set(key,out);return out;
 }

 // Baseline pages once.
 const pages=[];let scan=unlocked(base),guard=3000;
 while(guard-->0){const tr=washOnce(scan);scan=tr.state;if(tr.result?.got_gold)break;pages.push(unlocked(scan));}
 if(guard<=0){box.innerHTML='<div class="warn">기본 천장 이전 상태 재현 한도를 초과했습니다.</div>';return}

 // Build candidate operation shapes and order by ACTUAL pill cost first.
 // For a fixed lock count the per-wash cost is constant, so cost = unitCost * hold.
 const shapes=[];
 for(let lockCount=1;lockCount<slots;lockCount++){
   const unit=+(COST?.[slots]?.[lockCount]??0);if(unit<=0)continue;
   for(let hold=1;hold<=12;hold++)shapes.push({lockCount,hold,cost:unit*hold,unit});
 }
 shapes.sort((a,b)=>a.cost-b.cost || a.lockCount-b.lockCount || a.hold-b.hold);

 const WINDOWS=[8,16,28,40];
 let best=null,checked=0,probes=0,lastCost=-1;
 outer:
 for(const sh of shapes){
   // If a route already exists at a cheaper cost, later shapes cannot beat it.
   if(best && sh.cost>best.cost)break;
   if(sh.cost!==lastCost){lastCost=sh.cost;box.innerHTML=`<div class="warn">최소비용 탐색 · 현재 비용 <b>${sh.cost}단</b> · 잠금 ${sh.lockCount}개 × ${sh.hold}회</div>`;await uiYield();}

   // Progressive near-pity expansion: 8 -> 16 -> 28 -> 40 pages only.
   for(const win of WINDOWS){
     const limit=Math.min(win,pages.length);
     let foundThisWindow=false;
     for(let dist=0;dist<limit;dist++){
       const pg=pages[pages.length-1-dist];if(!pg)continue;
       const n=Math.min(slots,(pg.talents||[]).length);
       // combinations of exact lockCount only
       const masks=[];
       for(let m=1;m<(1<<n);m++){
         let c=0;for(let i=0;i<n;i++)if(m&(1<<i))c++;
         if(c===sh.lockCount)masks.push(m);
       }
       for(const m of masks){
         const lockIds=[];for(let i=0;i<n;i++)if(m&(1<<i))lockIds.push(+pg.talents[i].id);
         let st=dc(pg),path=[],ok=true;
         st.talents=st.talents.map(t=>({...t,locked:lockIds.includes(+t.id)}));
         for(let h=1;h<=sh.hold;h++){
           const before=dc(st);let tr;try{tr=washOnce(before)}catch(e){ok=false;break}
           st=tr.state;checked++;
           path.push({locks:lockIds.map(id=>({id,name:nm(id)})),pills:+tr.result.pills_used||0,beforeSeed:+before.seed,afterSeed:+st.seed,talents:(tr.result.talents||[]).map(t=>nm(t.id))});
           if(tr.result?.got_gold){ok=false;break}
           st.talents=st.talents.map(t=>({...t,locked:lockIds.includes(+t.id)}));
         }
         if(!ok)continue;
         const probe=probePitySeed(st);probes++;
         if(probe && +probe.seed===targetSeed){
           const cand={cost:sh.cost,dist,hold:sh.hold,lockIds:dc(lockIds),path:dc(path),probe,checked,probes,win};
           if(!best||cand.cost<best.cost||(cand.cost===best.cost&&cand.dist<best.dist))best=cand;
           foundThisWindow=true;
         }
       }
     }
     // We found a valid route at this exact cost. Since shapes are sorted by cost,
     // this cost is globally minimal among tested operation shapes. Stop immediately.
     if(best && best.cost===sh.cost)break outer;
     if(foundThisWindow)break;
   }
 }

 if(!best){
   box.innerHTML=`<div class="warn"><b>${sourceName}</b> 목표 seed ${targetSeed}에 대해 비용 우선 탐색을 했지만 경로를 찾지 못했습니다.<br>`+
     `최대 천장 전 40회차 · 잠금 후보 ${checked.toLocaleString()}회 · probe ${probes.toLocaleString()}회 · 캐시 ${probeCache.size.toLocaleString()}상태</div>`;
   return;
 }

 const lockNames=best.lockIds.map(id=>nm(id)).join(' + ');
 let h=`<div class="good"><b>목표 seed 도달 최소비용 경로</b> · 목표 seed <b>${targetSeed}</b> · 추가 잠금 세수 소모 <b>${best.cost.toLocaleString()}단</b></div>`+
   `<div class="small" style="line-height:1.7;margin:6px 0">천장에서 ${best.dist}회차 앞 · 잠금 ${best.lockIds.length}개 · 유지 ${best.hold}회<br>`+
   `검사: 잠금 ${checked.toLocaleString()}회 · probe ${probes.toLocaleString()}회 · 탐색범위 ${best.win}회차 이내<br>`+
   `잠금 해제 후 기본 세수 ${best.probe.washes}회 → 천장 직전 Born seed <b>${best.probe.seed}</b></div>`;
 h+='<div class="card" style="padding:10px"><b>실행 순서</b><ol style="margin:7px 0 0 20px;padding:0">';
 h+=`<li><b>${lockNames}</b> 잠금</li>`;
 for(let i=0;i<best.path.length;i++){
   const p=best.path[i];
   h+=`<li>잠금 유지 ${i+1}회차 세수 · ${p.pills}단 · Born ${p.beforeSeed} → ${p.afterSeed}<br><span class="small">결과: ${p.talents.join(' · ')}</span></li>`;
 }
 h+=`<li><b>잠금 해제</b> 후 기본 세수 ${best.probe.washes}회 → 목표 seed <b>${best.probe.seed}</b></li>`;
 h+='</ol></div>';
 box.innerHTML=h;
}'''
text=text[:a]+new_route+text[b:]

for x in ['const WINDOWS=[8,16,28,40]','shapes.sort((a,b)=>a.cost-b.cost','best.cost===sh.cost','최대 천장 전 40회차']:
 if x not in new_route: raise SystemExit('v3.17 guard missing: '+x)
if 'MAX_NEAR_PAGES=Math.min(100' in new_route: raise SystemExit('old 100-page scan remains')

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.17','file':'Nangman_Integrated_Simulator_v3_17.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.17',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.17</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v317_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.17: cost-first progressive near-pity search; max 40 pages')
