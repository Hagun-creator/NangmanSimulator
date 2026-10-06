from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_31.html')
DST=Path('Nangman_Integrated_Simulator_v3_32.html')
if not SRC.exists(): raise SystemExit('v3.31 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.31','v3.32').replace('v3_31','v3_32')
text=re.sub(r'(?<![0-9])3\.31(?![0-9])','3.32',text)
text=re.sub(r'<script id="stable-root-url-v331">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v332">try{if(/Nangman_Integrated_Simulator_v3_32\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

def bounds(s):
    a=s.find('async function showDaoPullRouteV290(')
    b=s.find('\nasync function showDaoExchangeWindowV288(){',a)
    if a<0 or b<0: raise SystemExit('route boundary missing')
    return a,b

def balanced_block_end(s,start):
    p=s.find('{',start)
    if p<0:return -1
    depth=0;quote=None;esc=False;line=False;block=False;i=p
    while i<len(s):
        c=s[i];n=s[i+1] if i+1<len(s) else ''
        if line:
            if c=='\n':line=False
            i+=1;continue
        if block:
            if c=='*' and n=='/':block=False;i+=2;continue
            i+=1;continue
        if quote:
            if esc:esc=False;i+=1;continue
            if c=='\\':esc=True;i+=1;continue
            if c==quote:quote=None
            i+=1;continue
        if c=='/' and n=='/':line=True;i+=2;continue
        if c=='/' and n=='*':block=True;i+=2;continue
        if c in ("'",'"','`'):quote=c;i+=1;continue
        if c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return i+1
        i+=1
    return -1

a,b=bounds(text);route=text[a:b]
anchor=route.find(' const targetSkip=Math.max(0,targetShift);')
start=route.rfind(' outer:{',0,anchor) if anchor>=0 else -1
end=balanced_block_end(route,start) if start>=0 else -1
if start<0 or end<0: raise SystemExit('v3.31 engine block missing')
old=route[start:end]
if 'function makeEpisodes()' not in old: raise SystemExit('unexpected v3.31 engine')

new=r''' outer:{
 // v3.32 exact-state route search.
 // Every edge is an actual washOnce() transition. No static page arithmetic after a lock.
 const targetSkip=Math.max(0,targetShift);
 const baselineCost=targetSkip>0?targetSkip*4:0;
 const maxExtraCost=Math.max(24,baselineCost+32);
 const maxNodes=Math.max(30000,Math.min(120000,30000+targetSkip*7000));

 function stateSig(st){
   if(typeof stateKeyRoute==='function')return stateKeyRoute(st);
   return [st.seed,st.born_talent_rc||0,st.luck_seed||0,st.luck_seed_inited?1:0,st.tal_lucky,
     (st.talents||[]).map(x=>+x.id).join(',')].join('|');
 }
 function heapPush(h,x){
   h.push(x);let i=h.length-1;
   while(i>0){let p=(i-1)>>1;if(heapCmp(h[p],x)<=0)break;h[i]=h[p];i=p}h[i]=x;
 }
 function heapPop(h){
   if(!h.length)return null;const root=h[0],last=h.pop();if(!h.length)return root;
   let i=0;while(true){let l=i*2+1,r=l+1;if(l>=h.length)break;let c=(r<h.length&&heapCmp(h[r],h[l])<0)?r:l;if(heapCmp(last,h[c])<=0)break;h[i]=h[c];i=c}h[i]=last;return root;
 }
 function heapCmp(a,b){return a.cost-b.cost||a.lockWashes-b.lockWashes||b.startIndex-a.startIndex||a.depth-b.depth}
 function unlockedCopy(st){const x=dc(st);x.talents=(x.talents||[]).map(t=>({...t,locked:false}));return x}
 function tryWash(st,lockIds){
   let x=unlockedCopy(st);const set=new Set(lockIds||[]);x.talents=(x.talents||[]).map(t=>({...t,locked:set.has(+t.id)}));
   let tr;try{tr=washOnce(x)}catch(_){return null}
   if(tr.result?.got_gold||tr.result?.was_pity)return null;
   const y=unlockedCopy(tr.state);
   return {state:y,result:tr.result,before:x};
 }
 function goalProbe(st){
   let p=null;try{p=probePitySeed(unlockedCopy(st))}catch(_){return null}
   probes++;return p&&+p.seed===+targetSeed?p:null;
 }
 function actionRecord(kind,lockIds,tr,startIndex){
   return {kind,lockIds:(lockIds||[]).slice(),pills:+tr.result.pills_used||0,beforeSeed:+tr.before.seed,afterSeed:+tr.state.seed,
     talents:(tr.result.talents||[]).map(t=>({id:+t.id,name:nm(t.id)})),startIndex};
 }
 function groupedEpisodes(actions,startPg){
   const out=[];let cur=null;
   for(const a of actions){
     if(a.kind==='free'){cur=null;continue}
     const key=a.lockIds.slice().sort((x,y)=>x-y).join(',');
     if(cur&&cur.key===key){cur.episode.hold++;cur.steps.push({beforeSeed:a.beforeSeed,afterSeed:a.afterSeed,pills:a.pills,talents:a.talents.map(x=>x.name)});continue}
     cur={key,episode:{pg:startPg,lockIds:a.lockIds.slice(),hold:1,skip:0,cost:a.pills,kind:a.lockIds.length===1?'1잠금 실제상태':'2잠금 실제상태'},
       steps:[{beforeSeed:a.beforeSeed,afterSeed:a.afterSeed,pills:a.pills,talents:a.talents.map(x=>x.name)}]};out.push(cur);
   }
   return out;
 }

 const heap=[],seen=new Map();
 // All naturally reachable baseline pages are zero-cost start points. Near-pity start wins ties.
 for(let i=0;i<pages.length;i++){
   const st=unlockedCopy(pages[i]);
   const n={st,cost:0,lockWashes:0,startIndex:i,depth:0,actions:[],startPg:pages[i]};
   const k=stateSig(st),old=seen.get(k);if(!old||i>old.startIndex){seen.set(k,{cost:0,startIndex:i});heapPush(heap,n)}
 }
 let expanded=0,lastYield=0;
 while(heap.length&&expanded<maxNodes){
   const cur=heapPop(heap);expanded++;
   const sig=stateSig(cur.st),sv=seen.get(sig);
   if(sv&&(cur.cost>sv.cost||(cur.cost===sv.cost&&cur.startIndex<sv.startIndex)))continue;
   const gp=goalProbe(cur.st);
   if(gp&&cur.actions.some(a=>a.kind!=='free')){
     const eps=groupedEpisodes(cur.actions,cur.startPg);
     const firstLock=cur.actions.find(a=>a.kind!=='free');
     const first=eps[0]?.episode||{pg:cur.startPg,lockIds:firstLock?.lockIds||[],hold:1};
     const rawSlots=dc(cur.startPg.__daoRawSlots||[]),lockRawSlots=rawSlots.filter(x=>(first.lockIds||[]).includes(+x.id));
     best={cost:cur.cost,dist:pages.length-1-cur.startIndex,hold:first.hold||1,lockIds:(first.lockIds||[]).slice(),path:eps[0]?.steps||[],probe:gp,checked:expanded,probes,win:pages.length,
       rawStart:+cur.startPg.__daoRawStart,rawEnd:+cur.startPg.__daoRawEnd,rawSlots,lockRawSlots,trace:null,firstFree:null,
       label:'실제 washOnce 상태 비용우선 탐색',estimatedSkips:targetSkip,baselineCost,multiEpisodes:eps,episodeCount:eps.length,expandedNodes:expanded};
     break;
   }
   if(cur.cost>maxExtraCost)continue;
   const visible=(cur.st.talents||[]).map(t=>+t.id);
   const ops=[{kind:'free',ids:[]}];
   for(const id of visible)ops.push({kind:'lock',ids:[id]});
   for(let i=0;i<visible.length;i++)for(let j=i+1;j<visible.length;j++)ops.push({kind:'lock',ids:[visible[i],visible[j]]});
   for(const op of ops){
     const tr=tryWash(cur.st,op.ids);if(!tr)continue;
     const edge=op.kind==='free'?0:(+tr.result.pills_used||0);
     const nc=cur.cost+edge;if(nc>maxExtraCost)continue;
     const na=cur.actions.concat([actionRecord(op.kind,op.ids,tr,cur.startIndex)]);
     const nn={st:tr.state,cost:nc,lockWashes:cur.lockWashes+(op.kind==='free'?0:1),startIndex:cur.startIndex,depth:cur.depth+1,actions:na,startPg:cur.startPg};
     const k=stateSig(nn.st),ov=seen.get(k);
     if(ov&&(ov.cost<nc||(ov.cost===nc&&ov.startIndex>=nn.startIndex)))continue;
     seen.set(k,{cost:nc,startIndex:nn.startIndex});heapPush(heap,nn);
   }
   if(expanded-lastYield>=400){lastYield=expanded;box.innerHTML=`<div class="warn"><b>실제 상태 루트 탐색 중</b><br>`+
     `목표 seed <b>${targetSeed}</b> · 목표 위치 ${targetSkip} · 기준 ${baselineCost}단<br>`+
     `실제 상태 ${expanded.toLocaleString()}/${maxNodes.toLocaleString()} · 대기 ${heap.length.toLocaleString()} · seed 검증 ${probes.toLocaleString()}회<br>`+
     `현재 비용 ${cur.cost}단 · 시작 천장 ${pages.length-1-cur.startIndex}회차 앞</div>`;await uiYield()}
 }
 }
'''
route=route[:start]+new+route[end:]
for tok in ['actual washOnce','실제 washOnce 상태 비용우선 탐색','function tryWash(','maxNodes','groupedEpisodes']:
    if tok not in route: raise SystemExit('v3.32 token missing '+tok)
if 'function makeEpisodes()' in route: raise SystemExit('v3.31 static DP remains')

prefix=text[:a];suffix=text[b:];out=prefix+route+suffix
DST.write_text(out,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.32','file':'Nangman_Integrated_Simulator_v3_32.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.32',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.32</title>' not in out[:10000]: raise SystemExit('title mismatch')
scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',out,re.I|re.S)
if not scripts: raise SystemExit('no scripts')
checked=0
for i,js in enumerate(scripts):
    if not js.strip():continue
    p=Path(f'/tmp/v332_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
    checked+=1
if checked<1: raise SystemExit('no scripts checked')
print(f'built v3.32 exact-state route search; JS checked={checked}')
