from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_33.html')
DST=Path('Nangman_Integrated_Simulator_v3_34.html')
if not SRC.exists(): raise SystemExit('v3.33 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.33','v3.34').replace('v3_33','v3_34')
text=re.sub(r'(?<![0-9])3\.33(?![0-9])','3.34',text)
text=re.sub(r'<script id="stable-root-url-v333">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v334">try{if(/Nangman_Integrated_Simulator_v3_34\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

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
if start<0 or end<0: raise SystemExit('v3.33 engine block missing')
old=route[start:end]
if 'time-sliced exact-state route search' not in old or 'function tryWash(' not in old:
    raise SystemExit('unexpected v3.33 engine')

new=r''' outer:{
 // v3.34 target-seed-directed daomai/kamek search.
 // First resolve the clicked Born seed to its raw RNG position, then search only states whose unlocked-pity seed approaches it.
 const requestedSkip=Math.max(0,targetShift);
 const baselineCost=requestedSkip>0?requestedSkip*4:0;
 const SLICE_MS=10,UI_MS=220;
 const seedToRaw=new Map();
 for(const [rn,x] of rawByNo.entries()){
   if(x&&Number.isFinite(+x.seedAfter))seedToRaw.set(+x.seedAfter,+rn);
   if(x&&Number.isFinite(+x.seedBefore)&&!seedToRaw.has(+x.seedBefore))seedToRaw.set(+x.seedBefore,+rn-1);
 }
 const targetRaw=seedToRaw.has(+targetSeed)?seedToRaw.get(+targetSeed):null;

 function stateSig(st){
   if(typeof stateKeyRoute==='function')return stateKeyRoute(st);
   return [st.seed,st.born_talent_rc||0,st.luck_seed||0,st.luck_seed_inited?1:0,st.tal_lucky,(st.talents||[]).map(x=>+x.id).join(',')].join('|');
 }
 function heapCmp(a,b){return a.cost-b.cost||a.need-b.need||a.stall-b.stall||b.startIndex-a.startIndex||a.depth-b.depth}
 function heapPush(h,x){h.push(x);let i=h.length-1;while(i>0){let p=(i-1)>>1;if(heapCmp(h[p],x)<=0)break;h[i]=h[p];i=p}h[i]=x}
 function heapPop(h){if(!h.length)return null;const root=h[0],last=h.pop();if(!h.length)return root;let i=0;while(true){let l=i*2+1,r=l+1;if(l>=h.length)break;let c=(r<h.length&&heapCmp(h[r],h[l])<0)?r:l;if(heapCmp(last,h[c])<=0)break;h[i]=h[c];i=c}h[i]=last;return root}
 function unlockedCopy(st){const x=dc(st);x.talents=(x.talents||[]).map(t=>({...t,locked:false}));return x}
 function tryWash(st,lockIds){
   let x=unlockedCopy(st);const set=new Set(lockIds||[]);x.talents=(x.talents||[]).map(t=>({...t,locked:set.has(+t.id)}));
   let tr;try{tr=washOnce(x)}catch(_){return null}
   if(tr.result?.got_gold||tr.result?.was_pity)return null;
   return {state:unlockedCopy(tr.state),result:tr.result,before:x};
 }
 function pityInfo(st){
   let p=null;try{p=probePitySeed(unlockedCopy(st))}catch(_){return null}
   if(!p)return null;
   const r=seedToRaw.has(+p.seed)?seedToRaw.get(+p.seed):null;
   return {probe:p,raw:r};
 }
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

 // Resolve the actual raw distance from the default unlocked pity to the clicked target seed.
 let baseInfo=null;
 for(let i=pages.length-1;i>=0&&!baseInfo;i--)baseInfo=pityInfo(pages[i]);
 const baseRaw=baseInfo&&baseInfo.raw!=null?baseInfo.raw:null;
 const derivedNeed=(targetRaw!=null&&baseRaw!=null)?(+targetRaw-+baseRaw):requestedSkip;
 const goalNeed=Math.max(0,Number.isFinite(derivedNeed)?derivedNeed:requestedSkip);
 const maxExtraCost=Math.max(24,goalNeed*4+24);
 const maxNodes=Math.max(2500,Math.min(14000,2500+goalNeed*450));
 const needSlack=Math.max(2,Math.min(6,Math.ceil(goalNeed/6)));

 const heap=[],seen=new Map();
 for(let i=0;i<pages.length;i++){
   const st=unlockedCopy(pages[i]),pi=pityInfo(st);if(!pi)continue;
   const need=(targetRaw!=null&&pi.raw!=null)?(+targetRaw-+pi.raw):goalNeed;
   if(need<0||need>goalNeed+needSlack)continue;
   const n={st,cost:0,need,stall:0,startIndex:i,depth:0,parent:null,action:null,startPg:pages[i],probe:pi.probe,hasLock:false};
   const k=stateSig(st),ov=seen.get(k);if(!ov||i>ov.startIndex){seen.set(k,{cost:0,need,startIndex:i});heapPush(heap,n)}
 }
 let expanded=0,sliceStart=nowMs(),lastUi=0;
 while(heap.length&&expanded<maxNodes){
   const cur=heapPop(heap);expanded++;
   const sig=stateSig(cur.st),sv=seen.get(sig);
   if(sv&&(cur.cost>sv.cost||(cur.cost===sv.cost&&cur.need>sv.need)))continue;

   if(cur.need===0&&cur.hasLock&&cur.probe&&+cur.probe.seed===+targetSeed){
     probes++;
     const actions=collectActions(cur),eps=groupedEpisodes(actions,cur.startPg),firstLock=actions.find(a=>a.kind!=='free');
     const first=eps[0]?.episode||{pg:cur.startPg,lockIds:firstLock?.lockIds||[],hold:1};
     const rawSlots=dc(cur.startPg.__daoRawSlots||[]),lockRawSlots=rawSlots.filter(x=>(first.lockIds||[]).includes(+x.id));
     best={cost:cur.cost,dist:pages.length-1-cur.startIndex,hold:first.hold||1,lockIds:(first.lockIds||[]).slice(),path:eps[0]?.steps||[],probe:cur.probe,checked:expanded,probes,win:pages.length,
       rawStart:+cur.startPg.__daoRawStart,rawEnd:+cur.startPg.__daoRawEnd,rawSlots,lockRawSlots,trace:null,firstFree:null,label:'목표 seed 역산 · 실제 washOnce 검증',
       estimatedSkips:goalNeed,baselineCost:goalNeed*4,multiEpisodes:eps,episodeCount:eps.length,expandedNodes:expanded,targetRaw,baseRaw};
     break;
   }
   if(cur.cost>maxExtraCost)continue;

   const visible=(cur.st.talents||[]).map(t=>+t.id),ops=[{kind:'free',ids:[]}];
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
 }
 }
'''
route=route[:start]+new+route[end:]
for tok in ['v3.34 target-seed-directed','const seedToRaw=new Map()','const derivedNeed=','목표 seed 역산 탐색 중','need<0||need>goalNeed+needSlack','maxNodes=Math.max(2500']:
    if tok not in route: raise SystemExit('v3.34 token missing '+tok)
if '120000' in new or 'time-sliced exact-state route search' in new: raise SystemExit('old broad search remains')

out=text[:a]+route+text[b:]
DST.write_text(out,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.34','file':'Nangman_Integrated_Simulator_v3_34.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.34',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.34</title>' not in out[:10000]: raise SystemExit('title mismatch')
scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',out,re.I|re.S)
if not scripts: raise SystemExit('no scripts')
checked=0
for i,js in enumerate(scripts):
    if not js.strip():continue
    p=Path(f'/tmp/v334_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
    checked+=1
if checked<1: raise SystemExit('no scripts checked')
print(f'built v3.34 target-seed-directed daomai search; JS checked={checked}')
