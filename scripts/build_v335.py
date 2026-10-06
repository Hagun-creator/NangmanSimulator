from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_34.html')
DST=Path('Nangman_Integrated_Simulator_v3_35.html')
if not SRC.exists(): raise SystemExit('v3.34 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.34','v3.35').replace('v3_34','v3_35')
text=re.sub(r'(?<![0-9])3\.34(?![0-9])','3.35',text)
text=re.sub(r'<script id="stable-root-url-v334">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v335">try{if(/Nangman_Integrated_Simulator_v3_35\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Keep the v3.34 target-seed engine, but reduce work per expanded state and restore detailed live progress.
old="const SLICE_MS=10,UI_MS=220;"
new="const SLICE_MS=4,UI_MS=80,BRANCH_KEEP=3;"
if old not in text: raise SystemExit('slice constants missing')
text=text.replace(old,new,1)

old="const maxNodes=Math.max(2500,Math.min(14000,2500+goalNeed*450));"
new="const maxNodes=Math.max(1800,Math.min(5200,1800+goalNeed*180));"
if old not in text: raise SystemExit('maxNodes line missing')
text=text.replace(old,new,1)

old=r'''   const visible=(cur.st.talents||[]).map(t=>+t.id),ops=[{kind:'free',ids:[]}];
   for(const id of visible)ops.push({kind:'lock',ids:[id]});
   for(let i=0;i<visible.length;i++)for(let j=i+1;j<visible.length;j++)ops.push({kind:'lock',ids:[visible[i],visible[j]]});
   for(const op of ops){
     const tr=tryWash(cur.st,op.ids);if(!tr)continue;
     const edge=op.kind==='free'?0:(+tr.result.pills_used||0),nc=cur.cost+edge;if(nc>maxExtraCost)continue;
     const pi=pityInfo(tr.state);if(!pi)continue;
     const need=(targetRaw!=null&&pi.raw!=null)?(+targetRaw-+pi.raw):cur.need;
     if(need<0||need>goalNeed+needSlack)continue; // overshot target seed or moved far away
     const improved=need<cur.need;
     const stall=improved?0:(cur.stall+1);
     // Free movement is allowed to reach another visible duplicate; non-improving lock chains are capped tightly.
     if(!improved&&op.kind!=='free'&&stall>2)continue;
     if(!improved&&op.kind==='free'&&stall>5)continue;
     const nn={st:tr.state,cost:nc,need,stall,startIndex:cur.startIndex,depth:cur.depth+1,parent:cur,action:actionRecord(op.kind,op.ids,tr),startPg:cur.startPg,probe:pi.probe,hasLock:cur.hasLock||op.kind!=='free'};
     const k=stateSig(nn.st),ov=seen.get(k);
     if(ov&&(ov.cost<nc||(ov.cost===nc&&ov.need<=need&&ov.startIndex>=nn.startIndex)))continue;
     seen.set(k,{cost:nc,need,startIndex:nn.startIndex});heapPush(heap,nn);
   }

   const t=nowMs();if(t-sliceStart>=SLICE_MS){
     if(t-lastUi>=UI_MS){lastUi=t;box.innerHTML=`<div class="warn"><b>목표 seed 역산 탐색 중</b><br>`+
       `목표 seed <b>${targetSeed}</b>${targetRaw!=null?` · raw #${targetRaw}`:''}<br>`+
       `기본 천장 raw ${baseRaw!=null?'#'+baseRaw:'확인불가'} · 필요한 추가 소비 <b>${goalNeed}</b>개<br>`+
       `검사 상태 ${expanded.toLocaleString()}/${maxNodes.toLocaleString()} · 대기 ${heap.length.toLocaleString()} · 현재 남은 raw ${cur.need}<br>`+
       `현재 추가비용 ${cur.cost}단 · 목표 seed 방향으로만 탐색</div>`}
     await uiYield();sliceStart=nowMs();
   }
'''

new=r'''   const visible=(cur.st.talents||[]).map(t=>+t.id),ops=[{kind:'free',ids:[]}];
   for(const id of visible)ops.push({kind:'lock',ids:[id]});
   for(let i=0;i<visible.length;i++)for(let j=i+1;j<visible.length;j++)ops.push({kind:'lock',ids:[visible[i],visible[j]]});
   const nexts=[];
   let opNo=0,lastOpLabel='무잠금';
   for(const op of ops){
     opNo++;
     lastOpLabel=op.kind==='free'?'무잠금':op.ids.map(id=>nm(id)).join(' + ')+' 잠금';
     const tr=tryWash(cur.st,op.ids);if(!tr)continue;
     const edge=op.kind==='free'?0:(+tr.result.pills_used||0),nc=cur.cost+edge;if(nc>maxExtraCost)continue;
     const pi=pityInfo(tr.state);if(!pi)continue;
     const need=(targetRaw!=null&&pi.raw!=null)?(+targetRaw-+pi.raw):cur.need;
     if(need<0||need>goalNeed+needSlack)continue;
     const improved=need<cur.need;
     const stall=improved?0:(cur.stall+1);
     if(!improved&&op.kind!=='free'&&stall>1)continue;
     if(!improved&&op.kind==='free'&&stall>4)continue;
     const nn={st:tr.state,cost:nc,need,stall,startIndex:cur.startIndex,depth:cur.depth+1,parent:cur,action:actionRecord(op.kind,op.ids,tr),startPg:cur.startPg,probe:pi.probe,hasLock:cur.hasLock||op.kind!=='free'};
     nexts.push({nn,op,improved,delta:cur.need-need});
     // Long per-state loops were the main freeze. Yield even inside one state's 7 operation checks.
     if(opNo%2===0){
       const tt=nowMs();
       if(tt-lastUi>=UI_MS){lastUi=tt;box.innerHTML=`<div class="warn"><b>목표 seed 역산 탐색 중</b><br>`+
         `1. 목표 seed 확정: <b>${targetSeed}</b>${targetRaw!=null?` · raw #${targetRaw}`:''}<br>`+
         `2. 기본 천장 raw: ${baseRaw!=null?'#'+baseRaw:'확인불가'} → 필요한 추가 소비 <b>${goalNeed}</b>개<br>`+
         `3. 현재 상태: ${expanded.toLocaleString()}/${maxNodes.toLocaleString()} · 대기 ${heap.length.toLocaleString()} · 남은 raw <b>${cur.need}</b> · 비용 ${cur.cost}단<br>`+
         `4. 현재 동작 검사: <b>${opNo}/${ops.length}</b> · ${lastOpLabel}<br>`+
         `5. 이 상태에서 유효 후보: ${nexts.length}개</div>`}
       await uiYield();sliceStart=nowMs();
     }
   }
   // Keep only the few moves that most directly approach the already-fixed target seed.
   nexts.sort((a,b)=>(b.improved-a.improved)||b.delta-a.delta||a.nn.cost-b.nn.cost||a.nn.stall-b.nn.stall);
   for(const {nn} of nexts.slice(0,BRANCH_KEEP)){
     const k=stateSig(nn.st),ov=seen.get(k);
     if(ov&&(ov.cost<nn.cost||(ov.cost===nn.cost&&ov.need<=nn.need&&ov.startIndex>=nn.startIndex)))continue;
     seen.set(k,{cost:nn.cost,need:nn.need,startIndex:nn.startIndex});heapPush(heap,nn);
   }

   const t=nowMs();if(t-sliceStart>=SLICE_MS||expanded%20===0){
     if(t-lastUi>=UI_MS||expanded%20===0){lastUi=t;box.innerHTML=`<div class="warn"><b>목표 seed 역산 탐색 중</b><br>`+
       `1. 목표 seed: <b>${targetSeed}</b>${targetRaw!=null?` · raw #${targetRaw}`:''}<br>`+
       `2. 기본 천장 raw: ${baseRaw!=null?'#'+baseRaw:'확인불가'} → 필요한 추가 소비 <b>${goalNeed}</b>개<br>`+
       `3. 진행: 상태 ${expanded.toLocaleString()}/${maxNodes.toLocaleString()} · 대기 ${heap.length.toLocaleString()}<br>`+
       `4. 현재: 남은 raw <b>${cur.need}</b> · 추가비용 ${cur.cost}단 · 시작점 천장 ${pages.length-1-cur.startIndex}회차 앞<br>`+
       `5. 다음 후보: ${nexts.length}개 중 상위 ${Math.min(BRANCH_KEEP,nexts.length)}개만 계속 탐색</div>`}
     await uiYield();sliceStart=nowMs();
   }
'''

if old not in text: raise SystemExit('v3.34 expansion block missing')
text=text.replace(old,new,1)

for tok in ['BRANCH_KEEP=3','현재 동작 검사','nexts.slice(0,BRANCH_KEEP)','expanded%20===0','maxNodes=Math.max(1800']:
    if tok not in text: raise SystemExit('v3.35 guard missing: '+tok)

Path('latest.json').write_text(json.dumps({'version':'v3.35','file':'Nangman_Integrated_Simulator_v3_35.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.35',s);r.write_text(s,encoding='utf-8')
DST.write_text(text,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.35</title>' not in text[:10000]: raise SystemExit('title mismatch')
scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)
if not scripts: raise SystemExit('no scripts')
checked=0
for i,js in enumerate(scripts):
    if not js.strip():continue
    p=Path(f'/tmp/v335_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
    checked+=1
if checked<1: raise SystemExit('no scripts checked')
print(f'built v3.35: branch-capped target-seed search with detailed live progress; JS checked={checked}')
