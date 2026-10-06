from pathlib import Path
import re, base64, subprocess

SRC=Path('Nangman_Integrated_Simulator_v2_87.html')
DST=Path('Nangman_Integrated_Simulator_v2_88.html')
VER='v2.88'
if not SRC.exists(): raise SystemExit('v2.87 source missing')
text=SRC.read_text(encoding='utf-8')
orig=text

# 1) Replace ONLY the visible pity/daomai pane. Keep compatibility nodes hidden so unrelated old reset code cannot break.
a=text.find('<div id="pityPane" class="pane">')
b=text.find('<div id="rulesPane" class="pane">',a)
if a<0 or b<0: raise SystemExit('pity pane boundaries missing')
new_pane='''<div id="pityPane" class="pane">
<div class="row" style="margin-bottom:8px">
<button id="daoRawBeforeBtn">1. 천장 전 모든 원시맥 보기</button>
<button id="daoExchangeWindowBtn">2. 천장 포함 이후 교체맥 보기</button>
</div>
<div class="small" style="margin-bottom:10px">첫 원시 자맥이 천장인 경우만 계산합니다. 1번은 첫 천장 직전까지의 모든 원시맥, 2번은 천장맥 자체를 포함해 다음 원시 자맥 직전까지의 교체맥만 표시합니다.</div>
<div id="daoRawBeforeResult"></div>
<div id="daoExchangeWindowResult" style="margin-top:12px"></div>
<div id="pityResult" hidden></div><div id="daoFirstResult" hidden></div><div id="rawFullSummary" hidden></div><table hidden><tbody id="rawFullBody"></tbody></table>
</div>

'''
text=text[:a]+new_pane+text[b:]

# 2) Inject two focused v2.88 functions before old daomai analyzer; old analyzers remain unreachable to minimize regression risk.
marker='async function analyzeFirstPityDaomai()'
pos=text.find(marker)
if pos<0: raise SystemExit('daomai function marker missing')
new_js=r'''let DAO_V288_CACHE=null;
async function daoFirstPityWindowV288(){
 if(!SAVE)throw Error('세이브를 먼저 불러오세요.');
 const r=roleObj();if(!r)throw Error('캐릭터를 선택하세요.');
 let st=stateFromSave(SAVE,r,+vipSel.value,rawCalcZizhi());
 st=unlockAll(st);
 const rows=[];let firstPity=null,nextPurple=null,pityState=null,guard=10000;
 while(guard-->0 && !nextPurple){
   const beforeBars=+st.total_talent_bars;
   const tr=washOnce(st);st=tr.state;
   const unlocked=tr.result.talents.filter(t=>!t.locked);
   const page=[];
   for(let i=0;i<unlocked.length;i++){
     const id=+unlocked[i].id,it=BYID.get(id);if(!it)continue;
     const rec={rawNo:beforeBars+i+1,wash:+st.total_wash,id,name:nm(id),weight:+it.weight,type:+it.type};
     rows.push(rec);page.push(rec);
   }
   const purple=page.find(x=>x.weight===4)||null;
   if(!firstPity){
     if(tr.result.got_gold && !tr.result.was_pity){
       throw Error(`첫 원시 자맥이 천장이 아닙니다. 원시 #${purple?.rawNo||'?'} ${purple?.name||''}`.trim());
     }
     if(tr.result.was_pity){
       if(!purple)throw Error('천장 자맥 행을 찾지 못했습니다.');
       firstPity=purple;pityState=dc(st);
     }
   }else if(tr.result.got_gold && purple){
     nextPurple=purple;
   }
   if(st.total_wash%100===0)await uiYield();
 }
 if(!firstPity)throw Error('첫 천장을 찾지 못했습니다.');
 if(!nextPurple)throw Error('첫 천장 이후 다음 원시 자맥을 찾지 못했습니다.');
 return {rows,firstPity,nextPurple,pityState};
}
async function daoWindowCachedV288(){
 const key=[roleSel?.value||'',vipSel?.value||'',rawCalcZizhi(),JSON.stringify(SPECIAL_STATE||{})].join('|');
 if(DAO_V288_CACHE&&DAO_V288_CACHE.key===key)return DAO_V288_CACHE.data;
 const data=await daoFirstPityWindowV288();DAO_V288_CACHE={key,data};return data;
}
async function showDaoRawBeforeV288(){
 daoRawBeforeResult.innerHTML='<div class="warn">첫 천장 전 원시맥 계산 중...</div>';
 daoExchangeWindowResult.innerHTML='';
 try{
   const d=await daoWindowCachedV288();
   const rows=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo);
   let h=`<div class="good"><b>첫 천장</b>: 원시 #${d.firstPity.rawNo} ${d.firstPity.name}<br><span class="small">아래 표는 천장 행을 제외한 직전까지의 모든 원시맥입니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>원시 #</th><th>세수 회차</th><th>맥 이름</th><th>등급</th><th>계열(type)</th></tr></thead><tbody>';
   for(const x of rows)h+=`<tr><td class="num">${x.rawNo}</td><td class="num">${x.wash}</td><td class="q${Math.max(1,Math.min(4,x.weight))}">${x.name}</td><td>${qualityLabel(x.weight)}</td><td>${x.type}</td></tr>`;
   h+='</tbody></table></div>';
   daoRawBeforeResult.innerHTML=h;
 }catch(e){daoRawBeforeResult.innerHTML=`<div class="warn">${e.message||e}</div>`}
}
async function showDaoExchangeWindowV288(){
 daoExchangeWindowResult.innerHTML='<div class="warn">천장 포함 교체맥 구간 계산 중...</div>';
 daoRawBeforeResult.innerHTML='';
 try{
   const d=await daoWindowCachedV288();
   const gap=Math.max(1,d.nextPurple.rawNo-d.firstPity.rawNo);
   const need=Math.max(0,gap-1);
   const seq=need?exchangeSequence(+d.pityState.luck_seed,d.pityState,need):[];
   let h=`<div class="good"><b>교체맥 구간</b>: 원시 #${d.firstPity.rawNo} 천장 ${d.firstPity.name} 포함 → 다음 원시 자맥 #${d.nextPurple.rawNo} ${d.nextPurple.name} 직전까지<br><span class="small">다음 원시 자맥 자체는 경계이므로 표에 포함하지 않습니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>구간 순번</th><th>종류</th><th>맥 이름</th></tr></thead><tbody>';
   h+=`<tr><td class="num">1</td><td>천장</td><td class="q4"><b>${d.firstPity.name}</b></td></tr>`;
   for(let i=0;i<seq.length;i++)h+=`<tr><td class="num">${i+2}</td><td>교체 ${i+1}</td><td class="q4">${seq[i].name}</td></tr>`;
   h+='</tbody></table></div>';
   daoExchangeWindowResult.innerHTML=h;
 }catch(e){daoExchangeWindowResult.innerHTML=`<div class="warn">${e.message||e}</div>`}
}

'''
text=text[:pos]+new_js+text[pos:]

