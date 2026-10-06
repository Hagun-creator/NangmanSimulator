from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_08.html')
DST=Path('Nangman_Integrated_Simulator_v3_09.html')
if not SRC.exists(): raise SystemExit('v3.08 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.08','v3.09').replace('v3_08','v3_09')
text=re.sub(r'(?<![0-9])3\.08(?![0-9])','3.09',text)
text=re.sub(r'<script id="stable-root-url-v308">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v309">try{if(/Nangman_Integrated_Simulator_v3_09\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Route: simulate the actual one-lock wash cadence. With 3 open slots and one lock,
# each wash keeps the locked talent and consumes only 2 new accepted raws. A same-id
# row is removed only when the cursor actually reaches it while the lock is active.
start=text.find('function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){')
end=text.find('\nasync function showDaoExchangeWindowV288(){',start)
if start<0 or end<0: raise SystemExit('route function not found')
new_route=r'''function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 원시 #700~천장 이후 100 교체맥 표를 계산하세요.</div>';return}
 const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!row||row.postPity){box.innerHTML='<div class="warn">최소루트 계산은 천장 이전 원시맥만 선택할 수 있습니다.</div>';return}
 const target=row.firstDraw||targetName||'';
 const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo&&x.weight<4).map(x=>({...x})).sort((a,b)=>a.rawNo-b.rawNo);
 const currentPrev=pre[pre.length-1]||null;
 if(!currentPrev){box.innerHTML='<div class="warn">현재 천장 직전 일반 자질을 찾지 못했습니다.</div>';return}
 const targetRaw=+sourceRaw;
 const needDel=Math.max(0,(+currentPrev.rawNo)-targetRaw);
 let h=`<div class="good"><b>${sourceName}</b> 기준 → 천장 후보 <b>${target}</b></div>`+
 `<div class="small" style="line-height:1.7;margin:6px 0">기본 천장: <b>#${d.firstPity.rawNo} ${d.firstPity.name}</b><br>현재 천장 직전 일반맥: #${currentPrev.rawNo} ${currentPrev.name}<br>선택한 천장 전 일반 원시맥: #${sourceRaw} ${sourceName}<br>필요한 실제 중복 제거 수: <b>${needDel}개</b></div>`;
 if(needDel<=0){box.innerHTML=h+'<div class="good">추가 중복 제거가 필요 없습니다.</div>';return}

 const slots=+QUAL[String(d.pityState.zizhi)]?.slots||0;
 const oneLockCost=+(COST?.[slots]?.[1]??0);
 if(slots<=1){box.innerHTML=h+'<div class="warn">잠금 세수 계산용 열린 칸 수가 부족합니다.</div>';return}

 // Simulate starting from the original page containing lockRaw.
 // One lock means only (slots-1) new talents are accepted per wash.
 function simulateLock(lockIdx){
   const lock=pre[lockIdx];
   const pageStart=Math.floor(lockIdx/slots)*slots;
   let cursor=Math.min(pre.length,pageStart+slots),washes=0,totalDeleted=0;
   const pages=[];
   while(cursor<pre.length && washes<300 && totalDeleted<needDel){
     washes++;
     const seen=new Set([+lock.id]);
     const accepted=[],skipped=[];
     while(accepted.length<slots-1 && cursor<pre.length){
       const r=pre[cursor++];
       if(seen.has(+r.id)){
         skipped.push(r);totalDeleted++;
         continue;
       }
       seen.add(+r.id);accepted.push(r);
     }
     pages.push({wash:washes,accepted,skipped,cursorRaw:cursor<pre.length?pre[cursor].rawNo:null,totalDeleted});
   }
   return {lock,washes,totalDeleted,pages,pageStartRaw:pre[pageStart]?.rawNo||lock.rawNo};
 }

 // Closest-to-pity lock first, but only accept a route when the requested number of
 // duplicate skips actually occurs in the simulated locked washes.
 let best=null;
 for(let i=pre.length-1;i>=0;i--){
   const r=pre[i];
   if(+r.rawNo>=+d.firstPity.rawNo)continue;
   const sim=simulateLock(i);
   if(sim.totalDeleted>=needDel){best=sim;break}
 }

 if(!best){
   h+=`<div class="warn">실제 잠금 세수 방식(잠금 1칸 유지 + 매회 새 원시 ${slots-1}개 채움)으로 천장에 가까운 원시맥부터 확인했지만, <b>한 종류의 맥을 계속 잠그는 경로</b>에서는 ${needDel}개 제거를 완성하지 못했습니다. 여러 번 잠금 대상을 바꾸는 연쇄 경로는 아직 확정으로 표시하지 않습니다.</div>`;
   box.innerHTML=h;return;
 }

 const shown=[];let got=0;
 for(const p of best.pages){shown.push(p);got=p.totalDeleted;if(got>=needDel)break}
 const total=shown.length*oneLockCost;
 h+=`<div class="good"><b>실제 잠금 세수 경로</b> · #${best.lock.rawNo} <b>${best.lock.name}</b> 잠금 · 세수 <b>${shown.length}회</b> · 중복 제거 <b>${needDel}개</b> · 추가 소모 <b>${total}단</b></div>`;
 h+=`<div class="small" style="margin-top:7px">시작 3칸: #${best.pageStartRaw}부터 원래 ${slots}칸 페이지 · 잠금 후에는 매 세수마다 잠금맥을 유지하고 새 원시 ${slots-1}개만 채웁니다.</div>`;
 h+='<div class="card" style="padding:10px;margin-top:8px"><b>실행/검증 순서</b><ol style="margin:7px 0 0 20px;padding:0">';
 for(const p of shown){
   const acc=p.accepted.map(x=>`#${x.rawNo} ${x.name}`).join(' · ')||'-';
   const sk=p.skipped.map(x=>`#${x.rawNo} ${x.name}`).join(' · ');
   h+=`<li style="margin:6px 0"><b>${p.wash}회차</b>: #${best.lock.rawNo} ${best.lock.name} 잠금 유지 + 새 칸 ${acc}${sk?`<br><span class="good">이 회차 중복 스킵: ${sk}</span>`:''}</li>`;
 }
 h+='</ol></div>';
 h+=`<div class="small" style="line-height:1.7;margin-top:8px">예: 3칸에서 #833을 잠그고 시작 페이지가 #832·#833·#834라면 1회차는 #835·#836까지만 채웁니다. #837이 같은 맥이면 2회차에서 실제로 #837까지 커서가 도달했을 때만 중복 제거로 계산합니다.</div>`;
 box.innerHTML=h;
}'''
text=text[:start]+new_route+text[end:]

# Extend the validation table: keep pre-pity #700..predecessor and append 100 normal
# raw candidates after the pity boundary. Post-pity rows are validation-only and are
# not clickable for the pre-pity pull-route calculation.
# Insert generation immediately after usable pre-pity candidates are formed.
old="""   const usable=candidates.filter(x=>+x.rawNo<=+currentPrev.rawNo).sort((a,b)=>a.rawNo-b.rawNo);
   if(!usable.length)throw Error('원시 #700 이후 천장 직전 후보 일반맥이 없습니다.');
"""
new="""   const usablePre=candidates.filter(x=>+x.rawNo<=+currentPrev.rawNo).sort((a,b)=>a.rawNo-b.rawNo);
   if(!usablePre.length)throw Error('원시 #700 이후 천장 직전 후보 일반맥이 없습니다.');

   // Validation extension: continue the normal raw stream for 100 accepted raws after pity.
   // Purple pity/exchange uses luck_seed; the ordinary raw seed continues independently.
   const post=[];
   let postSeed=+seed,postRc=+rc,postRaw=+currentPrev.rawNo,postWash=washNo;
   while(post.length<100&&guard-->0){
     postWash++;
     const seenPost=new Set();let acceptedPost=0;
     while(acceptedPost<slots&&post.length<100&&guard-->0){
       let id;[id,postSeed]=rawNormal(postSeed,eng,intl?postRc:0);if(intl)postRc++;
       if(!eng.allowed.has(id)||seenPost.has(id))continue;
       const it=BYID.get(id);if(!it)continue;
       seenPost.add(id);acceptedPost++;postRaw++;
       post.push({rawNo:postRaw,wash:postWash,id,name:nm(id),seedAfter:+postSeed,rcAfter:+postRc,postPity:true,afterPity:postRaw-(+currentPrev.rawNo)});
     }
   }
   if(post.length<100)throw Error('천장 이후 검증용 원시맥 100개 생성 한도를 초과했습니다.');
   const usable=[...usablePre,...post];
"""
if old not in text: raise SystemExit('usable block not found')
text=text.replace(old,new,1)

# Route rows: post-pity rows have no "need skip" meaning.
old2="""   const routeRows=rows.map(r=>({
     ...r,
     firstDraw:r.pity?.name||'',
     shift:Math.max(0,(+currentPrev.rawNo)-(+r.rawNo))
   }));
"""
new2="""   const routeRows=rows.map(r=>({
     ...r,
     firstDraw:r.pity?.name||'',
     postPity:!!r.postPity,
     shift:r.postPity?null:Math.max(0,(+currentPrev.rawNo)-(+r.rawNo))
   }));
"""
if old2 not in text: raise SystemExit('routeRows block not found')
text=text.replace(old2,new2,1)

text=text.replace('첫 천장 이전 원시 #700~#${currentPrev.rawNo} 원시맥별 교체맥 표','원시 #700~천장 직전 + 천장 이후 100개 원시맥별 교체맥 검증표',1)
text=text.replace('원시 #700부터 첫 천장 직전까지 원시맥별 천장/교체맥 15개 계산 중... 원시 #700부터 순서대로 처리합니다.','원시 #700부터 천장 직전 + 천장 이후 100개까지 천장/교체맥 15개 계산 중...',1)

# Make post-pity rows visibly validation-only.
oldrow='''     h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td class="num">${rr?.shift??'-'}</td>`+\n       `<td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td>`+\n       `<td class="q4"><b>${r.pity?.name||'-'}</b></td>`;'''
if oldrow not in text:
    # literal source in file has normal newlines, use regex replacement
    pat=re.compile(r'''     h\+=`<tr><td class="num">\$\{r\.rawNo\}</td><td class="num">\$\{r\.wash\}</td><td class="num">\$\{rr\?\.shift\?\?'-'\}</td>`\+\n       `<td><button type="button" class="linkBtn dao-pull-v295" data-raw="\$\{r\.rawNo\}" data-source="\$\{encodeURIComponent\(r\.name\)\}"><b>\$\{r\.name\}</b></button></td>`\+\n       `<td class="q4"><b>\$\{r\.pity\?\.name\|\|'-'\}</b></td>`;''')
    m=pat.search(text)
    if not m: raise SystemExit('table row renderer not found')
    repl='''     h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td class="num">${r.postPity?`천장후 +${r.afterPity}`:(rr?.shift??'-')}</td>`+\n       (r.postPity?`<td><b>${r.name}</b> <span class="small">(검증)</span></td>`:`<td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td>`)+\n       `<td class="q4"><b>${r.pity?.name||'-'}</b></td>`;'''
    text=text[:m.start()]+repl+text[m.end():]
else:
    text=text.replace(oldrow,'''     h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td class="num">${r.postPity?`천장후 +${r.afterPity}`:(rr?.shift??'-')}</td>`+\n       (r.postPity?`<td><b>${r.name}</b> <span class="small">(검증)</span></td>`:`<td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td>`)+\n       `<td class="q4"><b>${r.pity?.name||'-'}</b></td>`;''',1)

# Update button label/description so the validation range is explicit.
text=text.replace('2. 원시 #700~천장 직전 교체맥 보기','2. 원시 #700~천장 이후 100 교체맥 보기',1)
text=text.replace('2번은 원시 #700부터 천장 직전 일반맥까지 각 원시맥 직후 seed를 기준으로 천장 자맥과 교체맥 15개를 표시합니다.','2번은 원시 #700부터 천장 직전까지 유지하고 천장 이후 일반 원시맥 100개를 추가해 각 원시맥 직후 seed 기준 천장 자맥과 교체맥 15개를 검증할 수 있게 표시합니다.',1)

for x in [
 '2. 원시 #700~천장 이후 100 교체맥 보기',
 'post.length<100',
 '잠금 유지 + 새 칸',
 '1회차는 #835·#836까지만 채웁니다',
 'r.postPity?`천장후 +${r.afterPity}`',
 'sort((a,b)=>a.rawNo-b.rawNo)'
]:
 if x not in text: raise SystemExit('v3.09 guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.09','file':'Nangman_Integrated_Simulator_v3_09.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.09',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.09</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v309_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2500])
print('built v3.09: locked-wash cadence route + pre700/pity+100 validation table')
