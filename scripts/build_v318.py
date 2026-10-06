from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_17.html')
DST=Path('Nangman_Integrated_Simulator_v3_18.html')
if not SRC.exists(): raise SystemExit('v3.17 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.17','v3.18').replace('v3_17','v3_18')
text=re.sub(r'(?<![0-9])3\.17(?![0-9])','3.18',text)
text=re.sub(r'<script id="stable-root-url-v317">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v318">try{if(/Nangman_Integrated_Simulator_v3_18\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Patch only the route output / bookkeeping. Search algorithm remains v3.17.
a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]

old=""" // Baseline pages once.
 const pages=[];let scan=unlocked(base),guard=3000;
 while(guard-->0){const tr=washOnce(scan);scan=tr.state;if(tr.result?.got_gold)break;pages.push(unlocked(scan));}
 if(guard<=0){box.innerHTML='<div class=\"warn\">기본 천장 이전 상태 재현 한도를 초과했습니다.</div>';return}
"""
new=""" // Baseline pages once. Attach exact original raw numbers to every slot.
 const pages=[];let scan=unlocked(base),guard=3000;
 while(guard-->0){const tr=washOnce(scan);scan=tr.state;if(tr.result?.got_gold)break;pages.push(unlocked(scan));}
 if(guard<=0){box.innerHTML='<div class=\"warn\">기본 천장 이전 상태 재현 한도를 초과했습니다.</div>';return}
 const rawByNo=new Map();
 for(let i=0;i<pages.length;i++){
   const distFromPityPage=pages.length-1-i;
   const rawEnd=(+d.firstPity.rawNo)-1-distFromPityPage*slots;
   const rawStart=rawEnd-slots+1;
   const rs=(pages[i].talents||[]).slice(0,slots).map((t,j)=>({rawNo:rawStart+j,id:+t.id,name:nm(t.id)}));
   pages[i].__daoRawStart=rawStart;pages[i].__daoRawEnd=rawEnd;pages[i].__daoRawSlots=rs;
   for(const x of rs)rawByNo.set(+x.rawNo,x);
 }
 function traceEpisode(pg,lockIds,holdCount){
   let cursor=+pg.__daoRawEnd+1;const washes=[];
   for(let w=1;w<=holdCount;w++){
     const seen=new Set(lockIds.map(Number)),accepted=[],skipped=[];
     while(accepted.length<slots-lockIds.length && cursor<+d.firstPity.rawNo){
       const x=rawByNo.get(cursor);cursor++;
       if(!x)continue;
       if(seen.has(+x.id)){skipped.push(x);continue}
       seen.add(+x.id);accepted.push(x);
     }
     washes.push({accepted,skipped,cursorAfter:cursor});
   }
   return {washes,cursor};
 }
 function traceFreePage(startCursor){
   let cursor=startCursor,seen=new Set(),accepted=[],skipped=[];
   while(accepted.length<slots && cursor<+d.firstPity.rawNo){
     const x=rawByNo.get(cursor);cursor++;
     if(!x)continue;
     if(seen.has(+x.id)){skipped.push(x);continue}
     seen.add(+x.id);accepted.push(x);
   }
   return {accepted,skipped,cursorAfter:cursor};
 }
"""
if old not in route: raise SystemExit('baseline block not found')
route=route.replace(old,new,1)

oldcand="""           const cand={cost:sh.cost,dist,hold:sh.hold,lockIds:dc(lockIds),path:dc(path),probe,checked,probes,win};
"""
newcand="""           const rawSlots=dc(pg.__daoRawSlots||[]);
           const lockRawSlots=rawSlots.filter(x=>lockIds.includes(+x.id));
           const trace=traceEpisode(pg,lockIds,sh.hold);
           const firstFree=traceFreePage(trace.cursor);
           const cand={cost:sh.cost,dist,hold:sh.hold,lockIds:dc(lockIds),path:dc(path),probe,checked,probes,win,
             rawStart:+pg.__daoRawStart,rawEnd:+pg.__daoRawEnd,rawSlots,lockRawSlots,trace,firstFree};
"""
if oldcand not in route: raise SystemExit('candidate block not found')
route=route.replace(oldcand,newcand,1)

