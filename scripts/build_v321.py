from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_20.html')
DST=Path('Nangman_Integrated_Simulator_v3_21.html')
if not SRC.exists(): raise SystemExit('v3.20 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.20','v3.21').replace('v3_20','v3_21')
text=re.sub(r'(?<![0-9])3\.20(?![0-9])','3.21',text)
text=re.sub(r'<script id="stable-root-url-v320">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v321">try{if(/Nangman_Integrated_Simulator_v3_21\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Range UI: raw #600 through the first 6 ACTUAL normal raws after first pity.
text=text.replace('2. 원시 #700~천장 직전 교체맥 보기','2. 원시 #600~천장 이후 6개 교체맥 보기')
text=text.replace('원시 #700부터 천장 직전 일반맥까지','원시 #600부터 천장 이후 일반 원시맥 6개까지')
text=text.replace('원시 #700~천장 직전 교체맥 표','원시 #600~천장 이후 6개 교체맥 표')
text=text.replace('원시 #700~천장 직전','원시 #600~천장 이후 6개')

# Replace only button 2's generator. Preserve route/min-cost engine from v3.20.
a=text.find('async function showDaoExchangeWindowV288(){')
b=text.find('\n\nasync function analyzeFirstPityDaomai()',a)
if b<0: b=text.find('\nasync function analyzeFirstPityDaomai()',a)
if a<0 or b<0: raise SystemExit('showDaoExchangeWindowV288 boundary missing')
new_func=r'''async function showDaoExchangeWindowV288(){
 const daoRawBeforeResult=document.getElementById('daoRawBeforeResult');
 const daoExchangeWindowResult=document.getElementById('daoExchangeWindowResult');
 if(!daoExchangeWindowResult){console.error('daoExchangeWindowResult not found');return;}
 if(daoRawBeforeResult)daoRawBeforeResult.innerHTML='';
 const cacheKey=daoV296Key()+'|raw600-post6-v321';
 if(DAO_V296_EXCHANGE_CACHE&&DAO_V296_EXCHANGE_CACHE.key===cacheKey){
   renderDaoExchangeV296(DAO_V296_EXCHANGE_CACHE.pack);return;
 }
 daoExchangeWindowResult.innerHTML='<div class="warn">원시 #600부터 천장 이후 실제 일반 원시맥 6개까지 천장/교체맥 15개 계산 중...</div>';
 try{
   const d=await daoWindowCachedV288();DAO_V290_WINDOW=d;
   const base=stateFromSave(SAVE,roleObj(),+document.getElementById('vipSel').value,rawCalcZizhi());
   const slots=+QUAL[String(base.zizhi)]?.slots||0;
   const pityAt=+QUAL[String(base.zizhi)]?.base_pity||0;
   if(slots<=0)throw Error('원시 자맥 탭에서 계산용 칸을 1칸 이상 개방하세요.');
   if(!pityAt)throw Error('현재 개방 칸에는 천장 기준이 없습니다.');
   const eng=engineFor(base);
   let seed=+base.seed,rc=+(base.born_talent_rc||0),intl=!!base.international_wash;
   let talLucky=+base.tal_lucky||0,rawNo=0,washNo=0,guard=200000;
   const preCandidates=[];
   const minRaw=600;

   // Exact pre-pity normal stream, beginning at raw #600.
   while(talLucky<pityAt&&guard-->0){
     washNo++;
     const seen=new Set();let accepted=0;
     while(accepted<slots&&guard-->0){
       let id;[id,seed]=rawNormal(seed,eng,intl?rc:0);if(intl)rc++;
       if(!eng.allowed.has(id)||seen.has(id))continue;
       const it=BYID.get(id);if(!it)continue;
       if(+it.weight===4)throw Error(`원시 #${rawNo+1}에서 자연 자맥 ${nm(id)}이 천장보다 먼저 나옵니다. 첫 자맥=천장 도맥법 분기 대상이 아닙니다.`);
       seen.add(id);accepted++;rawNo++;
       if(rawNo>=minRaw)preCandidates.push({rawNo,wash:washNo,id,name:nm(id),seedAfter:+seed,rcAfter:+rc,side:'pre'});
     }
     talLucky+=slots;
     if(washNo%80===0)await uiYield();
   }
   if(guard<=0)throw Error('원시 #600 이후 천장 흐름 계산 한도를 초과했습니다.');

   const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo&&x.weight<4);
   const currentPrev=pre[pre.length-1]||null;
   if(!currentPrev)throw Error('현재 천장 직전 일반 자질을 찾지 못했습니다.');
   const preUsable=preCandidates.filter(x=>+x.rawNo<=+currentPrev.rawNo);

   // Take ONLY the first six actual normal raws after pity. d.rows is authoritative visible order.
   const postActual=d.rows.filter(x=>+x.rawNo>+d.firstPity.rawNo&&+x.weight<4).slice(0,6);
   if(postActual.length<6)throw Error(`천장 이후 일반 원시맥을 6개 찾지 못했습니다. 현재 ${postActual.length}개만 확인됩니다.`);
   const postCandidates=[];

   // Same-pity-wash trailing normals: replay from exact state immediately before pity.
   const same=postActual.filter(x=>+x.wash===+d.firstPity.wash);
   if(same.length){
     if(!d.pityBeforeState)throw Error('천장 직전 상태가 없어 천장 동일 회차 후속 원시맥 seed를 복원할 수 없습니다.');
     const st=dc(d.pityBeforeState),e=engineFor(st);
     let s=+st.seed,r=+(st.born_talent_rc||0),ii=!!st.international_wash;
     const seen=new Set([+d.firstPity.id]);
     for(const want of same){
       let ok=false,g=100000;
       while(g-->0){
         let id;[id,s]=rawNormal(s,e,ii?r:0);if(ii)r++;
         if(!e.allowed.has(id)||seen.has(id))continue;
         const it=BYID.get(id);if(!it||+it.weight===4)continue;
         seen.add(id);
         if(+id!==+want.id)throw Error(`천장 동일 회차 원시맥 재현 불일치: #${want.rawNo} ${want.name} / 재현 ${nm(id)}.`);
         postCandidates.push({rawNo:+want.rawNo,wash:+want.wash,id:+want.id,name:want.name,seedAfter:+s,rcAfter:+r,side:'post'});
         ok=true;break;
       }
       if(!ok)throw Error(`#${want.rawNo} ${want.name} seed 복원 한도를 초과했습니다.`);
     }
   }

   // Later washes: pityState is exact state after the pity wash (including same-page trailing raws).
   const later=postActual.filter(x=>+x.wash>+d.firstPity.wash);
   if(later.length){
     const st=dc(d.pityState),e=engineFor(st);
     let s=+st.seed,r=+(st.born_talent_rc||0),ii=!!st.international_wash;
     let p=0,g=200000,currentWash=null,seen=new Set();
     while(p<later.length&&g-->0){
       const want=later[p];
       if(currentWash!==+want.wash){currentWash=+want.wash;seen=new Set();}
       let id;[id,s]=rawNormal(s,e,ii?r:0);if(ii)r++;
       if(!e.allowed.has(id)||seen.has(id))continue;
       const it=BYID.get(id);if(!it)continue;
       if(+it.weight===4)continue;
       seen.add(id);
       if(+id!==+want.id)throw Error(`천장 이후 원시 흐름 재현 불일치: #${want.rawNo} ${want.name} / 재현 ${nm(id)}.`);
       postCandidates.push({rawNo:+want.rawNo,wash:+want.wash,id:+want.id,name:want.name,seedAfter:+s,rcAfter:+r,side:'post'});
       p++;
     }
     if(p<later.length)throw Error('천장 이후 원시 흐름 seed 복원 한도를 초과했습니다.');
   }
   postCandidates.sort((x,y)=>x.rawNo-y.rawNo);
   if(postCandidates.length!==6)throw Error(`천장 이후 seed 복원 결과가 6개가 아닙니다: ${postCandidates.length}개.`);

   function purpleFromSeed(startSeed,count){
     let luck=+startSeed,out=[],spins=0;
     while(out.length<count&&spins++<200000){
       let id;[id,luck]=rawPurple(luck,eng);if(!eng.allowed.has(id))continue;
       out.push({id,name:nm(id),seedAfter:+luck});
     }
     return {rows:out,lastSeed:+luck};
   }

   // Show closest pre-pity raws first, then the six verified post-pity raws.
   const usable=[...preUsable.sort((x,y)=>y.rawNo-x.rawNo),...postCandidates];
   if(!usable.length)throw Error('표시 가능한 원시맥 후보가 없습니다.');
   const rows=[];
   for(let i=0;i<usable.length;i++){
     const c=usable[i],p=purpleFromSeed(c.seedAfter,16);
     if(p.rows.length<1)continue;
     rows.push({...c,kind:'원시',pity:p.rows[0],draws:p.rows.slice(1,16),luckStart:+c.seedAfter});
     if(i%120===119)await uiYield();
   }
   if(!rows.length)throw Error('표시 가능한 천장/교체맥 결과가 없습니다.');

   const routeRows=rows.map(r=>({
     ...r,firstDraw:r.pity?.name||'',
     shift:r.side==='pre'?Math.max(0,(+currentPrev.rawNo)-(+r.rawNo)):(+r.rawNo)-(+d.firstPity.rawNo),
     shiftText:r.side==='pre'?String(Math.max(0,(+currentPrev.rawNo)-(+r.rawNo))):`천장 후 +${(+r.rawNo)-(+d.firstPity.rawNo)}`
   }));

   let h=`<div class="good"><b>원시 #600 ~ 천장 이후 일반 원시맥 6개</b><br>`+
     `<span class="small">천장 전은 #600부터 직전 일반맥까지, 천장 후는 <b>washOnce() 실제 흐름으로 검증된 일반 원시맥 6개</b>만 표시합니다. 각 행은 해당 원시맥 직후 seed 기준의 <b>자맥 후보 + 교체 1~15</b>입니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>원시 #</th><th>세수 회차</th><th>위치/생략</th><th>원시맥</th><th>자맥 후보</th>';
   for(let i=1;i<=15;i++)h+=`<th>교체 ${i}</th>`;
   h+='</tr></thead><tbody>';
   let postDivider=false;
   for(const r of rows){
     const rr=routeRows.find(x=>+x.rawNo===+r.rawNo);
     const divider=(r.side==='post'&&!postDivider);if(divider)postDivider=true;
     h+=`<tr${divider?' style="border-top:4px solid currentColor"':''}><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td class="num">${rr?.shiftText??'-'}</td>`+
       `<td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td>`+
       `<td class="q4"><b>${r.pity?.name||'-'}</b></td>`;
     for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||'-'}</td>`;
     h+='</tr>';
   }
   h+='</tbody></table></div>';
   h+='<div class="small" style="margin-top:7px">굵은 구분선 아래가 천장 이후 6개입니다. 천장 이후도 실제 원시 순서와 seed를 재현해 계산하며 추정값은 표시하지 않습니다.</div>';
   h+='<section id="daoPullRouteBoxV298" class="card" style="margin-top:14px;padding:12px">'+
      '<div style="font-weight:800;margin-bottom:8px">잡맥법 최소 세수단 경로</div>'+
      '<div id="daoPullRouteV290" class="small">위 표에서 원하는 <b>원시맥</b>을 누르면 해당 seed를 목표로 기존 최소비용 탐색을 실행합니다.</div>'+
      '</section>';
   const pack={window:d,routeRows,html:h};
   DAO_V296_EXCHANGE_CACHE={key:cacheKey,pack};renderDaoExchangeV296(pack);
 }catch(e){daoExchangeWindowResult.innerHTML=`<div class="warn">${e.message||e}</div>`}
}'''
text=text[:a]+new_func+text[b:]

# Focused copy fixes left by older versions.
text=text.replace('원시 #700부터 첫 천장 직전까지 원시맥별 천장/교체맥 15개 계산 중... 천장에 가까운 원시맥부터 처리합니다.',
                  '원시 #600부터 천장 이후 실제 일반 원시맥 6개까지 천장/교체맥 15개 계산 중...')
text=text.replace('첫 천장 이전 원시 #700~#${currentPrev.rawNo} 원시맥별 교체맥 표','원시 #600 ~ 천장 이후 일반 원시맥 6개')

# Regression/feature guards.
for x in [
 '2. 원시 #600~천장 이후 6개 교체맥 보기','const minRaw=600;','slice(0,6)',
 'pityBeforeState','washOnce() 실제 흐름으로 검증된 일반 원시맥 6개','postCandidates.length!==6',
 'for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||\'-\'}</td>`;',
 'class="linkBtn dao-pull-v295"','잡맥법 최소 세수단 경로','renderDaoSearchProgressV320',
 'readCurrentPillBalanceV320','현재 검색 <b>#${info.searchNo.toLocaleString()}</b>'
]:
 if x not in text: raise SystemExit('v3.21 guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.21','file':'Nangman_Integrated_Simulator_v3_21.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.21',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.21</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v321_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.21: raw #600 through six verified post-pity normals')
