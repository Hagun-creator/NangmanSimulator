from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_32.html')
DST=Path('Nangman_Integrated_Simulator_v3_33.html')
if not SRC.exists(): raise SystemExit('v3.32 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.32','v3.33').replace('v3_32','v3_33')
text=re.sub(r'(?<![0-9])3\.32(?![0-9])','3.33',text)
text=re.sub(r'<script id="stable-root-url-v332">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v333">try{if(/Nangman_Integrated_Simulator_v3_33\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

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
if start<0 or end<0: raise SystemExit('v3.32 engine block missing')
old=route[start:end]
if 'v3.32 exact-state route search' not in old: raise SystemExit('unexpected v3.32 engine')

new=r''' outer:{
 // v3.33 time-sliced exact-state route search.
 // Same exact washOnce state graph as v3.32, but low-memory parent links and cooperative yielding.
 const targetSkip=Math.max(0,targetShift);
 const baselineCost=targetSkip>0?targetSkip*4:0;
 const maxExtraCost=Math.max(24,baselineCost+32);
 const maxNodes=Math.max(30000,Math.min(120000,30000+targetSkip*7000));
 const SLICE_MS=12,UI_MS=220;

 function stateSig(st){
   if(typeof stateKeyRoute==='function')return stateKeyRoute(st);
   return [st.seed,st.born_talent_rc||0,st.luck_seed||0,st.luck_seed_inited?1:0,st.tal_lucky,
     (st.talents||[]).map(x=>+x.id).join(',')].join('|');
 }
 function heapCmp(a,b){return a.cost-b.cost||a.lockWashes-b.lockWashes||b.startIndex-a.startIndex||a.depth-b.depth}
 function heapPush(h,x){h.push(x);let i=h.length-1;while(i>0){let p=(i-1)>>1;if(heapCmp(h[p],x)<=0)break;h[i]=h[p];i=p}h[i]=x}
 function heapPop(h){if(!h.length)return null;const root=h[0],last=h.pop();if(!h.length)return root;let i=0;while(true){let l=i*2+1,r=l+1;if(l>=h.length)break;let c=(r<h.length&&heapCmp(h[r],h[l])<0)?r:l;if(heapCmp(last,h[c])<=0)break;h[i]=h[c];i=c}h[i]=last;return root}
 function unlockedCopy(st){const x=dc(st);x.talents=(x.talents||[]).map(t=>({...t,locked:false}));return x}
 function tryWash(st,lockIds){
   let x=unlockedCopy(st);const set=new Set(lockIds||[]);x.talents=(x.talents||[]).map(t=>({...t,locked:set.has(+t.id)}));
   let tr;try{tr=washOnce(x)}catch(_){return null}
   if(tr.result?.got_gold||tr.result?.was_pity)return null;
   return {state:unlockedCopy(tr.state),result:tr.result,before:x};
 }
 function goalProbe(st){let p=null;try{p=probePitySeed(unlockedCopy(st))}catch(_){return null}probes++;return p&&+p.seed===+targetSeed?p:null}
 function actionRecord(kind,lockIds,tr){return {kind,lockIds:(lockIds||[]).slice(),pills:+tr.result.pills_used||0,beforeSeed:+tr.before.seed,afterSeed:+tr.state.seed,talents:(tr.result.talents||[]).map(t=>({id:+t.id,name:nm(t.id)}))}}
 function collectActions(node){const rev=[];let n=node;while(n&&n.action){rev.push(n.action);n=n.parent}rev.reverse();return rev}
 function groupedEpisodes(actions,startPg){
   const out=[];let cur=null;
   for(const a of actions){
     if(a.kind==='free'){cur=null;continue}
     const key=a.lockIds.slice().sort((x,y)=>x-y).join(',');
     if(cur&&cur.key===key){cur.episode.hold++;cur.episode.cost+=a.pills;cur.steps.push({beforeSeed:a.beforeSeed,afterSeed:a.afterSeed,pills:a.pills,talents:a.talents.map(x=>x.name)});continue}
     cur={key,episode:{pg:startPg,lockIds:a.lockIds.slice(),hold:1,skip:0,cost:a.pills,kind:a.lockIds.length===1?'1잠금 실제상태':'2잠금 실제상태'},steps:[{beforeSeed:a.beforeSeed,afterSeed:a.afterSeed,pills:a.pills,talents:a.talents.map(x=>x.name)}]};out.push(cur)
   }
   return out;
 }
 function nowMs(){return (typeof performance!=='undefined'&&performance.now)?performance.now():Date.now()}

 const heap=[],seen=new Map();
 for(let i=0;i<pages.length;i++){
   const st=unlockedCopy(pages[i]),n={st,cost:0,lockWashes:0,startIndex:i,depth:0,parent:null,action:null,startPg:pages[i],hasLock:false};
   const k=stateSig(st),oldSeen=seen.get(k);if(!oldSeen||i>oldSeen.startIndex){seen.set(k,{cost:0,startIndex:i});heapPush(heap,n)}
 }
 let expanded=0,sliceStart=nowMs(),lastUi=0;
 while(heap.length&&expanded<maxNodes){
   const cur=heapPop(heap);expanded++;
   const sig=stateSig(cur.st),sv=seen.get(sig);
   if(sv&&(cur.cost>sv.cost||(cur.cost===sv.cost&&cur.startIndex<sv.startIndex)))continue;

   // Probing every free intermediate state was the main v3.32 CPU spike. A route can only change Born flow after a lock action,
   // so probe newly changed locked states; later lock actions will be probed in turn.
   if(cur.hasLock&&cur.action&&cur.action.kind!=='free'){
     const gp=goalProbe(cur.st);
     if(gp){
       const actions=collectActions(cur),eps=groupedEpisodes(actions,cur.startPg),firstLock=actions.find(a=>a.kind!=='free');
       const first=eps[0]?.episode||{pg:cur.startPg,lockIds:firstLock?.lockIds||[],hold:1};
       const rawSlots=dc(cur.startPg.__daoRawSlots||[]),lockRawSlots=rawSlots.filter(x=>(first.lockIds||[]).includes(+x.id));
       best={cost:cur.cost,dist:pages.length-1-cur.startIndex,hold:first.hold||1,lockIds:(first.lockIds||[]).slice(),path:eps[0]?.steps||[],probe:gp,checked:expanded,probes,win:pages.length,
         rawStart:+cur.startPg.__daoRawStart,rawEnd:+cur.startPg.__daoRawEnd,rawSlots,lockRawSlots,trace:null,firstFree:null,label:'실제 washOnce 상태 · 시간분할 비용우선 탐색',
         estimatedSkips:targetSkip,baselineCost,multiEpisodes:eps,episodeCount:eps.length,expandedNodes:expanded};
       break;
     }
   }
   if(cur.cost<=maxExtraCost){
     const visible=(cur.st.talents||[]).map(t=>+t.id),ops=[{kind:'free',ids:[]}];
     for(const id of visible)ops.push({kind:'lock',ids:[id]});
     for(let i=0;i<visible.length;i++)for(let j=i+1;j<visible.length;j++)ops.push({kind:'lock',ids:[visible[i],visible[j]]});
     for(const op of ops){
       const tr=tryWash(cur.st,op.ids);if(!tr)continue;
       const edge=op.kind==='free'?0:(+tr.result.pills_used||0),nc=cur.cost+edge;if(nc>maxExtraCost)continue;
       const nn={st:tr.state,cost:nc,lockWashes:cur.lockWashes+(op.kind==='free'?0:1),startIndex:cur.startIndex,depth:cur.depth+1,parent:cur,
         action:actionRecord(op.kind,op.ids,tr),startPg:cur.startPg,hasLock:cur.hasLock||op.kind!=='free'};
       const k=stateSig(nn.st),ov=seen.get(k);if(ov&&(ov.cost<nc||(ov.cost===nc&&ov.startIndex>=nn.startIndex)))continue;
       seen.set(k,{cost:nc,startIndex:nn.startIndex});heapPush(heap,nn);
     }
   }

   const t=nowMs();
   if(t-sliceStart>=SLICE_MS){
     if(t-lastUi>=UI_MS){lastUi=t;box.innerHTML=`<div class="warn"><b>실제 상태 루트 탐색 중</b><br>`+
       `목표 seed <b>${targetSeed}</b> · 목표 위치 ${targetSkip} · 기준 ${baselineCost}단<br>`+
       `실제 상태 ${expanded.toLocaleString()}/${maxNodes.toLocaleString()} · 대기 ${heap.length.toLocaleString()} · seed 검증 ${probes.toLocaleString()}회<br>`+
       `현재 비용 ${cur.cost}단 · 브라우저 응답 유지용 시간분할 탐색</div>`}
     await uiYield();sliceStart=nowMs();
   }
 }
 }
'''
route=route[:start]+new+route[end:]
for tok in ['v3.33 time-sliced exact-state route search','const SLICE_MS=12','function collectActions(node)','cur.hasLock&&cur.action','await uiYield();sliceStart=nowMs()']:
    if tok not in route: raise SystemExit('v3.33 token missing '+tok)
if 'actions:na' in route or 'cur.actions.concat' in route: raise SystemExit('v3.32 path copying remains')

out=text[:a]+route+text[b:]
DST.write_text(out,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.33','file':'Nangman_Integrated_Simulator_v3_33.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.33',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.33</title>' not in out[:10000]: raise SystemExit('title mismatch')
scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',out,re.I|re.S)
if not scripts: raise SystemExit('no scripts')
checked=0
for i,js in enumerate(scripts):
    if not js.strip():continue
    p=Path(f'/tmp/v333_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
    checked+=1
if checked<1: raise SystemExit('no scripts checked')
print(f'built v3.33 time-sliced exact-state route search; JS checked={checked}')