start=route.find(" const lockNames=best.lockIds.map(id=>nm(id)).join(' + ');")
end=route.find(" box.innerHTML=h;",start)
if start<0 or end<0: raise SystemExit('output block missing')
end=end+len(" box.innerHTML=h;")
newout=r''' const lockNames=best.lockRawSlots.length?best.lockRawSlots.map(x=>`#${x.rawNo} ${x.name}`).join(' + '):best.lockIds.map(id=>nm(id)).join(' + ');
 const pageText=(best.rawSlots||[]).map(x=>`#${x.rawNo} ${x.name}`).join(' · ');
 let h=`<div class="good"><b>목표 seed 도달 최소비용 경로</b> · 목표 seed <b>${targetSeed}</b> · 추가 잠금 세수 소모 <b>${best.cost.toLocaleString()}단</b></div>`+
   `<div class="small" style="line-height:1.8;margin:6px 0">시작 페이지: <b>원시 #${best.rawStart}~#${best.rawEnd}</b> · 천장에서 ${best.dist}회차 앞<br>`+
   `시작 3칸: <b>${pageText}</b><br>잠금 대상: <b>${lockNames}</b> · 유지 ${best.hold}회<br>`+
   `검사: 잠금 ${checked.toLocaleString()}회 · probe ${probes.toLocaleString()}회 · 탐색범위 ${best.win}회차 이내</div>`;
 h+='<div class="card" style="padding:10px"><b>실제 실행 순서</b><ol style="margin:7px 0 0 20px;padding:0">';
 h+=`<li><b>${lockNames}</b>을 잠급니다.<br><span class="small">이때 화면 3칸: ${pageText}</span></li>`;
 for(let i=0;i<best.path.length;i++){
   const p=best.path[i],tr=best.trace?.washes?.[i]||{accepted:[],skipped:[]};
   const accepted=tr.accepted.map(x=>`#${x.rawNo} ${x.name}`).join(' · ')||'-';
   const skipped=tr.skipped.map(x=>`#${x.rawNo} ${x.name}`).join(' · ');
   h+=`<li><b>잠금 유지 ${i+1}회 세수</b> · ${p.pills}단<br>`+
      `<span class="small">새로 채워진 원시맥: <b>${accepted}</b>${skipped?`<br>잠금 중복으로 스킵: <b>${skipped}</b>`:''}<br>`+
      `세수 결과 3칸: ${p.talents.join(' · ')}</span></li>`;
 }
 const ff=best.firstFree||{accepted:[],skipped:[]};
 const ffAcc=ff.accepted.map(x=>`#${x.rawNo} ${x.name}`).join(' · ')||'-';
 const ffSkip=ff.skipped.map(x=>`#${x.rawNo} ${x.name}`).join(' · ');
 h+=`<li><b>여기서 즉시 잠금 해제</b>합니다. 잠금 세수는 더 하지 않습니다.</li>`;
 h+=`<li>잠금 해제 후 첫 무잠금 세수의 원시 순서: <b>${ffAcc}</b>${ffSkip?`<br><span class="small">같은 페이지 중복 스킵: ${ffSkip}</span>`:''}</li>`;
 h+=`<li>그 뒤 무잠금 세수를 계속해서, 총 <b>${best.probe.washes}회</b>의 무잠금 세수 후 천장 발생 직전 Born seed <b>${best.probe.seed}</b>에 도달합니다.</li>`;
 h+='</ol></div>';
 box.innerHTML=h;'''
route=route[:start]+newout+route[end:]

for x in ['__daoRawSlots','traceEpisode','lockRawSlots','실제 실행 순서','여기서 즉시 잠금 해제','잠금 중복으로 스킵']:
 if x not in route: raise SystemExit('v3.18 guard missing: '+x)
text=text[:a]+route+text[b:]

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.18','file':'Nangman_Integrated_Simulator_v3_18.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.18',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.18</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v318_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.18: actionable raw-number route instructions')
