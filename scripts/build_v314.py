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

new_route=r'''function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 자맥 구간별 교체맥 표를 계산하세요.</div>';return}
 const rr=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw && x.name===sourceName) || DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!rr){box.innerHTML='<div class="warn">선택한 원시맥 행을 찾지 못했습니다.</div>';return}

 if(rr.zone==='pre'){
   box.innerHTML=`<div class="warn"><b>#${sourceRaw} ${sourceName}</b>은 현재 천장보다 이전 seed 참고행입니다.<br>`+
     `잡맥 생략은 원시 RNG를 앞으로 소비하므로 이 seed로 되돌아갈 수 없습니다. 천장 이전 행은 경로 계산 대상이 아닙니다.</div>`;
   return;
 }
 if(rr.zone==='pity'){
   box.innerHTML=`<div class="good"><b>필요 생략 0개</b> · 현재 기본 천장 seed</div>`+
    `<div class="small" style="line-height:1.8;margin-top:6px">천장 자맥: <b>${rr.pityName}</b><br>교체 1: <b>${rr.firstDraw||'-'}</b><br>교체 seed 검증: 현재 기본값</div>`;
   return;
 }

 const need=+rr.needSkip||0;
 let h=`<div class="good"><b>필요 생략 ${need}개</b> · 기본 천장 다음 ${need}번째 일반 원시 seed</div>`+
   `<div class="small" style="line-height:1.8;margin:6px 0">목표 천장: <b>${rr.pityName}</b><br>목표 교체 1: <b>${rr.firstDraw||'-'}</b><br>`+
   `목표는 원시 번호를 당기는 것이 아니라 <b>실제 천장 발생 후 luck_seed가 이 행의 목표 seed와 정확히 같아지는 것</b>입니다.</div>`;

 const base=unlockAll(stateFromSave(SAVE,roleObj(),+vipSel.value,rawCalcZizhi()));
 base.bag_pills=999999999;base.has_bag_pills=true;
 const slots=+QUAL[String(base.zizhi)]?.slots||0;
 const oneLockCost=+(COST?.[slots]?.[1]??0);

 function purpleFromStep(tr){
   const a=tr.result?.talents||[];
   const p=a.find(t=>!t.locked && +BYID.get(+t.id)?.weight===4) || a.find(t=>+BYID.get(+t.id)?.weight===4);
   return p?+p.id:0;
 }
 function outcomeAfterUnlock(st,max=400){
   let s=unlockAll(dc(st));
   for(let i=0;i<max;i++){
     const tr=washOnce(s);s=tr.state;
     if(tr.result?.got_gold){
       const pid=purpleFromStep(tr),draws=exchangeSequence(+s.luck_seed,s,15);
       return {state:s,pid,pname:pid?nm(pid):'-',draws,washes:i+1,wasPity:!!tr.result?.was_pity,luckAfterPity:+s.luck_seed};
     }
   }
   return null;
 }
 function nextNormals(st,count=2){
   let s=unlockAll(dc(st)),out=[],guard=100;
   while(out.length<count&&guard-->0){
     const before=+s.total_talent_bars||0,tr=washOnce(s);s=tr.state;
     const a=(tr.result?.talents||[]).filter(t=>!t.locked);
     for(let i=0;i<a.length&&out.length<count;i++){
       const it=BYID.get(+a[i].id);if(!it||+it.weight===4)continue;
       out.push({rawNo:before+i+1,id:+a[i].id,name:nm(+a[i].id)});
     }
   }
   return out;
 }

 // Exact single-lock search. Every candidate is replayed by washOnce; no array deletion/regrouping.
 let s=dc(base),pages=[],guard=2500;
 while(guard-->0){
   const tr=washOnce(s);s=tr.state;
   if(tr.result?.got_gold)break;
   pages.push({state:dc(s),tr:dc(tr)});
 }
 let best=null;
 const pageStart=Math.max(0,pages.length-120);
 for(let pi=pages.length-1;pi>=pageStart;pi--){
   const pg=pages[pi],normals=(pg.state.talents||[]).filter(t=>+BYID.get(+t.id)?.weight<4);
   for(const slot of normals){
     let b=dc(pg.state);b.talents=b.talents.map(t=>({...t,locked:+t.id===+slot.id}));
     if(b.talents.filter(t=>t.locked).length!==1)continue;
     for(let hold=1;hold<=32;hold++){
       let tr;try{tr=washOnce(b);b=tr.state}catch(e){break}
       if(tr.result?.got_gold)break;
       const out=outcomeAfterUnlock(b);if(!out)continue;
       if(+out.luckAfterPity!==+rr.targetLuckAfterPity)continue;
       if(+out.pid!==+rr.pityId)continue;
       const first=out.draws?.[0]?.id||0;
       if(+first!==+rr.firstDrawId)continue;
       const totalCost=(+out.state.total_pills||0)-(+base.total_pills||0);
       const cand={lockId:+slot.id,lockName:nm(+slot.id),lockWash:+pg.state.total_wash,hold,lockCost:hold*oneLockCost,totalCost,out,after:nextNormals(out.state,2)};
       if(!best||cand.totalCost<best.totalCost||(cand.totalCost===best.totalCost&&cand.lockWash>best.lockWash))best=cand;
       break;
     }
   }
 }

 if(!best){
   h+=`<div class="warn">실제 washOnce로 천장 직전 120회차의 1잠금 경로를 전부 검증했지만, <b>목표 seed와 완전히 같은</b> 단일잠금 경로를 찾지 못했습니다.<br>`+
     `이 경우 생략 ${need}개라는 표 값은 seed 위치를 뜻하지만, 실행 최소루트는 복수 잠금/잠금 변경 탐색이 더 필요합니다. 틀린 루트를 성공으로 표시하지 않습니다.</div>`;
   box.innerHTML=h;return;
 }
 const nxt=best.after.map(x=>`#${x.rawNo} ${x.name}`).join(' · ')||'-';
 h+=`<div class="good"><b>정확한 seed 검증 성공</b> · ${best.lockWash}회차 <b>${best.lockName}</b> 잠금 · 잠금 유지 <b>${best.hold}회</b></div>`+
   `<div class="small" style="line-height:1.8;margin-top:7px">총 소모: <b>${best.totalCost}단</b> · 잠금 세수 부분 ${best.lockCost}단<br>`+
   `실제 천장: <b>${best.out.pname}</b><br>실제 교체 1: <b>${best.out.draws?.[0]?.name||'-'}</b><br>`+
   `실제 천장 후 luck_seed: <b>${best.out.luckAfterPity}</b> = 목표 seed <b>${rr.targetLuckAfterPity}</b><br>`+
   `이어지는 일반 원시맥: <b>${nxt}</b></div>`;
 box.innerHTML=h;
}'''

