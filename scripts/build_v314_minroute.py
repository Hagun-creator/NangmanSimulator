from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_13.html')
DST=Path('Nangman_Integrated_Simulator_v3_14.html')
if not SRC.exists(): raise SystemExit('v3.13 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.13','v3.14').replace('v3_13','v3_14')
text=re.sub(r'(?<![0-9])3\.13(?![0-9])','3.14',text)
text=re.sub(r'<script id="stable-root-url-v313">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v314">try{if(/Nangman_Integrated_Simulator_v3_14\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

start=text.find('function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){')
end=text.find('\nasync function showDaoExchangeWindowV288(){',start)
marker=text.find('\n(()=>{',end)
if marker<0: marker=text.find('\nnCalc.onclick',end)
if min(start,end,marker)<0: raise SystemExit('daomai function boundary missing')

new_route=r'''async function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 자맥 구간별 교체맥 표를 계산하세요.</div>';return}
 const rr=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw&&x.name===sourceName)||DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!rr){box.innerHTML='<div class="warn">선택한 원시맥 행을 찾지 못했습니다.</div>';return}
 if(rr.zone==='pre'){
   box.innerHTML=`<div class="warn"><b>#${sourceRaw} ${sourceName}</b>은 현재 천장보다 이전 seed 참고행입니다. 잡맥 생략은 RNG를 앞으로 소비하므로 이 seed로 되돌아갈 수 없습니다.</div>`;return;
 }
 if(rr.zone==='pity'){
   box.innerHTML=`<div class="good"><b>최소루트</b> · 추가 조작 없음 · 필요 생략 0개</div><div class="small" style="line-height:1.8;margin-top:6px">천장 <b>${rr.pityName}</b> · 교체 1 <b>${rr.firstDraw||'-'}</b></div>`;return;
 }
 const need=+rr.needSkip||0;
 box.innerHTML=`<div class="warn"><b>목표 seed 최소비용 경로 탐색 중...</b><br>목표: 생략 ${need}개 위치 · 천장 ${rr.pityName} · 교체 1 ${rr.firstDraw||'-'}</div>`;
 await uiYield();

 const root=unlockAll(stateFromSave(SAVE,roleObj(),+vipSel.value,rawCalcZizhi()));
 root.bag_pills=999999999;root.has_bag_pills=true;
 const slots=+QUAL[String(root.zizhi)]?.slots||0;
 if(slots<=0){box.innerHTML='<div class="warn">열린 슬롯 수를 찾지 못했습니다.</div>';return}
 const basePills=+root.total_pills||0;
 const pityAt=+QUAL[String(root.zizhi)]?.base_pity||0;

 function stateKey(s){
   const ids=(s.talents||[]).map(t=>+t.id).sort((a,b)=>a-b).join(',');
   return [+s.seed||0,+s.luck_seed||0,+s.tal_lucky||0,+s.born_talent_rc||0,ids].join('|');
 }
 function subsets(s){
   const a=(s.talents||[]).filter(t=>+BYID.get(+t.id)?.weight<4).map(t=>+t.id);
   const out=[[]],n=a.length;
   for(let mask=1;mask<(1<<n);mask++){
     const x=[];for(let i=0;i<n;i++)if(mask&(1<<i))x.push(a[i]);
     if(x.length<slots)out.push(x);
   }
   return out;
 }
 function purpleId(tr){
   const p=(tr.result?.talents||[]).find(t=>+BYID.get(+t.id)?.weight===4);return p?+p.id:0;
 }
 function routeLabel(ids){return ids.length?ids.map(id=>nm(id)).join(' + '):'잠금 없음'}
 function nextNormals(st,count=2){
   let s=unlockAll(dc(st)),out=[],g=80;
   while(out.length<count&&g-->0){
     const before=+s.total_talent_bars||0,tr=washOnce(s);s=tr.state;
     const arr=(tr.result?.talents||[]).filter(t=>!t.locked);
     for(let i=0;i<arr.length&&out.length<count;i++){
       const it=BYID.get(+arr[i].id);if(!it||+it.weight===4)continue;
       out.push({rawNo:before+i+1,id:+arr[i].id,name:nm(+arr[i].id)});
     }
   }
   return out;
 }

 const heap=new MinHeap(),seen=new Map();let serial=0,expanded=0,best=null;
 heap.push({cost:0,serial:serial++,st:dc(root),path:[]});
 seen.set(stateKey(root),0);
 const MAX_EXPAND=120000,MAX_EXTRA_WASH=420;
 const rootWash=+root.total_wash||0;
 while(heap.length&&expanded<MAX_EXPAND){
   const cur=heap.pop();expanded++;
   if(cur.cost!==seen.get(stateKey(cur.st)))continue;
   if((+cur.st.total_wash||0)-rootWash>MAX_EXTRA_WASH)continue;
   for(const lockIdsNow of subsets(cur.st)){
     let prepared=dc(cur.st);const keep=new Set(lockIdsNow);
     prepared.talents=prepared.talents.map(t=>({...t,locked:keep.has(+t.id)}));
     let tr;try{tr=washOnce(prepared)}catch(e){continue}
     const ns=tr.state,stepCost=+(tr.result?.pills_used||0),nc=cur.cost+stepCost;
     const action={wash:+ns.total_wash,locks:[...lockIdsNow],lockNames:routeLabel(lockIdsNow),cost:stepCost,total:nc,
       result:(tr.result?.talents||[]).map(t=>({id:+t.id,name:nm(+t.id),locked:!!t.locked})),gotGold:!!tr.result?.got_gold};
     if(tr.result?.got_gold){
       const pid=purpleId(tr),draws=exchangeSequence(+ns.luck_seed,ns,15),first=+(draws[0]?.id||0);
       if(+ns.luck_seed===+rr.targetLuckAfterPity && pid===+rr.pityId && first===+rr.firstDrawId){
         best={cost:nc,state:ns,path:cur.path.concat([action]),draws,pid};break;
       }
       continue;
     }
     const k=stateKey(ns),old=seen.get(k);
     if(old!=null&&old<=nc)continue;
     seen.set(k,nc);heap.push({cost:nc,serial:serial++,st:ns,path:cur.path.concat([action])});
   }
   if(best)break;
   if(expanded%2500===0){box.innerHTML=`<div class="warn">최소비용 경로 탐색 중 · 상태 ${expanded.toLocaleString()}개 · 현재 비용 ${cur.cost.toLocaleString()}단</div>`;await uiYield()}
 }

 if(!best){
   box.innerHTML=`<div class="warn"><b>목표 seed 최소루트를 찾지 못했습니다.</b><br>실제 washOnce 상태 ${expanded.toLocaleString()}개를 비용순으로 탐색했습니다. 잘못된 근사 루트는 표시하지 않습니다.</div>`;return;
 }
 const compact=[];
 for(const a of best.path){
   const prev=compact[compact.length-1];
   const key=a.locks.slice().sort((x,y)=>x-y).join(',');
   if(prev&&prev.key===key){prev.count++;prev.cost+=a.cost;prev.endWash=a.wash;prev.last=a}else compact.push({key,locks:a.locks,lockNames:a.lockNames,count:1,cost:a.cost,startWash:a.wash,endWash:a.wash,last:a});
 }
 let h=`<div class="good"><b>최소 세수단 루트</b> · 총 <b>${best.cost.toLocaleString()}단</b> · 목표 생략 위치 ${need}개 · 탐색 상태 ${expanded.toLocaleString()}개</div>`+
   `<div class="small" style="line-height:1.8;margin-top:6px">목표 천장: <b>${rr.pityName}</b> · 목표 교체 1: <b>${rr.firstDraw||'-'}</b><br>`+
   `실제 도달 luck_seed: <b>${best.state.luck_seed}</b> = 목표 seed <b>${rr.targetLuckAfterPity}</b></div>`;
 h+='<div class="card" style="padding:10px;margin-top:8px"><b>실행 순서</b><ol style="margin:7px 0 0 20px;padding:0">';
 for(const x of compact){
   const range=x.startWash===x.endWash?`${x.startWash}회차`:`${x.startWash}~${x.endWash}회차`;
   const vals=x.last.result.map(t=>`${t.locked?'[잠금] ':''}${t.name}`).join(' · ');
   h+=`<li style="margin:7px 0"><b>${range}</b>: ${x.lockNames} · ${x.count}회 세수 · ${x.cost}단<br><span class="small">마지막 결과: ${vals}</span></li>`;
 }
 h+='</ol></div>';
 const after=nextNormals(best.state,2).map(x=>`#${x.rawNo} ${x.name}`).join(' · ')||'-';
 h+=`<div class="good" style="margin-top:8px">검증 완료 · 실제 천장 <b>${nm(best.pid)}</b> · 교체 1 <b>${best.draws[0]?.name||'-'}</b> · 이후 일반맥 <b>${after}</b></div>`;
 box.innerHTML=h;
}'''

new_exchange=r'''async function showDaoExchangeWindowV288(){
 const rawOut=document.getElementById('daoRawBeforeResult'),out=document.getElementById('daoExchangeWindowResult');if(!out)return;
 if(rawOut)rawOut.innerHTML='';
 out.innerHTML='<div class="warn">정확한 천장/교체 seed 표 계산 중...</div>';
 try{
   const d=await daoWindowCachedV288();DAO_V290_WINDOW=d;
   const base=stateFromSave(SAVE,roleObj(),+vipSel.value,rawCalcZizhi()),eng=engineFor(base),slots=+QUAL[String(base.zizhi)]?.slots||0;
   function pityPack(normalSeed,state){
     const pe=engineFor(state);let luck=+normalSeed,g=100000,pid=0;
     while(g-->0){let id;[id,luck]=rawPurple(luck,pe);if(!pe.allowed.has(id))continue;pid=+id;break}
     if(!pid)throw Error('천장 자맥 계산 실패');
     const draws=exchangeSequence(+luck,state,15);
     return {pityId:pid,pityName:nm(pid),targetLuckAfterPity:+luck,draws,firstDraw:draws[0]?.name||'',firstDrawId:+(draws[0]?.id||0)};
   }
   let seed=+base.seed,rc=+(base.born_talent_rc||0),intl=!!base.international_wash,talLucky=+base.tal_lucky||0,rawNo=0,washNo=0,guard=200000,preAll=[];
   const pityAt=+QUAL[String(base.zizhi)]?.base_pity||0;
   while(talLucky<pityAt&&guard-->0){washNo++;const seen=new Set();let accepted=0;while(accepted<slots&&guard-->0){let id;[id,seed]=rawNormal(seed,eng,intl?rc:0);if(intl)rc++;if(!eng.allowed.has(id)||seen.has(id))continue;const it=BYID.get(id);if(!it)continue;seen.add(id);accepted++;rawNo++;if(+it.weight===4)throw Error(`첫 천장 전 자연 자맥 ${nm(id)} 등장`);preAll.push({rawNo,wash:washNo,id,name:nm(id),normalSeed:+seed})}talLucky+=slots}
   const rows=[];for(const r of preAll.slice(-6)){const p=pityPack(r.normalSeed,base);rows.push({...r,...p,kind:'천장 전 참고',zone:'pre',needSkip:null})}
   const currentDraws=exchangeSequence(+d.pityState.luck_seed,d.pityState,15);
   rows.push({rawNo:+d.firstPity.rawNo,wash:+d.firstPity.wash,id:+d.firstPity.id,name:d.firstPity.name,kind:'현재 천장',zone:'pity',needSkip:0,pityId:+d.firstPity.id,pityName:d.firstPity.name,targetLuckAfterPity:+d.pityState.luck_seed,draws:currentDraws,firstDraw:currentDraws[0]?.name||'',firstDrawId:+(currentDraws[0]?.id||0)});
   const bs=dc(d.pityState),pe=engineFor(bs);let pseed=+bs.seed,prc=+(bs.born_talent_rc||0),pintl=!!bs.international_wash,praw=+d.firstPity.rawNo,pwash=+bs.total_wash,skip=0,stop=null;guard=200000;
   while(guard-->0&&!stop){pwash++;const seen=new Set();let accepted=0;while(accepted<slots&&guard-->0){let id;[id,pseed]=rawNormal(pseed,pe,pintl?prc:0);if(pintl)prc++;if(!pe.allowed.has(id)||seen.has(id))continue;const it=BYID.get(id);if(!it)continue;seen.add(id);accepted++;praw++;if(+it.weight===4){stop={rawNo:praw,name:nm(id)};break}skip++;const branch=dc(bs);branch.seed=+pseed;if(pintl)branch.born_talent_rc=+prc;const p=pityPack(+pseed,branch);rows.push({rawNo:praw,wash:pwash,id,name:nm(id),normalSeed:+pseed,kind:'천장 이후',zone:'post',needSkip:skip,...p})}}
   if(!stop)throw Error('다음 원시 자맥을 찾지 못했습니다.');
   DAO_V290_ROUTE_ROWS=rows.map(x=>({...x}));
   let h=`<div class="good"><b>정확한 seed 기준 교체맥 표</b><br><span class="small">현재 천장=생략 0. 천장 바로 다음 일반맥=1개, 두 번째=2개 순서입니다. 클릭하면 숫자만 보여주는 것이 아니라 <b>그 seed로 실제 도달하는 최소 세수단 루트</b>를 탐색합니다. 다음 자맥 <b>#${stop.rawNo} ${stop.name}</b>은 경계입니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>원시 #</th><th>구간</th><th>seed 위치</th><th>기준 일반맥</th><th>천장 후보</th>';for(let i=1;i<=15;i++)h+=`<th>교체 ${i}</th>`;h+='</tr></thead><tbody>';
   for(const r of rows){const ns=r.zone==='pre'?'이동 불가':String(r.needSkip??0);h+=`<tr><td class="num">${r.rawNo}</td><td>${r.kind}</td><td class="num">${ns}</td><td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td><td class="q4"><b>${r.pityName}</b></td>`;for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||'-'}</td>`;h+='</tr>'}
   h+='</tbody></table></div><div id="daoPullRouteV290" class="card" style="margin-top:8px"><div class="small">원시맥 클릭 → 목표 seed와 정확히 일치하는 최소 세수단 경로 탐색.</div></div>';out.innerHTML=h;
   out.onclick=async(ev)=>{const btn=ev.target.closest?.('.dao-pull-v295');if(!btn)return;ev.preventDefault();const raw=Number(btn.dataset.raw||0),source=decodeURIComponent(btn.dataset.source||'');const r=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw&&x.name===source)||DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw);await showDaoPullRouteV290(r?.firstDraw||'',raw,source,1)};
 }catch(e){out.innerHTML=`<div class="warn">교체맥 계산 오류: ${String(e&&e.message||e)}</div>`}
}'''

text=text[:start]+new_route+'\n'+new_exchange+text[marker:]
for x in ['최소 세수단 루트','MAX_EXPAND=120000','targetLuckAfterPity','천장 바로 다음 일반맥=1개','v3.14']:
 if x not in text: raise SystemExit('guard missing '+x)
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.14','file':'Nangman_Integrated_Simulator_v3_14.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.14',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.14</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v314m_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:4000])
print('built v3.14 exact minimum-cost route')
