from pathlib import Path
import re, base64, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v2_95.html')
DST=Path('Nangman_Integrated_Simulator_v2_96.html')
if not SRC.exists(): raise SystemExit('v2.95 source missing')
text=SRC.read_text(encoding='utf-8')

# 1) First-pity raw table: visually group rows in sets of 3, matching the real 3-slot wash page.
a=text.find('async function showDaoRawBeforeV288(){')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('showDaoRawBeforeV288 boundary missing')
new_raw=r'''async function showDaoRawBeforeV288(){
 daoRawBeforeResult.innerHTML='<div class="warn">첫 천장 전 원시맥 계산 중...</div>';
 daoExchangeWindowResult.innerHTML='';
 try{
   const d=await daoWindowCachedV288();
   const rows=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo);
   let h=`<div class="good"><b>첫 천장</b>: 원시 #${d.firstPity.rawNo} ${d.firstPity.name}<br><span class="small">아래 표는 천장 행을 제외한 직전까지의 모든 원시맥입니다. 실제 세수 3칸 단위처럼 <b>3행씩 굵은 구분선</b>으로 묶었습니다.</span></div>`;
   h+='<div class="scroll"><table class="dao-raw-v296"><thead><tr><th>원시 #</th><th>세수 회차</th><th>맥 이름</th><th>등급</th><th>계열(type)</th></tr></thead><tbody>';
   for(let i=0;i<rows.length;i++){
     const x=rows[i], group=Math.floor(i/3)+1;
     const top=(i%3===0)?' style="border-top:3px solid currentColor"':'';
     h+=`<tr${top} data-group="${group}"><td class="num">${x.rawNo}</td><td class="num">${x.wash}</td><td class="q${Math.max(1,Math.min(4,x.weight))}">${x.name}</td><td>${qualityLabel(x.weight)}</td><td>${x.type}</td></tr>`;
   }
   h+='</tbody></table></div>';
   daoRawBeforeResult.innerHTML=h;
 }catch(e){daoRawBeforeResult.innerHTML=`<div class="warn">${e.message||e}</div>`}
}'''
text=text[:a]+new_raw+text[b:]

# 2) Post-pity exchange table cache. Insert before the known v2.95 route helpers.
anchor='function daoDeleteCandidatesV295(d){'
if anchor not in text: raise SystemExit('daoDeleteCandidatesV295 anchor missing')
text=text.replace(anchor,'let DAO_V296_EXCHANGE_CACHE=null;\n'+anchor,1)

