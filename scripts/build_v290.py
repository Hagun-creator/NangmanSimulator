from pathlib import Path
import re, base64, subprocess

SRC=Path('Nangman_Integrated_Simulator_v2_89.html')
DST=Path('Nangman_Integrated_Simulator_v2_90.html')
if not SRC.exists(): raise SystemExit('v2.89 source missing')
text=SRC.read_text(encoding='utf-8')

start=text.find('async function showDaoExchangeWindowV288(){')
end=text.find('\n}\n\nasync function analyzeFirstPityDaomai()',start)
if start<0 or end<0: raise SystemExit('function2 boundary missing')
end+=3
new_func=r'''let DAO_V290_ROUTE_ROWS=[];
let DAO_V290_WINDOW=null;
function daoDeleteCandidatesV290(d){
 const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo && x.weight<4);
 const by=new Map();
 for(const x of pre){if(!by.has(x.id))by.set(x.id,[]);by.get(x.id).push(x)}
 const slots=+QUAL[String(d.pityState.zizhi)]?.slots||0;
 const oneLockCost=(COST?.[slots]?.[1]??0);
 const out=[];
 for(const arr of by.values()){
   if(arr.length<2)continue;
   for(let j=1;j<arr.length;j++){
     // Lock the nearest previous same trait; the later duplicate is swallowed when it collides on screen.
     const del=arr[j], prev=arr[j-1];
     const washes=Math.max(1,+del.wash-+prev.wash);
     out.push({id:del.id,name:del.name,lockRaw:prev.rawNo,lockWash:prev.wash,deleteRaw:del.rawNo,deleteWash:del.wash,washes,pills:washes*oneLockCost});
   }
 }
 return out.sort((a,b)=>a.pills-b.pills || b.deleteRaw-a.deleteRaw);
}
function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;
 if(!d){box.innerHTML='<div class="warn">먼저 천장 이후 교체맥 표를 계산하세요.</div>';return}
 const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo && x.weight<4);
 const currentPrev=pre.length?pre[pre.length-1]:null;
 if(!currentPrev){box.innerHTML='<div class="warn">현재 천장 직전 일반 자질을 찾지 못했습니다.</div>';return}

 // 잡맥법: deletion pulls later raw traits forward. Therefore only a later raw basis can replace current pity predecessor.
 const targets=DAO_V290_ROUTE_ROWS.filter(x=>x.firstDraw===targetName && x.rawNo>currentPrev.rawNo)
   .sort((a,b)=>(a.rawNo-currentPrev.rawNo)-(b.rawNo-currentPrev.rawNo));
 if(!targets.length){
   box.innerHTML=`<div class="warn"><b>${targetName}</b> · 선택 위치 교체 ${sourceCol}<br>현재 천장 직전 원시 #${currentPrev.rawNo} ${currentPrev.name}보다 뒤쪽에서 이 맥이 <b>교체 1</b>이 되는 기준 원시맥을 찾지 못했습니다. 현재 표시 구간의 잡맥 생략만으로는 이 맥을 천장으로 당기는 경로를 확정할 수 없습니다.</div>`;
   return;
 }
 const c=targets[0];
 const need=Math.max(0,c.rawNo-currentPrev.rawNo);
 const cand=daoDeleteCandidatesV290(d);
 if(cand.length<need){
   box.innerHTML=`<div class="warn"><b>${targetName}</b>을 천장으로 당기려면 원시 순서를 <b>${need}칸</b> 줄여야 합니다.<br>현재 천장 전 표에서 확인되는 생략 가능한 중복쌍은 ${cand.length}개라 자동 경로를 완성하지 못했습니다.</div>`;
   return;
 }
 // Greedy minimum-pill route; ties prefer deletions closest to pity.
 const chosen=cand.slice(0,need);
 const total=chosen.reduce((s,x)=>s+x.pills,0);
 let h=`<div class="good"><b>${targetName}</b>을 천장맥으로 당기는 최소 세수단 잡맥법</div>`;
 h+=`<div class="small" style="line-height:1.75;margin-top:6px">선택: 원시 #${sourceRaw} ${sourceName}의 <b>교체 ${sourceCol}</b><br>`;
 h+=`현재 천장 직전: <b>원시 #${currentPrev.rawNo} ${currentPrev.name}</b><br>`;
 h+=`목표 천장 직전: <b>원시 #${c.rawNo} ${c.name}</b> · 이 원시맥 직후 교체 1 = <b>${targetName}</b><br>`;
 h+=`필요 생략: <b>${need}개</b> · 예상 추가 소모 <b>${total}단</b><br></div>`;
 h+='<div class="scroll"><table><thead><tr><th>순서</th><th>잠글 원시맥</th><th>삭제되는 중복맥</th><th>유지 세수</th><th>예상 소모</th></tr></thead><tbody>';
 chosen.forEach((x,i)=>{h+=`<tr><td>${i+1}</td><td>#${x.lockRaw} ${x.name}</td><td>#${x.deleteRaw} ${x.name}</td><td>${x.washes}회</td><td>${x.pills}단</td></tr>`});
 h+='</tbody></table></div>';
 h+=`<div class="small" style="line-height:1.7;margin-top:7px"><b>실행:</b> 위 순서대로 앞의 동일 자질을 잠그고, 뒤의 같은 자질이 같은 화면에 들어와 삭제될 때까지 돌린 뒤 잠금을 해제합니다. 필요한 ${need}개가 생략되면 원래 #${c.rawNo} ${c.name}이 천장 직전 위치로 당겨지고, 다음 천장 자맥이 계산상 <b>${targetName}</b>으로 바뀝니다.<br><span class="warn">잡맥법 규칙: 동일 자질은 한 화면에 둘 수 없어 뒤 중복이 삭제되고, 삭제된 개수만큼 뒤 원시 순서가 앞으로 당겨집니다.</span></div>`;
 box.innerHTML=h;box.scrollIntoView({block:'nearest'});
}
async function showDaoExchangeWindowV288(){
 daoExchangeWindowResult.innerHTML='<div class="warn">천장 이후 원시맥별 교체맥 15개 계산 중...</div>';
 daoRawBeforeResult.innerHTML='';
 try{
   const d=await daoWindowCachedV288();DAO_V290_WINDOW=d;
   const baseState=dc(d.pityState),eng=engineFor(baseState),slots=+QUAL[String(baseState.zizhi)]?.slots||0;
   const rows=[];
   rows.push({rawNo:d.firstPity.rawNo,wash:d.firstPity.wash,id:d.firstPity.id,name:d.firstPity.name,kind:'천장',seed:+baseState.luck_seed,draws:exchangeSequence(+baseState.luck_seed,baseState,15)});
   let seed=+baseState.seed,rc=+(baseState.born_talent_rc||0),intl=!!baseState.international_wash,rawNo=+d.firstPity.rawNo,washNo=+baseState.total_wash,guard=200000,stopPurple=null;
   while(guard-->0&&!stopPurple){
     washNo++;const seen=new Set();let accepted=0;
     while(accepted<slots&&guard-->0){
       let id;[id,seed]=rawNormal(seed,eng,intl?rc:0);if(intl)rc++;
       if(!eng.allowed.has(id)||seen.has(id))continue;const it=BYID.get(id);if(!it)continue;
       seen.add(id);accepted++;rawNo++;
       if(+it.weight===4){stopPurple={rawNo,wash:washNo,id,name:nm(id)};break}
       const branch=dc(baseState);branch.seed=+seed;if(intl)branch.born_talent_rc=+rc;
       rows.push({rawNo,wash:washNo,id,name:nm(id),kind:'원시',seed:+seed,draws:exchangeSequence(+seed,branch,15)});
     }
     if(washNo%80===0)await uiYield();
   }
   if(guard<=0)throw Error('천장 이후 원시 흐름 스캔 한도를 초과했습니다.');
   if(!stopPurple)throw Error('다음 원시 자맥을 찾지 못했습니다.');
   DAO_V290_ROUTE_ROWS=rows.map(r=>({...r,firstDraw:r.draws[0]?.name||''}));
   let h=`<div class="good"><b>천장 포함 이후 원시맥별 교체맥 표</b><br><span class="small">교체맥 이름을 누르면 잡맥법으로 그 맥을 천장맥으로 당기는 최소 세수단 경로를 계산합니다. 다음 원시 자맥 <b>#${stopPurple.rawNo} ${stopPurple.name}</b>은 경계라 표에 포함하지 않습니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>원시 #</th><th>세수 회차</th><th>기준</th><th>원시맥</th>';
   for(let i=1;i<=15;i++)h+=`<th>교체 ${i}</th>`;h+='</tr></thead><tbody>';
   for(const r of rows){
     h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td>${r.kind}</td><td class="${r.kind==='천장'?'q4':''}"><b>${r.name}</b></td>`;
     for(let i=0;i<15;i++){const n=r.draws[i]?.name||'-';h+=`<td class="q4"><button type="button" class="linkBtn" onclick="showDaoPullRouteV290(${JSON.stringify(n)},${r.rawNo},${JSON.stringify(r.name)},${i+1})">${n}</button></td>`}
     h+='</tr>';
   }
   h+='</tbody></table></div><div id="daoPullRouteV290" style="margin-top:12px"></div>';
   daoExchangeWindowResult.innerHTML=h;
 }catch(e){daoExchangeWindowResult.innerHTML=`<div class="warn">${e.message||e}</div>`}
}
'''
text=text[:start]+new_func+text[end:]
text=text.replace('v2.89','v2.90').replace('v2_89','v2_90')
text=re.sub(r'(?<![0-9])2\.89(?![0-9])','2.90',text)
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;';m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace').replace('v2.89','v2.90').replace('v2_89','v2_90')
inner=re.sub(r'(?<![0-9])2\.89(?![0-9])','2.90',inner);enc=base64.b64encode(inner.encode()).decode();text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{enc}";'+text[m.end():]
DST.write_text(text,encoding='utf-8');Path('index.html').write_text(text,encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.90',s);r.write_text(s,encoding='utf-8')
# guards
for x in ["const sharedSaveInput = document.getElementById('sharedSaveFile')","sharedSaveInput?.addEventListener('change'","sharedSaveText = await file.text()","JSON.parse(sharedSaveText)"]:
    if x not in text: raise SystemExit('save loader regression: '+x)
if 'daoRawBeforeBtn.onclick=showDaoRawBeforeV288' not in text: raise SystemExit('function1 changed')
for x in ['showDaoPullRouteV290','daoDeleteCandidatesV290','최소 세수단 잡맥법','교체 15']:
    if x not in text: raise SystemExit('v2.90 missing '+x)
if 'http-equiv="Cache-Control"' not in text[:8000]: raise SystemExit('cache guard lost')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v290_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(f'JS syntax error {i}: {cp.stderr[:1500]}')
if '<title>낭만강호 통합 시뮬레이터 v2.90</title>' not in text[:8000]: raise SystemExit('title mismatch')
print('built v2.90')