new_exchange=r'''async function showDaoExchangeWindowV288(){
 const rawOut=document.getElementById('daoRawBeforeResult'),out=document.getElementById('daoExchangeWindowResult');if(!out)return;
 if(rawOut)rawOut.innerHTML='';
 out.innerHTML='<div class="warn">천장 직전 6개 참고 + 현재 천장 + 다음 원시 자맥 직전까지 정확한 천장/교체 seed 계산 중...</div>';
 try{
   const d=await daoWindowCachedV288();DAO_V290_WINDOW=d;
   const base=stateFromSave(SAVE,roleObj(),+vipSel.value,rawCalcZizhi());
   const eng=engineFor(base),slots=+QUAL[String(base.zizhi)]?.slots||0;if(!slots)throw Error('열린 슬롯 수를 찾지 못했습니다.');

   function pityPack(normalSeed,state){
     const pe=engineFor(state);let luck=+normalSeed,g=100000,pid=0;
     while(g-->0){let id;[id,luck]=rawPurple(luck,pe);if(!pe.allowed.has(id))continue;pid=+id;break}
     if(!pid)throw Error('천장 자맥 계산 실패');
     const draws=exchangeSequence(+luck,state,15);
     return {pityId:pid,pityName:nm(pid),targetLuckAfterPity:+luck,draws,firstDraw:draws[0]?.name||'',firstDrawId:+(draws[0]?.id||0)};
   }

   // Rebuild pre-pity normal snapshots only for six reference rows.
   let seed=+base.seed,rc=+(base.born_talent_rc||0),intl=!!base.international_wash;
   let talLucky=+base.tal_lucky||0,rawNo=0,washNo=0,guard=200000,preAll=[];
   const pityAt=+QUAL[String(base.zizhi)]?.base_pity||0;
   while(talLucky<pityAt&&guard-->0){
     washNo++;const seen=new Set();let accepted=0;
     while(accepted<slots&&guard-->0){
       let id;[id,seed]=rawNormal(seed,eng,intl?rc:0);if(intl)rc++;
       if(!eng.allowed.has(id)||seen.has(id))continue;
       const it=BYID.get(id);if(!it)continue;seen.add(id);accepted++;rawNo++;
       if(+it.weight===4)throw Error(`첫 천장 전 자연 자맥 ${nm(id)}이 나와 현재 분기와 맞지 않습니다.`);
       preAll.push({rawNo,wash:washNo,id,name:nm(id),normalSeed:+seed,rcAfter:+rc});
     }
     talLucky+=slots;
   }
   const rows=[];
   for(const r of preAll.slice(-6)){const p=pityPack(r.normalSeed,base);rows.push({...r,...p,kind:'천장 전 참고',zone:'pre',needSkip:null});}

   // Current real pity row. d.pityState.luck_seed is already AFTER the pity draw.
   const currentDraws=exchangeSequence(+d.pityState.luck_seed,d.pityState,15);
   rows.push({rawNo:+d.firstPity.rawNo,wash:+d.firstPity.wash,id:+d.firstPity.id,name:d.firstPity.name,kind:'현재 천장',zone:'pity',needSkip:0,
     pityId:+d.firstPity.id,pityName:d.firstPity.name,targetLuckAfterPity:+d.pityState.luck_seed,draws:currentDraws,firstDraw:currentDraws[0]?.name||'',firstDrawId:+(currentDraws[0]?.id||0)});

   // Forward seed table: 1 skip = first accepted normal raw after the default pity seed,
   // 2 skips = second, and so on, until the next natural purple boundary.
   const baseState=dc(d.pityState),postEng=engineFor(baseState);
   let pseed=+baseState.seed,prc=+(baseState.born_talent_rc||0),pintl=!!baseState.international_wash;
   let praw=+d.firstPity.rawNo,pwash=+baseState.total_wash,skip=0,stopPurple=null;guard=200000;
   while(guard-->0&&!stopPurple){
     pwash++;const seen=new Set();let accepted=0;
     while(accepted<slots&&guard-->0){
       let id;[id,pseed]=rawNormal(pseed,postEng,pintl?prc:0);if(pintl)prc++;
       if(!postEng.allowed.has(id)||seen.has(id))continue;
       const it=BYID.get(id);if(!it)continue;seen.add(id);accepted++;praw++;
       if(+it.weight===4){stopPurple={rawNo:praw,wash:pwash,id,name:nm(id)};break}
       skip++;
       const branch=dc(baseState);branch.seed=+pseed;if(pintl)branch.born_talent_rc=+prc;
       const p=pityPack(+pseed,branch);
       rows.push({rawNo:praw,wash:pwash,id,name:nm(id),normalSeed:+pseed,kind:'천장 이후',zone:'post',needSkip:skip,...p});
     }
   }
   if(!stopPurple)throw Error('다음 원시 자맥을 찾지 못했습니다.');

   DAO_V290_ROUTE_ROWS=rows.map(x=>({...x}));
   let h=`<div class="good"><b>정확한 seed 기준 교체맥 표</b><br><span class="small">`+
    `천장 전 6개는 참고용. 현재 천장은 생략 0개. <b>천장 바로 다음 일반맥 = 생략 1개, 두 번째 = 생략 2개</b> 순서입니다. `+
    `각 행은 일반 seed에서 천장 자맥을 먼저 1회 추출한 뒤 그 다음부터 교체 1~15를 계산합니다. 다음 원시 자맥 <b>#${stopPurple.rawNo} ${stopPurple.name}</b>은 경계입니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>원시 #</th><th>구간</th><th>필요 생략</th><th>기준 일반맥</th><th>천장 후보</th>';
   for(let i=1;i<=15;i++)h+=`<th>교체 ${i}</th>`;h+='</tr></thead><tbody>';
   for(const r of rows){
     const ns=r.zone==='pre'?'이동 불가':String(r.needSkip??0);
     h+=`<tr><td class="num">${r.rawNo}</td><td>${r.kind}</td><td class="num">${ns}</td>`+
      `<td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td>`+
      `<td class="q4"><b>${r.pityName}</b></td>`;
     for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||'-'}</td>`;h+='</tr>';
   }
   h+='</tbody></table></div><div id="daoPullRouteV290" class="card" style="margin-top:8px"><div class="small">원시맥을 누르면 목표 seed와 정확히 일치하는 실제 잠금 세수 경로만 표시합니다.</div></div>';
   out.innerHTML=h;
   out.onclick=(ev)=>{const btn=ev.target.closest?.('.dao-pull-v295');if(!btn)return;ev.preventDefault();const raw=Number(btn.dataset.raw||0),source=decodeURIComponent(btn.dataset.source||'');const r=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw&&x.name===source)||DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw);showDaoPullRouteV290(r?.firstDraw||'',raw,source,1);};
 }catch(e){out.innerHTML=`<div class="warn">교체맥 계산 오류: ${String(e&&e.message||e)}</div>`}
}'''

text=text[:start]+new_route+'\n'+new_exchange+text[marker:]
for x in ['천장 바로 다음 일반맥 = 생략 1개','targetLuckAfterPity','정확한 seed 검증 성공','천장 후보','v3.14']:
 if x not in text: raise SystemExit('v3.14 guard missing: '+x)
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.14','file':'Nangman_Integrated_Simulator_v3_14.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.14',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.14</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v314_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:4000])
print('built v3.14: skip N maps to Nth post-pity normal seed; pity draw first; exact post-pity luck_seed verification')
