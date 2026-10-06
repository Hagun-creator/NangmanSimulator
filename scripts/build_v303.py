from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_02.html')
DST=Path('Nangman_Integrated_Simulator_v3_03.html')
if not SRC.exists(): raise SystemExit('v3.02 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.02','v3.03').replace('v3_02','v3_03')
text=re.sub(r'(?<![0-9])3\.02(?![0-9])','3.03',text)
text=re.sub(r'<script id="stable-root-url-v302">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v303">try{if(/Nangman_Integrated_Simulator_v3_03\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Narrow only the second daomai table to raw #700+.
text=text.replace('2. 원시 #600~천장 직전 교체맥 보기','2. 원시 #700~천장 직전 교체맥 보기')
text=text.replace('원시 #600부터 천장 직전 일반맥까지','원시 #700부터 천장 직전 일반맥까지')
text=text.replace('원시 #600~천장 직전 교체맥 표','원시 #700~천장 직전 교체맥 표')
text=text.replace('첫 천장 이전 원시 #600~#${currentPrev.rawNo}','첫 천장 이전 원시 #700~#${currentPrev.rawNo}')
text=text.replace('원시 #600부터 첫 천장 직전까지 원시맥별 천장/교체맥 15개 계산 중...','원시 #700부터 첫 천장 직전까지 원시맥별 천장/교체맥 15개 계산 중...')
text=text.replace('원시 #600 이후 천장 직전 후보 일반맥이 없습니다.','원시 #700 이후 천장 직전 후보 일반맥이 없습니다.')
text=text.replace('원시 #600 이후 천장 직전 흐름 계산 한도를 초과했습니다.','원시 #700 이후 천장 직전 흐름 계산 한도를 초과했습니다.')
text=text.replace("const cacheKey=daoV296Key()+'|pre600-v301';","const cacheKey=daoV296Key()+'|pre700-v303';")

# Change only the second-button scan threshold, not analyzeFirstPityDaomai legacy code.
s=text.find('async function showDaoExchangeWindowV288(){')
pos=text.find('const minRaw=600;',s)
if pos<0: raise SystemExit('exchange minRaw not found')
text=text[:pos]+'const minRaw=700;'+text[pos+len('const minRaw=600;'):]

# Process/display rows closest to pity first while still calculating all 15 exchanges for every visible row.
text=text.replace('const usable=candidates.filter(x=>+x.rawNo<=+currentPrev.rawNo);','const usable=candidates.filter(x=>+x.rawNo<=+currentPrev.rawNo).sort((a,b)=>b.rawNo-a.rawNo);',1)
text=text.replace("daoExchangeWindowResult.innerHTML='<div class=\"warn\">원시 #700부터 첫 천장 직전까지 원시맥별 천장/교체맥 15개 계산 중...</div>';",
                  "daoExchangeWindowResult.innerHTML='<div class=\"warn\">원시 #700부터 첫 천장 직전까지 원시맥별 천장/교체맥 15개 계산 중... 천장에 가까운 원시맥부터 처리합니다.</div>';",1)

# Replace exhaustive branch search with click-only greedy nearest-first sequential regrouping.
start=text.find('function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){')
end=text.find('\nasync function showDaoExchangeWindowV288(){',start)
if start<0 or end<0: raise SystemExit('route function not found')
new_func=r'''function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){
 const box=document.getElementById('daoPullRouteV290');if(!box)return;
 const d=DAO_V290_WINDOW;if(!d){box.innerHTML='<div class="warn">먼저 원시 #700~천장 직전 교체맥 표를 계산하세요.</div>';return}
 const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!row){box.innerHTML='<div class="warn">선택한 원시맥 행을 찾지 못했습니다.</div>';return}
 const target=row.firstDraw||targetName||'';
 const pre=d.rows.filter(x=>x.rawNo<d.firstPity.rawNo&&x.weight<4).map(x=>({...x}));
 const currentPrev=pre[pre.length-1]||null;
 if(!currentPrev){box.innerHTML='<div class="warn">현재 천장 직전 일반 자질을 찾지 못했습니다.</div>';return}
 const targetRaw=+sourceRaw;
 const needDel=pre.filter(x=>+x.rawNo>targetRaw).length;
 let h=`<div class="good"><b>${sourceName}</b> 기준 → 천장 후보 <b>${target}</b></div>`+
 `<div class="small" style="line-height:1.7;margin:6px 0">기본 천장: <b>#${d.firstPity.rawNo} ${d.firstPity.name}</b><br>현재 천장 직전 일반맥: #${currentPrev.rawNo} ${currentPrev.name}<br>선택한 천장 전 일반 원시맥: #${sourceRaw} ${sourceName}<br>필요한 일반맥 생략 수: <b>${needDel}개</b></div>`;
 if(needDel<=0){box.innerHTML=h+'<div class="good">이미 이 원시맥이 천장 직전입니다. 추가 잡맥 조작이 필요 없습니다.</div>';return}

 const slots=+QUAL[String(d.pityState.zizhi)]?.slots||0;
 const oneLockCost=+(COST?.[slots]?.[1]??0);
 if(slots<=0){box.innerHTML=h+'<div class="warn">계산용 열린 칸 수를 확인할 수 없습니다.</div>';return}

 const deleted=new Set();
 const steps=[];
 const maxSteps=Math.min(24,needDel+8);
 function remaining(){return pre.filter(x=>!deleted.has(+x.rawNo));}
 function grouped(){
   const a=remaining(),gs=[];
   for(let i=0;i<a.length;i+=slots)gs.push(a.slice(i,i+slots));
   return gs;
 }
 function tailLeft(){return remaining().filter(x=>+x.rawNo>targetRaw).length;}
 function nearestCandidate(){
   const gs=grouped();
   // Closest to pity first: scan later groups backward, and later raw rows backward inside the group.
   for(let g=gs.length-1;g>=1;g--){
     const prev=gs[g-1],cur=[...gs[g]].sort((a,b)=>b.rawNo-a.rawNo);
     for(const c of cur){
       const matches=[...prev].filter(p=>+p.id===+c.id).sort((a,b)=>b.rawNo-a.rawNo);
       if(matches.length)return {lock:matches[0],del:c,group:g};
     }
   }
   return null;
 }

 let guard=0;
 while(tailLeft()>0 && steps.length<maxSteps && guard++<64){
   const c=nearestCandidate();
   if(!c)break;
   deleted.add(+c.del.rawNo);
   steps.push({lockRaw:+c.lock.rawNo,deleteRaw:+c.del.rawNo,name:c.del.name,beforeTarget:+c.del.rawNo<targetRaw,tailAfter:tailLeft()});
 }

 if(tailLeft()>0){
   h+=`<div class="warn">천장에 가까운 중복부터 순서대로 <b>${steps.length}단계</b> 재구성했지만, 현재 규칙으로는 뒤쪽 원시맥 ${tailLeft()}개가 남아 확정 경로를 완성하지 못했습니다.<br>모든 중복 후보를 전수 탐색하지 않도록 최적화했기 때문에 여기서 중단합니다.</div>`;
   if(steps.length){
     h+='<div class="small" style="margin-top:8px">계산된 단계: '+steps.map((s,i)=>`${i+1}) #${s.lockRaw} ${s.name} 잠금 → #${s.deleteRaw} ${s.name} 제거`).join(' / ')+'</div>';
   }
   box.innerHTML=h;return;
 }

 const total=steps.length*oneLockCost;
 h+=`<div class="good"><b>가까운 순서 최소루트</b> · 잠금 세수 <b>${steps.length}회</b> · 추가 소모 <b>${total}단</b></div>`;
 h+='<div class="card" style="padding:10px;margin-top:8px"><b>실행 순서</b><ol style="margin:7px 0 0 20px;padding:0">';
 for(const s of steps){
   h+=`<li style="margin:5px 0"><b>#${s.lockRaw} ${s.name}</b> 잠금 → 1회 세수 → 재구성된 다음 3칸에서 <b>#${s.deleteRaw} ${s.name}</b> 중복 제거 → 잠금 해제${s.beforeTarget?' <span class="small">(목표보다 앞쪽 재배치)</span>':''}</li>`;
 }
 h+='</ol></div>';
 h+=`<div class="small" style="line-height:1.7;margin-top:8px">각 단계마다 남은 원시맥을 ${slots}칸 단위로 다시 묶은 뒤, <b>천장에 가장 가까운 중복 1개만</b> 다음 단계로 사용합니다. 전수 분기 탐색은 하지 않습니다.<br>최종 목표: <b>#${sourceRaw} ${sourceName}</b>이 천장 직전이 되어 다음 천장이 <b>${target}</b>으로 계산됩니다.</div>`;
 box.innerHTML=h;
}'''
text=text[:start]+new_func+text[end:]

# Explanatory copy: exchanges are still all precomputed; only route search is click-only and optimized.
text=text.replace('삭제마다 3칸 테이블을 재구성하는 분기 탐색으로 최소 세수단 경로를 계산합니다.','교체맥 15개는 모두 표시하고, 최소 세수단 경로는 원하는 원시맥을 눌렀을 때만 가까운 중복부터 순차 계산합니다.')
text=text.replace('삭제마다 3칸 테이블을 다시 구성해 앞쪽 중복까지 포함한 최소 경로를 탐색합니다.','교체맥 15개는 그대로 표시하며, 최소루트는 원시맥 클릭 시 천장에 가까운 중복부터 순차 재구성합니다.')
text=text.replace('그 원시맥을 천장 직전으로 당기는 최소소모 루트를 전체 분기 탐색합니다.','그 원시맥을 눌렀을 때만 천장에 가까운 중복부터 최소소모 루트를 계산합니다.')

for x in [
 '1. 천장 전 모든 원시맥 보기',
 '2. 원시 #700~천장 직전 교체맥 보기',
 'const minRaw=700;',
 'for(let i=0;i<15;i++)h+=`<td class="q4">${r.draws[i]?.name||\'-\'}</td>`;',
 'function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol)',
 'function nearestCandidate()',
 '천장에 가장 가까운 중복 1개만',
 'daoRawBeforeBtn.onclick=showDaoRawBeforeV288',
 'daoExchangeWindowBtn.onclick=showDaoExchangeWindowV288'
]:
 if x not in text: raise SystemExit('v3.03 guard missing: '+x)
if 'expanded<60000' in text or 'const queue=[' in text: raise SystemExit('exhaustive branch search remains')

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.03','file':'Nangman_Integrated_Simulator_v3_03.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.03',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.03</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v303_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.03: #700+ exchange table; all exchange 1-15 shown; click-only nearest-first route search')
