from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_12.html')
DST=Path('Nangman_Integrated_Simulator_v3_13.html')
if not SRC.exists(): raise SystemExit('v3.12 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.12','v3.13').replace('v3_12','v3_13')
text=re.sub(r'(?<![0-9])3\.12(?![0-9])','3.13',text)
text=re.sub(r'<script id="stable-root-url-v312">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v313">try{if(/Nangman_Integrated_Simulator_v3_13\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Replace ONLY the daomai route function. Table rows already carry their target seed in luckStart.
a=text.find('function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
new_route=r'''async function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 자맥 구간별 교체맥 표를 계산하세요.</div>';return}
 const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!row){box.innerHTML='<div class="warn">선택한 원시맥 행을 찾지 못했습니다.</div>';return}
 if(!SAVE||!roleObj()){box.innerHTML='<div class="warn">세이브와 캐릭터를 먼저 선택하세요.</div>';return}
 const targetSeed=+(row.luckStart??row.seedAfter??0);
 const targetPity=row.pity?.name||targetName||'';
 const targetDraws=(row.draws||[]).slice(0,15).map(x=>x.name);
 if(!targetSeed){box.innerHTML='<div class="warn">선택 행의 목표 seed를 찾지 못했습니다.</div>';return}

 let base=unlockAll(stateFromSave(SAVE,roleObj(),+vipSel.value,rawCalcZizhi()));
 base.bag_pills=999999999;base.has_bag_pills=true;
 const slots=+QUAL[String(base.zizhi)]?.slots||0;
 if(slots<=0){box.innerHTML='<div class="warn">열린 슬롯이 없습니다.</div>';return}

 box.innerHTML=`<div class="warn"><b>${sourceName}</b> 목표 seed <b>${targetSeed}</b> 최소 세수단 경로 탐색 중...<br><span class="small">실제 washOnce 상태만 탐색하며 seed·천장·교체 1~15가 모두 일치해야 성공합니다.</span></div>`;
 await uiYield();

 function normalize(st){const x=dc(st);x.talents=(x.talents||[]).map(t=>({...t,locked:false}));return x}
 function stateKey(st){
   return [st.seed,st.born_talent_rc||0,st.luck_seed||0,st.luck_seed_inited?1:0,st.tal_lucky,
     (st.talents||[]).map(t=>+t.id).join(','),st.gold_count||0,st.pity_count||0].join('|');
 }
 function lockSets(n){
   const out=[[]],max=(1<<n)-1;
   for(let m=1;m<=max;m++){
     const a=[];for(let i=0;i<n;i++)if(m&(1<<i))a.push(i);
     if(a.length<slots)out.push(a);
   }
   return out;
 }
 function heapPush(h,x){h.push(x);let i=h.length-1;while(i){const p=(i-1)>>1;if(h[p].cost<=x.cost)break;h[i]=h[p];i=p}h[i]=x}
 function heapPop(h){if(!h.length)return null;const r=h[0],x=h.pop();if(h.length){let i=0;while(1){let l=i*2+1;if(l>=h.length)break;let rr=l+1,c=rr<h.length&&h[rr].cost<h[l].cost?rr:l;if(h[c].cost>=x.cost)break;h[i]=h[c];i=c}h[i]=x}return r}
 function pityName(st){const t=(st.talents||[]).find(t=>+BYID.get(+t.id)?.weight===4);return t?nm(t.id):''}
 function goal(before,after,tr){
   if(!tr.result.was_pity)return false;
   if(+before.seed!==targetSeed)return false;
   if(pityName(after)!==targetPity)return false;
   const got=exchangeSequence(+after.luck_seed,after,15).map(x=>x.name);
   if(got.length<targetDraws.length)return false;
   for(let i=0;i<targetDraws.length;i++)if(got[i]!==targetDraws[i])return false;
   return true;
 }

 const heap=[],seen=new Map();
 const root=normalize(base),rk=stateKey(root);
 heapPush(heap,{cost:0,st:root,path:[]});seen.set(rk,0);
 let best=null,expanded=0;
 const NODE_LIMIT=220000;
 while(heap.length&&expanded<NODE_LIMIT){
   const cur=heapPop(heap);if(!cur)break;
   const ck=stateKey(cur.st);if((seen.get(ck)??Infinity)<cur.cost)continue;
   expanded++;
   if(expanded%2000===0){box.innerHTML=`<div class="warn">최소경로 탐색 중 · 상태 ${expanded.toLocaleString()}개 · 현재비용 ${cur.cost.toLocaleString()}단</div>`;await uiYield();}
   if(+cur.st.gold_count>0||cur.st.luck_seed_inited)continue;
   const n=Math.min(slots,(cur.st.talents||[]).length);
   for(const idxs of lockSets(n)){
     const before=dc(cur.st);
     before.talents=before.talents.map((t,i)=>({...t,locked:idxs.includes(i)}));
     if(before.talents.filter(t=>t.locked).length>=slots)continue;
     let tr;try{tr=washOnce(before)}catch(e){continue}
     const after=tr.state,edge=+tr.result.pills_used||0,nc=cur.cost+edge;
     const step={locks:idxs.map(i=>({id:+before.talents[i].id,name:nm(before.talents[i].id)})),pills:edge,
       beforeSeed:+before.seed,afterSeed:+after.seed,talLuckyBefore:+before.tal_lucky,
       talents:(tr.result.talents||[]).map(t=>nm(t.id)),wasPity:!!tr.result.was_pity};
     if(goal(before,after,tr)){best={cost:nc,st:after,path:cur.path.concat([step]),expanded};heap.length=0;break}
     if(tr.result.got_gold)continue;
     const ns=normalize(after),nk=stateKey(ns),old=seen.get(nk);
     if(old!=null&&old<=nc)continue;
     seen.set(nk,nc);heapPush(heap,{cost:nc,st:ns,path:cur.path.concat([step])});
   }
 }

 if(!best){
   box.innerHTML=`<div class="warn"><b>${sourceName}</b> 목표 seed ${targetSeed}에 대해 실제 상태 ${expanded.toLocaleString()}개를 탐색했지만 확정 경로를 찾지 못했습니다.${expanded>=NODE_LIMIT?' 탐색 한도에 도달했으므로 최소경로를 추정해서 표시하지 않습니다.':''}</div>`;
   return;
 }

 const parts=[];let freeRun=0,freePills=0;
 function flushFree(){if(freeRun){parts.push({free:true,count:freeRun,pills:freePills});freeRun=0;freePills=0}}
 for(const s of best.path){if(!s.locks.length&&!s.wasPity){freeRun++;freePills+=s.pills;continue}flushFree();parts.push(s)}flushFree();
 let h=`<div class="good"><b>검증 완료 최소비용 경로</b> · 목표 seed <b>${targetSeed}</b> · 실제 천장 <b>${pityName(best.st)}</b> · 총 소모 <b>${best.cost.toLocaleString()}단</b></div>`+
 `<div class="small" style="line-height:1.7;margin:6px 0">성공 조건: 천장 직전 Born seed = ${targetSeed} · 천장 자맥 = ${targetPity} · 교체 1~15 전부 일치<br>탐색 상태: ${best.expanded.toLocaleString()}개</div>`;
 h+='<div class="card" style="padding:10px"><b>실행 순서</b><ol style="margin:7px 0 0 20px;padding:0">';
 for(const p of parts){
   if(p.free){h+=`<li>잠금 없이 <b>${p.count}회</b> 세수 · ${p.pills}단</li>`;continue}
   const lk=p.locks.length?p.locks.map(x=>x.name).join(' + '):'잠금 없음';
   h+=`<li><b>${lk}</b> 상태로 1회 세수 · ${p.pills}단 · Born ${p.beforeSeed} → ${p.afterSeed}${p.wasPity?' · <b>천장 발생 / seed 검증 성공</b>':''}<br><span class="small">결과: ${p.talents.join(' · ')}</span></li>`;
 }
 h+='</ol></div>';
 box.innerHTML=h;
}'''
text=text[:a]+new_route+text[b:]

text=text.replace('필요한 일반맥 생략 수','목표 seed 이동 순번')
text=text.replace('필요한 실제 중복 제거 수','목표 seed 이동 순번')

route=text[text.find('async function showDaoPullRouteV290('):text.find('\nasync function showDaoExchangeWindowV288(){',text.find('async function showDaoPullRouteV290('))]
for bad in ['needDel','totalDeleted>=','rawNo)-targetRaw']:
 if bad in route: raise SystemExit('old deletion success criterion remains: '+bad)
for x in ['goal(before,after,tr)','+before.seed!==targetSeed','exchangeSequence(+after.luck_seed,after,15)','NODE_LIMIT=220000','검증 완료 최소비용 경로']:
 if x not in route: raise SystemExit('exact route guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.13','file':'Nangman_Integrated_Simulator_v3_13.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.13',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.13</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v313_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.13: exact uniform-cost washOnce route search with seed+pity+15-draw verification')
