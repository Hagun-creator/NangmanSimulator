from pathlib import Path
import re, base64, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v2_99.html')
DST=Path('Nangman_Integrated_Simulator_v3_01.html')
if not SRC.exists(): raise SystemExit('v2.99 source missing')
text=SRC.read_text(encoding='utf-8')

# Version bump from the known-good v2.99 baseline.
text=text.replace('v2.99','v3.01').replace('v2_99','v3_01')
text=re.sub(r'(?<![0-9])2\.99(?![0-9])','3.01',text)
text=re.sub(r'<script id="stable-root-url-v299">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v301">try{if(/Nangman_Integrated_Simulator_v3_01\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Keep equipment behavior untouched; synchronize only visible version strings inside payload.
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace')
inner=inner.replace('v2.99','v3.01').replace('v2_99','v3_01')
inner=re.sub(r'(?<![0-9])2\.99(?![0-9])','3.01',inner)
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{base64.b64encode(inner.encode()).decode()}";'+text[m.end():]

# Keep the v2.99 two-button layout. Only change button 2's source window/description.
old_ui='''<button id="daoRawBeforeBtn">1. 천장 전 모든 원시맥 보기</button>\n<button id="daoExchangeWindowBtn">2. 천장 포함 이후 교체맥 보기</button>\n</div>\n<div class="small" style="margin-bottom:10px">첫 원시 자맥이 천장인 경우만 계산합니다. 1번은 첫 천장 직전까지의 모든 원시맥, 2번은 천장맥 자체를 포함해 다음 원시 자맥 직전까지의 교체맥만 표시합니다.</div>'''
new_ui='''<button id="daoRawBeforeBtn">1. 천장 전 모든 원시맥 보기</button>\n<button id="daoExchangeWindowBtn">2. 원시 #600~천장 직전 교체맥 보기</button>\n</div>\n<div class="small" style="margin-bottom:10px">첫 원시 자맥이 천장인 경우만 계산합니다. 1번은 첫 천장 직전까지의 모든 원시맥을 그대로 표시하고, 2번은 원시 #600부터 천장 직전 일반맥까지 각 원시맥 직후 seed를 기준으로 천장 자맥과 교체맥 15개를 표시합니다. 표의 원시맥을 누르면 기존 잡맥법 최소 세수단 경로를 그대로 계산합니다.</div>'''
if old_ui not in text: raise SystemExit('v2.99 two-button daomai UI not found')
text=text.replace(old_ui,new_ui,1)

# Replace only the second-button calculation function. Button 1 and route engine stay intact.
start=text.find('async function showDaoExchangeWindowV288(){')
end=text.find('\n\nasync function analyzeFirstPityDaomai()',start)
if start<0 or end<0: raise SystemExit('showDaoExchangeWindowV288 block not found')
new_func=r'''async function showDaoExchangeWindowV288(){
 daoRawBeforeResult.innerHTML='';
 const cacheKey=daoV296Key()+'|pre600-v301';
 if(DAO_V296_EXCHANGE_CACHE&&DAO_V296_EXCHANGE_CACHE.key===cacheKey){
   renderDaoExchangeV296(DAO_V296_EXCHANGE_CACHE.pack);
   return;
 }
 daoExchangeWindowResult.innerHTML='<div class="warn">원시 #600부터 첫 천장 직전까지 원시맥별 천장/교체맥 15개 계산 중...</div>';
 try{
   const d=await daoWindowCachedV288();DAO_V290_WINDOW=d;
   const base=stateFromSave(SAVE,roleObj(),+vipSel.value,rawCalcZizhi());
   const slots=+QUAL[String(base.zizhi)]?.slots||0;
   const pityAt=+QUAL[String(base.zizhi)]?.base_pity||0;
   if(slots<=0)throw Error('원시 자맥 탭에서 계산용 칸을 1칸 이상 개방하세요.');
   if(!pityAt)throw Error('현재 개방 칸에는 천장 기준이 없습니다.');

   const eng=engineFor(base);
   let seed=+base.seed,rc=+(base.born_talent_rc||0),intl=!!base.international_wash;
   let talLucky=+base.tal_lucky||0,rawNo=0,washNo=0,guard=200000;
   const candidates=[];
   const minRaw=600;

   // Pre-pity normal stream: identical semantics to the older #600+ daomai table.
   while(talLucky<pityAt&&guard-->0){
     washNo++;
     const seen=new Set();
     let accepted=0;
     while(accepted<slots&&guard-->0){
       let id;
       [id,seed]=rawNormal(seed,eng,intl?rc:0);
       if(intl)rc++;
       if(!eng.allowed.has(id)||seen.has(id))continue;
       const it=BYID.get(id);if(!it)continue;
       if(+it.weight===4)throw Error(`원시 #${rawNo+1}에서 자연 자맥 ${nm(id)}이 천장보다 먼저 나옵니다. 첫 자맥=천장 도맥법 분기 대상이 아닙니다.`);
       seen.add(id);accepted++;rawNo++;
       if(rawNo>=minRaw)candidates.push({rawNo,wash:washNo,id,name:nm(id),seedAfter:+seed,rcAfter:+rc});
     }
     talLucky+=slots;
     if(washNo%80===0)await uiYield();
   }
   if(guard<=0)throw Error('원시 #600 이후 천장 직전 흐름 계산 한도를 초과했습니다.');

   const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo&&x.weight<4);
   const currentPrev=pre[pre.length-1]||null;
   if(!currentPrev)throw Error('현재 천장 직전 일반 자질을 찾지 못했습니다.');
   const usable=candidates.filter(x=>+x.rawNo<=+currentPrev.rawNo);
   if(!usable.length)throw Error('원시 #600 이후 천장 직전 후보 일반맥이 없습니다.');

   function purpleFromSeed(startSeed,count){
     let luck=+startSeed,out=[],spins=0;
     while(out.length<count&&spins++<200000){
       let id;[id,luck]=rawPurple(luck,eng);
       if(!eng.allowed.has(id))continue;
       out.push({id,name:nm(id),seedAfter:+luck});
     }
     return {rows:out,lastSeed:+luck};
   }

   const rows=[];
   for(let i=0;i<usable.length;i++){
     const c=usable[i];
     const p=purpleFromSeed(c.seedAfter,16); // 천장 자맥 1 + 교체 15
     if(p.rows.length<1)continue;
     rows.push({...c,kind:'원시',pity:p.rows[0],draws:p.rows.slice(1,16),luckStart:+c.seedAfter});
     if(i%120===119)await uiYield();
   }
   if(!rows.length)throw Error('표시 가능한 천장/교체맥 결과가 없습니다.');

   const routeRows=rows.map(r=>({
     ...r,
     firstDraw:r.pity?.name||'',
     shift:Math.max(0,(+currentPrev.rawNo)-(+r.rawNo))
   }));

   let h=`<div class="good"><b>첫 천장 이전 원시 #600~#${currentPrev.rawNo} 원시맥별 교체맥 표</b><br>`+
     `<span class="small">각 행은 해당 원시맥이 천장 직전 일반맥이 되도록 뒤의 일반맥을 생략했을 때의 직후 seed를 기준으로 계산합니다. <b>천장 자맥</b>과 그 뒤 <b>교체 1~15</b>를 표시하며, 원시맥 버튼을 누르면 기존 잡맥법 최소 세수단 경로 계산을 그대로 사용합니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>원시 #</th><th>세수 회차</th><th>필요 생략</th><th>원시맥</th><th>천장 자맥</th>';
   for(let i=1;i<=15;i++)h+=`<th>교체 ${i}</th>`;
   h+='</tr></thead><tbody>';
   for(const r of rows){
     const rr=routeRows.find(x=>+x.rawNo===+r.rawNo);
     h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td class="num">${rr?.shift??'-'}</td>`+
       `<td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td>`+
       `<td class="q4"><b>${r.pity?.name||'-'}</b></td>`;
     for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||'-'}</td>`;
     h+='</tr>';
   }
   h+='</tbody></table></div>';
   h+='<div class="small" style="margin-top:7px">같은 이름의 일반맥도 원시 위치가 다르면 seed가 달라질 수 있으므로 원시 #별로 별도 계산합니다.</div>';
   h+='<section id="daoPullRouteBoxV298" class="card" style="margin-top:14px;padding:12px">'+
      '<div style="font-weight:800;margin-bottom:8px">잡맥법 최소 세수단 경로</div>'+
      '<div id="daoPullRouteV290" class="small">위 표에서 원하는 <b>원시맥</b>을 누르면 그 원시맥을 천장 직전으로 당기는 기존 최소소모 루트를 계산합니다.</div>'+
      '</section>';
   const pack={window:d,routeRows,html:h};
   DAO_V296_EXCHANGE_CACHE={key:cacheKey,pack};
   renderDaoExchangeV296(pack);
 }catch(e){daoExchangeWindowResult.innerHTML=`<div class="warn">${e.message||e}</div>`}
}'''
text=text[:start]+new_func+text[end:]

# Route engine is preserved; only adapt labels/no-op wording to the pre-pity source rows.
text=text.replace("먼저 천장 이후 교체맥 표를 계산하세요.","먼저 원시 #600~천장 직전 교체맥 표를 계산하세요.")
text=text.replace("선택한 천장 이후 일반 원시맥:","선택한 천장 전 일반 원시맥:")
text=text.replace("if(needDel<=0){box.innerHTML=h+'<div class=\"warn\">기본 천장 행은 변경 대상이 아닙니다.</div>';return}",
                  "if(needDel<=0){box.innerHTML=h+'<div class=\"good\">선택한 원시맥이 이미 현재 천장 직전 일반맥이므로 추가 잡맥 생략이 필요 없습니다.</div>';return}")

# Guard requested behavior: button 1 intact, button 2 pre-pity #600+, click-to-route intact.
for x in [
  '<button id="daoRawBeforeBtn">1. 천장 전 모든 원시맥 보기</button>',
  'daoRawBeforeBtn.onclick=showDaoRawBeforeV288',
  'daoExchangeWindowBtn.onclick=showDaoExchangeWindowV288',
  'const minRaw=600;',
  'shift:Math.max(0,(+currentPrev.rawNo)-(+r.rawNo))',
  'class="linkBtn dao-pull-v295"',
  'showDaoPullRouteV290(row?.firstDraw||\'\',raw,source,1);',
  '잡맥법 최소 세수단 경로',
  'daoPullRouteBoxV298'
]:
  if x not in text: raise SystemExit('v3.01 regression guard missing: '+x)
if '천장 포함 이후 교체맥 보기' in text: raise SystemExit('old post-pity button label remains')

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.01','file':'Nangman_Integrated_Simulator_v3_01.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.01',s);r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.01</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
  p=Path(f'/tmp/v301_app_{i}.js');p.write_text(js,encoding='utf-8')
  cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
  if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.01: keep pre-pity raw list + switch exchange table to raw #600..pity-predecessor + preserve route click')
