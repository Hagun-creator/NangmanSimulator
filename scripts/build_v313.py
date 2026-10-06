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

# Replace only the daomai route + exchange-table functions. Other simulator modules remain intact.
start=text.find('function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){')
end=text.find('\nasync function showDaoExchangeWindowV288(){',start)
if start<0 or end<0: raise SystemExit('route function boundary missing')
end2=text.find('\n}',end)
# Find the real end of async function by using the next known binding marker.
marker=text.find('\n(()=>{',end)
if marker<0: marker=text.find('\nnCalc.onclick',end)
if marker<0: raise SystemExit('exchange function end marker missing')

new_route=r'''function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 자맥 구간별 교체맥 표를 계산하세요.</div>';return}
 const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw && x.kind===((x.kind)||''));
 const rr=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw && x.name===sourceName) || DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!rr){box.innerHTML='<div class="warn">선택한 원시맥 행을 찾지 못했습니다.</div>';return}
 const target=rr.firstDraw||targetName||'';

 if(rr.zone==='pre'){
   box.innerHTML=`<div class="warn"><b>#${sourceRaw} ${sourceName}</b>은 현재 천장보다 이전 seed 참고행입니다.<br>`+
     `중복 스킵은 원시 RNG를 <b>앞으로 더 소비</b>하는 동작이라 과거 seed로 되돌릴 수 없습니다. 따라서 이 행에는 “필요 생략 ${rr.preDistance||0}개” 같은 역방향 경로를 표시하지 않습니다.</div>`;
   return;
 }
 if(rr.zone==='pity'){
   box.innerHTML=`<div class="good"><b>#${sourceRaw} ${sourceName}</b>은 현재 기본 천장입니다.</div>`+
     `<div class="small" style="line-height:1.7;margin-top:6px">필요 생략: <b>0개</b><br>현재 천장 자맥: <b>${d.firstPity.name}</b><br>교체 1: <b>${rr.firstDraw||'-'}</b></div>`;
   return;
 }

 const need=Math.max(0,+rr.needSkip||0);
 let h=`<div class="good"><b>#${sourceRaw} ${sourceName}</b> 기준 → 목표 천장/교체 1 <b>${target}</b></div>`+
   `<div class="small" style="line-height:1.7;margin:6px 0">현재 기본 천장: <b>#${d.firstPity.rawNo} ${d.firstPity.name}</b><br>`+
   `이 기준 seed까지 필요한 추가 원시 소비(생략): <b>${need}개</b><br>`+
   `※ 천장 이전 번호 차이를 빼는 방식이 아니라, <b>천장 이후 seed가 앞으로 진행한 횟수</b>입니다.</div>`;
 if(need===0){box.innerHTML=h;return}

 // Exact verification: reproduce real wash states, lock one actually visible normal talent,
 // run locked washes, unlock, then continue with washOnce() until the first purple page.
 // Accept only a route whose ACTUAL resulting purple equals the clicked row's target.
 const base=unlockAll(stateFromSave(SAVE,roleObj(),+vipSel.value,rawCalcZizhi()));
 base.bag_pills=999999999;base.has_bag_pills=true;
 const slots=+QUAL[String(base.zizhi)]?.slots||0;
 const oneLockCost=+(COST?.[slots]?.[1]??0);
 const targetId=(()=>{const x=BYNAME?.get?.(target);return x?+x.id:0})();

 function purpleFromStep(tr){
   const a=tr.result?.talents||[];
   const p=a.find(t=>!t.locked && +BYID.get(+t.id)?.weight===4) || a.find(t=>+BYID.get(+t.id)?.weight===4);
   return p?+p.id:0;
 }
 function outcomeAfterUnlock(st,max=500){
   let s=unlockAll(dc(st));
   for(let i=0;i<max;i++){
     const tr=washOnce(s);s=tr.state;
     if(tr.result?.got_gold){
       const pid=purpleFromStep(tr);
       const draws=exchangeSequence(+s.luck_seed,s,15);
       return {state:s,pid,pname:pid?nm(pid):'-',draws,washes:i+1,wasPity:!!tr.result?.was_pity};
     }
   }
   return null;
 }
 function nextNormals(st,count=2){
   let s=unlockAll(dc(st)),out=[],guard=80;
   while(out.length<count&&guard-->0){
     const before=+s.total_talent_bars||0,tr=washOnce(s);s=tr.state;
     const a=(tr.result?.talents||[]).filter(t=>!t.locked);
     for(let i=0;i<a.length&&out.length<count;i++){
       const it=BYID.get(+a[i].id);if(!it||+it.weight===4)continue;
       out.push({rawNo:before+i+1,id:+a[i].id,name:nm(+a[i].id)});
     }
     if(tr.result?.got_gold&&out.length===0)continue;
   }
   return out;
 }

 // Cache the real unlocked pages before the first pity so we do not reconstruct from arrays.
 let s=dc(base),pages=[],guard=2000;
 while(guard-->0){
   const tr=washOnce(s);s=tr.state;
   pages.push({state:dc(s),tr:dc(tr)});
   if(tr.result?.got_gold)break;
 }
 const normalPages=pages.filter(p=>!p.tr.result?.got_gold);
 let best=null;
 const pageStart=Math.max(0,normalPages.length-90);
 for(let pi=normalPages.length-1;pi>=pageStart;pi--){
   const pg=normalPages[pi];
   const normals=(pg.state.talents||[]).filter(t=>+BYID.get(+t.id)?.weight<4);
   for(const slot of normals){
     let b=dc(pg.state);
     b.talents=b.talents.map(t=>({...t,locked:+t.id===+slot.id}));
     if(b.talents.filter(t=>t.locked).length!==1)continue;
     for(let hold=1;hold<=24;hold++){
       let tr;
       try{tr=washOnce(b);b=tr.state}catch(e){break}
       if(tr.result?.got_gold)break;
       const out=outcomeAfterUnlock(b,300);if(!out)continue;
       const same=targetId ? +out.pid===+targetId : out.pname===target;
       if(!same)continue;
       const score=hold*oneLockCost;
       const cand={lockId:+slot.id,lockName:nm(+slot.id),lockWash:+pg.state.total_wash,hold,score,out,after:nextNormals(out.state,2)};
       if(!best||cand.score<best.score||(cand.score===best.score&&cand.lockWash>best.lockWash))best=cand;
       break;
     }
   }
 }

 if(!best){
   h+=`<div class="warn">실제 <b>washOnce 상태 전이</b>로 천장 직전 90회차의 1잠금 경로를 검증했지만, 목표 <b>${target}</b>이 실제 첫 자맥으로 나오는 단일 잠금 경로를 찾지 못했습니다.<br>`+
      `이 경우 “${need}개 생략이면 된다”를 실행 경로로 확정해서 표시하지 않습니다. 복수 잠금/잠금 교체 경로가 필요할 수 있습니다.</div>`;
   box.innerHTML=h;return;
 }
 const firstEx=best.out.draws?.[0]?.name||'-';
 const nxt=best.after.map(x=>`#${x.rawNo} ${x.name}`).join(' · ')||'-';
 h+=`<div class="good"><b>실제 상태 전이 검증 성공</b> · #${best.lockWash}회차 <b>${best.lockName}</b> 잠금 · 잠금 세수 <b>${best.hold}회</b> · 잠금 세수 소모 <b>${best.score}단</b></div>`+
    `<div class="small" style="line-height:1.8;margin-top:7px">실제 첫 자맥: <b>${best.out.pname}</b>${best.out.wasPity?' (천장)':''}<br>`+
    `실제 교체 1: <b>${firstEx}</b><br>그 다음 일반 원시맥: <b>${nxt}</b><br>`+
    `표의 목표와 실제 washOnce 결과가 일치한 경우에만 이 경로를 표시합니다.</div>`;
 box.innerHTML=h;
}'''