# 3) Remove bindings to removed visible controls, bind only the two requested functions.
text=text.replace('rawFullBtn.onclick=analyzeRawUntilSecondPurple;','')
old='nCalc.onclick=calcN;pityAnalyzeBtn.onclick=analyzePityShift;daoFirstBtn.onclick=analyzeFirstPityDaomai;'
new='nCalc.onclick=calcN;daoRawBeforeBtn.onclick=showDaoRawBeforeV288;daoExchangeWindowBtn.onclick=showDaoExchangeWindowV288;'
if old not in text: raise SystemExit('old pity binding missing')
text=text.replace(old,new,1)

# Reset only the daomai cache when conditions that already invalidate RAW change.
text=text.replace('ENGINE_CACHE.clear(); RAW=[]; CANDS=[];', 'ENGINE_CACHE.clear(); DAO_V288_CACHE=null; RAW=[]; CANDS=[];')
text=text.replace('simCancelRunning();RAW=[];CANDS=[];', 'simCancelRunning();DAO_V288_CACHE=null;RAW=[];CANDS=[];')

# 4) Version bump outer, without broad behavioral edits.
text=text.replace('v2.87','v2.88').replace('v2_87','v2_88')
text=re.sub(r'(?<![0-9])2\.87(?![0-9])','2.88',text)

# 5) Bump embedded equipment display version only, preserving its logic exactly.
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace')
inner=inner.replace('v2.87','v2.88').replace('v2_87','v2_88')
inner=re.sub(r'(?<![0-9])2\.87(?![0-9])','2.88',inner)
enc=base64.b64encode(inner.encode()).decode()
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{enc}";'+text[m.end():]

DST.write_text(text,encoding='utf-8');Path('index.html').write_text(text,encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.88',s);r.write_text(s,encoding='utf-8')

# Regression guards: save loading MUST remain present and untouched in behavior.
for x in ["const sharedSaveInput = document.getElementById('sharedSaveFile')","sharedSaveInput?.addEventListener('change'","sharedSaveText = await file.text()","JSON.parse(sharedSaveText)"]:
    if x not in text: raise SystemExit('save loader regression: '+x)
# Only two visible daomai controls.
for x in ['daoRawBeforeBtn','daoExchangeWindowBtn','천장 전 모든 원시맥 보기','천장 포함 이후 교체맥 보기']:
    if x not in text: raise SystemExit('v2.88 daomai UI missing '+x)
# Old controls must not be visible in pity pane.
pane=text[text.find('<div id="pityPane"'):text.find('<div id="rulesPane"')]
for oldtxt in ['첫 천장·카맥 분석','첫 자맥 천장 도맥법 보기','1·2번째 자맥까지 전체 원시맥 계산','#600']:
    if oldtxt in pane: raise SystemExit('old daomai UI remains '+oldtxt)
# Cache guard from v2.87 must remain.
if 'http-equiv="Cache-Control"' not in text[:8000]: raise SystemExit('cache guard lost')
# Syntax-check executable scripts.
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v288_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(f'JS syntax error {i}: {cp.stderr[:1500]}')
if '<title>낭만강호 통합 시뮬레이터 v2.88</title>' not in text[:8000]: raise SystemExit('title mismatch')
print('built v2.88')