# 3) Replace the post-pity table generator.
#    Visible raw names/order come from daoFirstPityWindowV288(), which already uses washOnce().
#    For rows after the pity wash, replay only the deterministic accepted-normal seed progression
#    to capture each row's exact branch state for exchange 1~15; do not synthesize a new visible raw order.
a=text.find('async function showDaoExchangeWindowV288(){')
b=text.find('\n}\n\nasync function analyzeFirstPityDaomai()',a)
if a<0 or b<0: raise SystemExit('showDaoExchangeWindowV288 boundary missing')
b+=3
new_exchange=r'''function daoV296Key(){
 return [roleSel?.value||'',vipSel?.value||'',rawCalcZizhi(),JSON.stringify(SPECIAL_STATE||{})].join('|');
}
function renderDaoExchangeV296(pack){
 DAO_V290_WINDOW=pack.window;
 DAO_V290_ROUTE_ROWS=pack.routeRows.map(x=>({...x,draws:(x.draws||[]).map(y=>({...y}))}));
 daoExchangeWindowResult.innerHTML=pack.html;
}
async function showDaoExchangeWindowV288(){
 daoRawBeforeResult.innerHTML='';
 const cacheKey=daoV296Key();
 if(DAO_V296_EXCHANGE_CACHE&&DAO_V296_EXCHANGE_CACHE.key===cacheKey){
   renderDaoExchangeV296(DAO_V296_EXCHANGE_CACHE.pack);
   return;
 }
 daoExchangeWindowResult.innerHTML='<div class="warn">천장 이후 실제 원시 흐름과 교체맥 15개 계산 중... 최초 1회만 계산합니다.</div>';
 try{
   const d=await daoWindowCachedV288();DAO_V290_WINDOW=d;
   const baseState=dc(d.pityState),eng=engineFor(baseState),slots=+QUAL[String(baseState.zizhi)]?.slots||0;
   const actual=d.rows.filter(x=>x.rawNo>=d.firstPity.rawNo&&x.rawNo<d.nextPurple.rawNo);
   if(!actual.length||+actual[0].rawNo!==+d.firstPity.rawNo)throw Error('천장 이후 실제 원시 흐름을 찾지 못했습니다.');
   const rows=[];
   rows.push({rawNo:d.firstPity.rawNo,wash:d.firstPity.wash,id:d.firstPity.id,name:d.firstPity.name,kind:'천장',seed:+baseState.luck_seed,draws:exchangeSequence(+baseState.luck_seed,baseState,15)});

   // pityState is the real state after the pity wash. Subsequent washOnce rows are authoritative
   // for visible order/names; rawNormal below is used only to recover the exact per-row branch seed.
   let seed=+baseState.seed,rc=+(baseState.born_talent_rc||0),intl=!!baseState.international_wash;
   const later=actual.slice(1).filter(x=>+x.wash>+d.firstPity.wash);
   let p=0,guard=200000,currentWash=null,seen=new Set(),accepted=0;
   while(p<later.length&&guard-->0){
     const want=later[p];
     if(currentWash!==+want.wash){currentWash=+want.wash;seen=new Set();accepted=0;}
     let id;[id,seed]=rawNormal(seed,eng,intl?rc:0);if(intl)rc++;
     if(!eng.allowed.has(id)||seen.has(id))continue;
     const it=BYID.get(id);if(!it)continue;
     seen.add(id);accepted++;
     if(+id!==+want.id){
       throw Error(`실제 원시 흐름 재현 불일치: #${want.rawNo} ${want.name} / 재현 ${nm(id)}. 추정값으로 표시하지 않고 중단합니다.`);
     }
     const branch=dc(baseState);branch.seed=+seed;if(intl)branch.born_talent_rc=+rc;
     rows.push({rawNo:want.rawNo,wash:want.wash,id:want.id,name:want.name,kind:'원시',seed:+seed,draws:exchangeSequence(+seed,branch,15)});
     p++;
     if(accepted>=slots){currentWash=null;}
     if(p%80===0)await uiYield();
   }
   if(guard<=0)throw Error('천장 이후 실제 원시 흐름 재현 한도를 초과했습니다.');

   // If the pity page itself had trailing normal rows, do not invent branch seeds for them.
   const samePityWash=actual.slice(1).filter(x=>+x.wash===+d.firstPity.wash);
   if(samePityWash.length){
     rows.splice(1,0,...samePityWash.map(x=>({rawNo:x.rawNo,wash:x.wash,id:x.id,name:x.name,kind:'원시',seed:null,draws:[],samePityWash:true})));
   }

   let normalShift=0;
   DAO_V290_ROUTE_ROWS=rows.map(r=>{
     if(r.kind==='천장')return {...r,firstDraw:'',shift:0};
     normalShift++;return {...r,firstDraw:r.draws[0]?.name||'',shift:normalShift};
   });
   let h=`<div class="good"><b>천장 포함 이후 실제 원시맥별 교체맥 표</b><br><span class="small">원시맥 순서는 새 RNG 생성이 아니라 <b>washOnce() 실제 원시 흐름</b>을 사용합니다. 같은 세이브/조건에서는 최초 1회 계산 후 캐시되어 다시 누르면 즉시 표시됩니다. 다음 원시 자맥 <b>#${d.nextPurple.rawNo} ${d.nextPurple.name}</b>은 경계라 표에 포함하지 않습니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>원시 #</th><th>세수 회차</th><th>기준</th><th>원시맥</th>';
   for(let i=1;i<=15;i++)h+=`<th>교체 ${i}</th>`;h+='</tr></thead><tbody>';
   for(const r of rows){
     if(r.kind==='천장'){
       h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td>기본 천장</td><td class="q4"><b>${r.name}</b><div class="small">조작 없음 · 클릭 불가</div></td>`;
       for(let i=0;i<15;i++){const n=r.draws[i]?.name||'-';h+=`<td class="q4">${n}</td>`;}
     }else{
       const rr=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+r.rawNo);
       h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td>원시 · 생략 ${rr?.shift||'?'}개</td><td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td>`;
       for(let i=0;i<15;i++){
         const n=r.draws[i]?.name||'-';
         h+=r.samePityWash?`<td class="muted">-</td>`:`<td class="q4">${n}</td>`;
       }
     }
     h+='</tr>';
   }
   h+='</tbody></table></div><div id="daoPullRouteV290" style="margin-top:12px"></div>';
   const pack={window:d,routeRows:DAO_V290_ROUTE_ROWS,html:h};
   DAO_V296_EXCHANGE_CACHE={key:cacheKey,pack};
   renderDaoExchangeV296(pack);
 }catch(e){daoExchangeWindowResult.innerHTML=`<div class="warn">${e.message||e}</div>`}
}
'''
text=text[:a]+new_exchange+text[b:]

# 4) Cache invalidation must follow the existing daomai/save-condition invalidation paths,
#    but never touch the original let declaration.
text=re.sub(r'(?<!let )DAO_V288_CACHE=null;', 'DAO_V288_CACHE=null;DAO_V296_EXCHANGE_CACHE=null;', text)

# 5) Version bump only. Equipment behavior is untouched.
text=text.replace('v2.95','v2.96').replace('v2_95','v2_96')
text=re.sub(r'(?<![0-9])2\.95(?![0-9])','2.96',text)
text=re.sub(r'<script id="stable-root-url-v295">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v296">try{if(/Nangman_Integrated_Simulator_v2_96\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace').replace('v2.95','v2.96').replace('v2_95','v2_96')
inner=re.sub(r'(?<![0-9])2\.95(?![0-9])','2.96',inner)
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{base64.b64encode(inner.encode()).decode()}";'+text[m.end():]

# Stable root must be byte-identical latest app.
DST.write_text(text,encoding='utf-8')
Path('index.html').write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v2.96','file':'Nangman_Integrated_Simulator_v2_96.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.96',s);r.write_text(s,encoding='utf-8')

# Regression guards.
for x in [
    "sharedSaveText = await file.text()","JSON.parse(sharedSaveText)",
    'daoRawBeforeBtn.onclick=showDaoRawBeforeV288','dao-pull-v295','daoDeleteCandidatesV295',
    'DAO_V296_EXCHANGE_CACHE','washOnce() 실제 원시 흐름','border-top:3px solid currentColor'
]:
    if x not in text: raise SystemExit('regression '+x)
if DST.read_text(encoding='utf-8')!=Path('index.html').read_text(encoding='utf-8'):
    raise SystemExit('index/versioned mismatch')
if '<title>낭만강호 통합 시뮬레이터 v2.96</title>' not in text[:10000]: raise SystemExit('title mismatch')
if '현재 사이트 버전: v2.96' not in r.read_text(encoding='utf-8'): raise SystemExit('README mismatch')

for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v296_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:1500])
print('built v2.96 final')
