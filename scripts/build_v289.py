from pathlib import Path
import re, base64, subprocess

SRC=Path('Nangman_Integrated_Simulator_v2_88.html')
DST=Path('Nangman_Integrated_Simulator_v2_89.html')
VER='v2.89'
if not SRC.exists(): raise SystemExit('v2.88 source missing')
text=SRC.read_text(encoding='utf-8')

# Narrow patch: replace ONLY daomai function-2 renderer/calculation.
start=text.find('async function showDaoExchangeWindowV288(){')
end=text.find('\n}\n\nasync function analyzeFirstPityDaomai()',start)
if start<0 or end<0: raise SystemExit('v2.88 daomai function-2 boundary missing')
end += 3
new_func=r'''async function showDaoExchangeWindowV288(){
 daoExchangeWindowResult.innerHTML='<div class="warn">천장 이후 원시맥별 교체맥 15개 계산 중...</div>';
 daoRawBeforeResult.innerHTML='';
 try{
   const d=await daoWindowCachedV288();
   const baseState=dc(d.pityState);
   const eng=engineFor(baseState);
   const slots=+QUAL[String(baseState.zizhi)]?.slots||0;
   const rows=[];

   // 첫 행: 천장 자맥 자체를 기준 원시맥으로 포함.
   rows.push({
     rawNo:d.firstPity.rawNo,
     wash:d.firstPity.wash,
     id:d.firstPity.id,
     name:d.firstPity.name,
     kind:'천장',
     seed:+baseState.luck_seed,
     draws:exchangeSequence(+baseState.luck_seed,baseState,15)
   });

   // 이후 normal 원시 흐름을 직접 재생한다.
   // 무한교체 N표와 동일하게 각 기준 원시맥 직후 seed에서 교체맥 15개를 독립 계산한다.
   let seed=+baseState.seed;
   let rc=+(baseState.born_talent_rc||0);
   const intl=!!baseState.international_wash;
   let rawNo=+d.firstPity.rawNo;
   let washNo=+baseState.total_wash;
   let guard=200000;
   let stopPurple=null;

   while(guard-->0 && !stopPurple){
     washNo++;
     const seen=new Set();
     let accepted=0;
     while(accepted<slots && guard-->0){
       let id;
       [id,seed]=rawNormal(seed,eng,intl?rc:0);
       if(intl)rc++;
       if(!eng.allowed.has(id)||seen.has(id))continue;
       const it=BYID.get(id);if(!it)continue;
       seen.add(id);accepted++;rawNo++;
       if(+it.weight===4){
         stopPurple={rawNo,wash:washNo,id,name:nm(id)};
         break;
       }
       const branch=dc(baseState);
       branch.seed=+seed;
       if(intl)branch.born_talent_rc=+rc;
       rows.push({
         rawNo,wash:washNo,id,name:nm(id),kind:'원시',seed:+seed,
         draws:exchangeSequence(+seed,branch,15)
       });
     }
     if(washNo%80===0)await uiYield();
   }
   if(guard<=0)throw Error('천장 이후 원시 흐름 스캔 한도를 초과했습니다.');
   if(!stopPurple)throw Error('다음 원시 자맥을 찾지 못했습니다.');

   let h=`<div class="good"><b>천장 포함 이후 원시맥별 교체맥 표</b><br>`+
         `<span class="small">첫 행은 천장 자맥 자체입니다. 이후 각 원시맥 직후 seed를 기준으로 교체맥 15개를 독립 계산합니다. 다음 원시 자맥 <b>#${stopPurple.rawNo} ${stopPurple.name}</b>은 경계라 표에 포함하지 않습니다.</span></div>`;
   h+='<div class="scroll"><table><thead><tr><th>원시 #</th><th>세수 회차</th><th>기준</th><th>원시맥</th>';
   for(let i=1;i<=15;i++)h+=`<th>교체 ${i}</th>`;
   h+='</tr></thead><tbody>';
   for(const r of rows){
     h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td>${r.kind}</td><td class="${r.kind==='천장'?'q4':''}"><b>${r.name}</b></td>`;
     for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||'-'}</td>`;
     h+='</tr>';
   }
   h+='</tbody></table></div>';
   daoExchangeWindowResult.innerHTML=h;
 }catch(e){daoExchangeWindowResult.innerHTML=`<div class="warn">${e.message||e}</div>`}
}
'''
text=text[:start]+new_func+text[end:]

# Version bump only; preserve all unrelated logic including save loader/equipment.
text=text.replace('v2.88','v2.89').replace('v2_88','v2_89')
text=re.sub(r'(?<![0-9])2\.88(?![0-9])','2.89',text)

# Embedded equipment: version labels only, no behavioral changes.
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace')
inner=inner.replace('v2.88','v2.89').replace('v2_88','v2_89')
inner=re.sub(r'(?<![0-9])2\.88(?![0-9])','2.89',inner)
enc=base64.b64encode(inner.encode()).decode()
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{enc}";'+text[m.end():]

DST.write_text(text,encoding='utf-8')
Path('index.html').write_text(text,encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.89',s);r.write_text(s,encoding='utf-8')

# Regression guards: unrelated working features must remain.
for x in ["const sharedSaveInput = document.getElementById('sharedSaveFile')","sharedSaveInput?.addEventListener('change'","sharedSaveText = await file.text()","JSON.parse(sharedSaveText)"]:
    if x not in text: raise SystemExit('save loader regression: '+x)
if 'daoRawBeforeBtn.onclick=showDaoRawBeforeV288' not in text: raise SystemExit('daomai function 1 changed/lost')
if 'daoExchangeWindowBtn.onclick=showDaoExchangeWindowV288' not in text: raise SystemExit('daomai function 2 binding lost')
for x in ['원시맥별 교체맥 표','for(let i=1;i<=15;i++)','exchangeSequence(+seed,branch,15)']:
    if x not in text: raise SystemExit('v2.89 row table regression: '+x)
if 'http-equiv="Cache-Control"' not in text[:8000]: raise SystemExit('cache guard lost')
# Syntax check every executable script block.
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v289_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(f'JS syntax error {i}: {cp.stderr[:1500]}')
if '<title>낭만강호 통합 시뮬레이터 v2.89</title>' not in text[:8000]: raise SystemExit('title mismatch')
print('built v2.89')
