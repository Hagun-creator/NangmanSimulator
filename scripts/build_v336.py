from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_35.html')
DST=Path('Nangman_Integrated_Simulator_v3_36.html')
if not SRC.exists(): raise SystemExit('v3.35 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.35','v3.36').replace('v3_35','v3_36')
text=re.sub(r'(?<![0-9])3\.35(?![0-9])','3.36',text)
text=re.sub(r'<script id="stable-root-url-v335">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v336">try{if(/Nangman_Integrated_Simulator_v3_36\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Tighten the target-seed engine around the user's practical lower bound:
# location/skip N starts solution checking at N*4 pills. Lower-cost states are only transit states.
old="function heapCmp(a,b){return a.cost-b.cost||a.need-b.need||a.stall-b.stall||b.startIndex-a.startIndex||a.depth-b.depth}"
new="function heapCmp(a,b){return a.score-b.score||a.need-b.need||a.cost-b.cost||a.stall-b.stall||b.startIndex-a.startIndex||a.depth-b.depth}"
if old not in text: raise SystemExit('heapCmp line missing')
text=text.replace(old,new,1)

old="const maxExtraCost=Math.max(24,goalNeed*4+24);\n const maxNodes=Math.max(1800,Math.min(5200,1800+goalNeed*180));\n const needSlack=Math.max(2,Math.min(6,Math.ceil(goalNeed/6)));"
new="const solutionCostFloor=Math.max(0,goalNeed*4);\n const maxExtraCost=Math.max(24,solutionCostFloor+32);\n const maxNodes=Math.max(1200,Math.min(3600,1200+goalNeed*120));\n const needSlack=Math.max(2,Math.min(5,Math.ceil(goalNeed/7)));\n const BEAM_PER_CELL=8;\n const cellSeen=new Map();\n function scoreOf(cost,need){return cost+Math.max(0,need)*4}\n function admitCell(cost,need,startIndex){\n   const layer=Math.floor(cost/4),key=layer+'|'+need;\n   let a=cellSeen.get(key);if(!a){a=[];cellSeen.set(key,a)}\n   const q={cost,need,startIndex};a.push(q);a.sort((x,y)=>y.startIndex-x.startIndex||x.cost-y.cost);\n   if(a.length>BEAM_PER_CELL)a.length=BEAM_PER_CELL;\n   return a.includes(q);\n }"
if old not in text: raise SystemExit('cost/maxNodes block missing')
text=text.replace(old,new,1)

old="const n={st,cost:0,need,stall:0,startIndex:i,depth:0,parent:null,action:null,startPg:pages[i],probe:pi.probe,hasLock:false};"
new="const n={st,cost:0,need,score:scoreOf(0,need),stall:0,startIndex:i,depth:0,parent:null,action:null,startPg:pages[i],probe:pi.probe,hasLock:false};"
if old not in text: raise SystemExit('start node line missing')
text=text.replace(old,new,1)

old="if(cur.need===0&&cur.hasLock&&cur.probe&&+cur.probe.seed===+targetSeed){"
new="if(cur.cost>=solutionCostFloor&&cur.need===0&&cur.hasLock&&cur.probe&&+cur.probe.seed===+targetSeed){"
if old not in text: raise SystemExit('goal condition missing')
text=text.replace(old,new,1)

old="const nn={st:tr.state,cost:nc,need,stall,startIndex:cur.startIndex,depth:cur.depth+1,parent:cur,action:actionRecord(op.kind,op.ids,tr),startPg:cur.startPg,probe:pi.probe,hasLock:cur.hasLock||op.kind!=='free'};\n     nexts.push({nn,op,improved,delta:cur.need-need});"
new="const nn={st:tr.state,cost:nc,need,score:scoreOf(nc,need),stall,startIndex:cur.startIndex,depth:cur.depth+1,parent:cur,action:actionRecord(op.kind,op.ids,tr),startPg:cur.startPg,probe:pi.probe,hasLock:cur.hasLock||op.kind!=='free'};\n     nexts.push({nn,op,improved,delta:cur.need-need});"
if old not in text: raise SystemExit('next node block missing')
text=text.replace(old,new,1)

old="nexts.sort((a,b)=>(b.improved-a.improved)||b.delta-a.delta||a.nn.cost-b.nn.cost||a.nn.stall-b.nn.stall);\n   for(const {nn} of nexts.slice(0,BRANCH_KEEP)){\n     const k=stateSig(nn.st),ov=seen.get(k);\n     if(ov&&(ov.cost<nn.cost||(ov.cost===nn.cost&&ov.need<=nn.need&&ov.startIndex>=nn.startIndex)))continue;\n     seen.set(k,{cost:nn.cost,need:nn.need,startIndex:nn.startIndex});heapPush(heap,nn);\n   }"
new="nexts.sort((a,b)=>a.nn.score-b.nn.score||(b.improved-a.improved)||b.delta-a.delta||a.nn.cost-b.nn.cost||a.nn.stall-b.nn.stall);\n   for(const {nn} of nexts.slice(0,BRANCH_KEEP)){\n     // Same cost-layer / remaining-raw cell keeps only a small beam. This prevents 10k+ equivalent candidates.\n     if(!admitCell(nn.cost,nn.need,nn.startIndex))continue;\n     const k=stateSig(nn.st),ov=seen.get(k);\n     if(ov&&(ov.cost<nn.cost||(ov.cost===nn.cost&&ov.need<=nn.need&&ov.startIndex>=nn.startIndex)))continue;\n     seen.set(k,{cost:nn.cost,need:nn.need,startIndex:nn.startIndex});heapPush(heap,nn);\n   }"
if old not in text: raise SystemExit('nexts insertion block missing')
text=text.replace(old,new,1)

# Live progress: clearly show that sub-floor costs are transit-only, not candidates.
text=text.replace("`2. 기본 천장 raw: ${baseRaw!=null?'#'+baseRaw:'확인불가'} → 필요한 추가 소비 <b>${goalNeed}</b>개<br>`+\n         `3. 현재 상태: ${expanded.toLocaleString()}/${maxNodes.toLocaleString()} · 대기 ${heap.length.toLocaleString()} · 남은 raw <b>${cur.need}</b> · 비용 ${cur.cost}단<br>`+",
                  "`2. 기본 천장 raw: ${baseRaw!=null?'#'+baseRaw:'확인불가'} → 필요한 추가 소비 <b>${goalNeed}</b>개 · 정답 최소비용 <b>${solutionCostFloor}단</b><br>`+\n         `3. 현재 상태: ${expanded.toLocaleString()}/${maxNodes.toLocaleString()} · 대기 ${heap.length.toLocaleString()} · 남은 raw <b>${cur.need}</b> · 비용 ${cur.cost}단${cur.cost<solutionCostFloor?' (연결 단계 · 후보검증 안 함)':''}<br>`+",1)

text=text.replace("`2. 기본 천장 raw: ${baseRaw!=null?'#'+baseRaw:'확인불가'} → 필요한 추가 소비 <b>${goalNeed}</b>개<br>`+\n       `3. 진행: 상태 ${expanded.toLocaleString()}/${maxNodes.toLocaleString()} · 대기 ${heap.length.toLocaleString()}<br>`+\n       `4. 현재: 남은 raw <b>${cur.need}</b> · 추가비용 ${cur.cost}단 · 시작점 천장 ${pages.length-1-cur.startIndex}회차 앞<br>`+",
                  "`2. 기본 천장 raw: ${baseRaw!=null?'#'+baseRaw:'확인불가'} → 필요한 추가 소비 <b>${goalNeed}</b>개 · 정답 최소비용 <b>${solutionCostFloor}단</b><br>`+\n       `3. 진행: 상태 ${expanded.toLocaleString()}/${maxNodes.toLocaleString()} · 대기 ${heap.length.toLocaleString()}<br>`+\n       `4. 현재: 남은 raw <b>${cur.need}</b> · 추가비용 ${cur.cost}단${cur.cost<solutionCostFloor?' (연결 단계)':''} · 시작점 천장 ${pages.length-1-cur.startIndex}회차 앞<br>`+",1)

# Success label should record the enforced floor.
text=text.replace("label:'목표 seed 역산 · 실제 washOnce 검증',",
                  "label:'목표 seed 역산 · 비용하한 '+solutionCostFloor+'단부터 실제 washOnce 검증',",1)

for tok in ['solutionCostFloor=Math.max(0,goalNeed*4)','BEAM_PER_CELL=8','function scoreOf(cost,need)','function admitCell(cost,need,startIndex)','cur.cost>=solutionCostFloor','연결 단계 · 후보검증 안 함']:
    if tok not in text: raise SystemExit('v3.36 guard missing: '+tok)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.36','file':'Nangman_Integrated_Simulator_v3_36.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.36',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.36</title>' not in text[:10000]: raise SystemExit('title mismatch')
scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)
if not scripts: raise SystemExit('no scripts')
checked=0
for i,js in enumerate(scripts):
    if not js.strip(): continue
    p=Path(f'/tmp/v336_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
    checked+=1
if checked<1: raise SystemExit('no scripts checked')
print(f'built v3.36: target-seed A* with N*4 solution floor and per-cell beam; JS checked={checked}')
