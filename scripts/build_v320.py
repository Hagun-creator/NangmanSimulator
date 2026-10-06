from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_19.html')
DST=Path('Nangman_Integrated_Simulator_v3_20.html')
if not SRC.exists(): raise SystemExit('v3.19 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.19','v3.20').replace('v3_19','v3_20')
text=re.sub(r'(?<![0-9])3\.19(?![0-9])','3.20',text)
text=re.sub(r'<script id="stable-root-url-v319">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v320">try{if(/Nangman_Integrated_Simulator_v3_20\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Patch only daomai route progress/output. Keep v3.19 route algorithm intact.
a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]

# Add a runtime helper that reuses the existing simulator "현재 세수단" input without duplicating UI.
anchor=""" const targetSeed=+(row.luckStart??row.seedAfter??0);
 if(!targetSeed){box.innerHTML='<div class=\"warn\">선택 행의 목표 seed를 찾지 못했습니다.</div>';return}
"""
insert=""" const targetSeed=+(row.luckStart??row.seedAfter??0);
 if(!targetSeed){box.innerHTML='<div class=\"warn\">선택 행의 목표 seed를 찾지 못했습니다.</div>';return}
 function daoCurrentPillsValue(){
   const inputs=[...document.querySelectorAll('input[type=\"number\"],input:not([type])')];
   for(const el of inputs){
     const id=String(el.id||'').toLowerCase(),nm0=String(el.name||'').toLowerCase(),ph=String(el.placeholder||'');
     let label='';
     try{
       const lab=el.id?document.querySelector(`label[for=\"${CSS.escape(el.id)}\"]`):null;
       label=(lab?.textContent||'')+' '+(el.closest('label')?.textContent||'')+' '+(el.parentElement?.textContent||'');
     }catch(e){label=(el.parentElement?.textContent||'')}
     const sig=(label+' '+ph+' '+id+' '+nm0).replace(/\\s+/g,' ');
     if(/현재\\s*세수단|보유\\s*세수단/.test(sig)){
       const v=Number(el.value);if(Number.isFinite(v)&&v>=0)return v;
     }
   }
   return 0;
 }
 const daoCurrentPills=daoCurrentPillsValue();
"""
if anchor not in route: raise SystemExit('target seed anchor missing')
route=route.replace(anchor,insert,1)

# Add progress counters for the direct near-pity verification.
needle=""" const direct=[];
 const nearLimit=Math.min(4,pages.length);
 for(let dist=0;dist<nearLimit;dist++){
"""
repl=""" const direct=[];
 let directChecked=0;
 const nearLimit=Math.min(4,pages.length);
 for(let dist=0;dist<nearLimit;dist++){
"""
if needle not in route: raise SystemExit('direct block anchor missing')
route=route.replace(needle,repl,1)

# Replace the innermost direct hold loop to show current search count without changing candidates.
old="""       for(let hold=1;hold<=3;hold++){
         const cand=exactNearCandidate(pg,dist,lockIds,hold,nearLimit,'천장 직전 직접검증');
         if(cand)direct.push(cand);
       }
"""
new="""       for(let hold=1;hold<=3;hold++){
         directChecked++;
         if(directChecked===1 || directChecked%6===0){
           box.innerHTML=`<div class=\"warn\"><b>최소비용 탐색 중</b> · 천장 직전 직접검증<br>`+
             `현재 검색 <b>#${directChecked}</b> · 페이지 ${dist+1}/${nearLimit} · 잠금 ${lockCount}개 · 유지 ${hold}회 · 누적 잠금 ${checked.toLocaleString()}회 · probe ${probes.toLocaleString()}회</div>`;
           await uiYield();
         }
         const cand=exactNearCandidate(pg,dist,lockIds,hold,nearLimit,'천장 직전 직접검증');
         if(cand)direct.push(cand);
       }
"""
if old not in route: raise SystemExit('direct hold loop missing')
route=route.replace(old,new,1)

# Generic search: indexed masks + throttled live progress. Algorithm/order is unchanged.
old2="""       for(const m of masks){
         const lockIds=[];for(let i=0;i<n;i++)if(m&(1<<i))lockIds.push(+pg.talents[i].id);
         const cand=exactNearCandidate(pg,dist,lockIds,sh.hold,win,'비용우선 탐색');
         if(!cand)continue;
         if(!best||cand.cost<best.cost||(cand.cost===best.cost&&cand.dist<best.dist))best=cand;
       }
"""
new2="""       for(let mi=0;mi<masks.length;mi++){
         const m=masks[mi];
         const lockIds=[];for(let i=0;i<n;i++)if(m&(1<<i))lockIds.push(+pg.talents[i].id);
         if(checked===0 || checked%12===0){
           box.innerHTML=`<div class=\"warn\"><b>최소비용 탐색 중</b> · 현재 비용 <b>${sh.cost}단</b><br>`+
             `탐색 창 ${win}회차 · 천장에서 ${dist}회차 앞 (${dist+1}/${limit}) · 잠금 조합 ${mi+1}/${masks.length}<br>`+
             `누적 잠금 검사 <b>${checked.toLocaleString()}회</b> · 천장 probe <b>${probes.toLocaleString()}회</b>${best?` · 현재 최저 ${best.cost}단`:''}</div>`;
           await uiYield();
         }
         const cand=exactNearCandidate(pg,dist,lockIds,sh.hold,win,'비용우선 탐색');
         if(!cand)continue;
         if(!best||cand.cost<best.cost||(cand.cost===best.cost&&cand.dist<best.dist))best=cand;
       }
"""
if old2 not in route: raise SystemExit('generic mask loop missing')
route=route.replace(old2,new2,1)

# Add current-pill / remaining display to the winning result only.
needle3=""" let h=`<div class=\"good\"><b>목표 seed 도달 최소비용 경로</b> · 목표 seed <b>${targetSeed}</b> · 추가 잠금 세수 소모 <b>${best.cost.toLocaleString()}단</b></div>`+
"""
repl3=""" const remainAfterExtra=daoCurrentPills>0?Math.max(0,daoCurrentPills-best.cost):null;
 const pillBalanceHtml=daoCurrentPills>0
   ? `<div class=\"good\" style=\"margin-top:6px\"><b>현재 세수단 ${daoCurrentPills.toLocaleString()}개</b> · 잡맥 추가 소모 ${best.cost.toLocaleString()}개 · <b>잡맥 적용 후 남음 ${remainAfterExtra.toLocaleString()}개</b></div>`
   : `<div class=\"small\" style=\"margin-top:6px\">모의 세수작의 <b>현재 세수단</b>에 값을 입력하면 이 경로 적용 후 남은 세수단을 함께 표시합니다.</div>`;
 let h=`<div class=\"good\"><b>목표 seed 도달 최소비용 경로</b> · 목표 seed <b>${targetSeed}</b> · 추가 잠금 세수 소모 <b>${best.cost.toLocaleString()}단</b></div>`+pillBalanceHtml+
"""
if needle3 not in route: raise SystemExit('winning output anchor missing')
route=route.replace(needle3,repl3,1)

for x in ['daoCurrentPillsValue','현재 검색 <b>#${directChecked}</b>','잠금 조합 ${mi+1}/${masks.length}','누적 잠금 검사','잡맥 적용 후 남음']:
 if x not in route: raise SystemExit('v3.20 guard missing: '+x)
text=text[:a]+route+text[b:]

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.20','file':'Nangman_Integrated_Simulator_v3_20.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.20',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.20</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v320_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.20: shared current pills display + live route search progress')