new_exchange=r'''async function showDaoExchangeWindowV288(){
 const daoRawBeforeResult=document.getElementById('daoRawBeforeResult');
 const out=document.getElementById('daoExchangeWindowResult');
 if(!out)return;
 if(daoRawBeforeResult)daoRawBeforeResult.innerHTML='';
 out.innerHTML='<div class="warn">천장 직전 6개 참고 seed + 현재 천장 + 다음 원시 자맥 직전까지 교체맥 계산 중...</div>';
 try{
   const d=await daoWindowCachedV288();DAO_V290_WINDOW=d;
   const base=stateFromSave(SAVE,roleObj(),+vipSel.value,rawCalcZizhi());
   const eng=engineFor(base),slots=+QUAL[String(base.zizhi)]?.slots||0;
   if(!slots)throw Error('열린 슬롯 수를 찾지 못했습니다.');

   // Rebuild no-lock normal seed snapshots up to the first pity. These six rows are REFERENCE ONLY.
   let seed=+base.seed,rc=+(base.born_talent_rc||0),intl=!!base.international_wash;
   let talLucky=+base.tal_lucky||0,rawNo=0,washNo=0,guard=200000;
   const preAll=[];
   while(talLucky<+QUAL[String(base.zizhi)]?.base_pity&&guard-->0){
     washNo++;const seen=new Set();let accepted=0;
     while(accepted<slots&&guard-->0){
       let id;[id,seed]=rawNormal(seed,eng,intl?rc:0);if(intl)rc++;
       if(!eng.allowed.has(id)||seen.has(id))continue;
       const it=BYID.get(id);if(!it)continue;
       seen.add(id);accepted++;rawNo++;
       if(+it.weight===4)throw Error(`첫 천장 전 자연 자맥 ${nm(id)}이 나와 현재 분기와 맞지 않습니다.`);
       preAll.push({rawNo,wash:washNo,id,name:nm(id),seedAfter:+seed,rcAfter:+rc});
     }
     talLucky+=slots;
   }
   if(guard<=0)throw Error('첫 천장 이전 seed 계산 한도를 초과했습니다.');
   const preRows=preAll.slice(-6);

   function seqFromSeed(start,count=15){
     let luck=+start,arr=[],g=100000;
     while(arr.length<count&&g-->0){
       let id;[id,luck]=rawPurple(luck,eng);
       if(!eng.allowed.has(id))continue;
       arr.push({id,name:nm(id),seedAfter:+luck});
     }
     return arr;
   }

   const rows=[];
   for(const r of preRows){
     const draws=seqFromSeed(r.seedAfter,15);
     rows.push({...r,kind:'천장 전 참고',zone:'pre',preDistance:Math.max(0,(d.firstPity.rawNo-1)-r.rawNo),needSkip:null,draws,firstDraw:draws[0]?.name||''});
   }

   // Current actual pity row: zero extra raw consumption.
   const pityDraws=exchangeSequence(+d.pityState.luck_seed,d.pityState,15);
   rows.push({rawNo:+d.firstPity.rawNo,wash:+d.firstPity.wash,id:+d.firstPity.id,name:d.firstPity.name,kind:'현재 천장',zone:'pity',needSkip:0,draws:pityDraws,firstDraw:pityDraws[0]?.name||''});

   // Restore the old v2.89 direction: consume normal RNG AFTER the pity seed.
   // Each post-pity normal row is one step farther FORWARD in seed space.
   const baseState=dc(d.pityState),postEng=engineFor(baseState);
   let pseed=+baseState.seed,prc=+(baseState.born_talent_rc||0),pintl=!!baseState.international_wash;
   let praw=+d.firstPity.rawNo,pwash=+baseState.total_wash,stopPurple=null;
   guard=200000;
   while(guard-->0&&!stopPurple){
     pwash++;const seen=new Set();let accepted=0;
     while(accepted<slots&&guard-->0){
       let id;[id,pseed]=rawNormal(pseed,postEng,pintl?prc:0);if(pintl)prc++;
       if(!postEng.allowed.has(id)||seen.has(id))continue;
       const it=BYID.get(id);if(!it)continue;
       seen.add(id);accepted++;praw++;
       if(+it.weight===4){stopPurple={rawNo:praw,wash:pwash,id,name:nm(id)};break}
       const branch=dc(baseState);branch.seed=+pseed;if(pintl)branch.born_talent_rc=+prc;
       const draws=exchangeSequence(+pseed,branch,15);
       const need=Math.max(0,praw-(+d.firstPity.rawNo));
       rows.push({rawNo:praw,wash:pwash,id,name:nm(id),kind:'천장 이후',zone:'post',needSkip:need,draws,firstDraw:draws[0]?.name||''});
     }
     if(pwash%80===0)await uiYield();
   }
   if(!stopPurple)throw Error('다음 원시 자맥을 찾지 못했습니다.');

   DAO_V290_ROUTE_ROWS=rows.map(x=>({...x}));
   let h=`<div class="good"><b>자맥 기준 교체맥 표</b><br><span class="small">`+
     `천장 직전 6개는 <b>이전 seed 참고용</b>이라 생략으로 되돌아갈 수 없습니다. 현재 천장은 생략 0개. `+
     `천장 이후 행은 seed가 앞으로 진행한 만큼 <b>필요 생략 1,2,3…</b>으로 계산합니다. 다음 원시 자맥 <b>#${stopPurple.rawNo} ${stopPurple.name}</b>은 경계라 제외합니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>원시 #</th><th>세수</th><th>구간</th><th>필요 생략</th><th>원시맥</th>';
   for(let i=1;i<=15;i++)h+=`<th>교체 ${i}</th>`;h+='</tr></thead><tbody>';
   for(const r of rows){
     const ns=r.zone==='pre'?'이동 불가':String(r.needSkip??0);
     h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td>${r.kind}</td><td class="num">${ns}</td>`+
       `<td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td>`;
     for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||'-'}</td>`;
     h+='</tr>';
   }
   h+='</tbody></table></div><div id="daoPullRouteV290" class="card" style="margin-top:8px"><div class="small">원시맥을 누르면 필요 생략 수와 실제 washOnce 검증 결과를 표시합니다.</div></div>';
   out.innerHTML=h;
   out.onclick=(ev)=>{
     const btn=ev.target.closest?.('.dao-pull-v295');if(!btn)return;
     ev.preventDefault();const raw=Number(btn.dataset.raw||0),source=decodeURIComponent(btn.dataset.source||'');
     const r=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw&&x.name===source)||DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===raw);
     showDaoPullRouteV290(r?.firstDraw||'',raw,source,1);
   };
 }catch(e){out.innerHTML=`<div class="warn">교체맥 계산 오류: ${String(e&&e.message||e)}</div>`}
}'''

text=text[:start]+new_route+'\n'+new_exchange+text[marker:]

# Update visible button/description only where this exact old label exists.
text=text.replace('2. 자맥 구간별 교체맥 보기','2. 자맥 구간별 교체맥 보기',1)
text=text.replace('첫 천장 직전 6개 + 첫 천장 이후 다음 원시 자맥 직전까지 교체맥 15개 계산 중...','천장 직전 6개 참고 seed + 현재 천장 + 다음 원시 자맥 직전까지 교체맥 계산 중...',1)

for x in ['이전 seed 참고용','필요 생략 1,2,3','실제 washOnce 검증 결과','zone:\'post\'','v3.13']:
 if x not in text: raise SystemExit('v3.13 guard missing: '+x)
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.13','file':'Nangman_Integrated_Simulator_v3_13.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.13',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.13</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v313_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:4000])
print('built v3.13: corrected forward seed direction and exact washOnce route verification')
