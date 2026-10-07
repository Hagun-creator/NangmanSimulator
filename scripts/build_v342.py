from pathlib import Path
import re,base64,subprocess,json

SRC=Path('Nangman_Integrated_Simulator_v3_41.html')
DST=Path('Nangman_Integrated_Simulator_v3_42.html')
if not SRC.exists(): raise SystemExit('v3.41 source missing')
text=SRC.read_text(encoding='utf-8')
if '</head>' not in text.lower(): raise SystemExit('v3.41 source is not normal HTML')
text=text.replace('v3.41','v3.42').replace('v3_41','v3_42')
text=re.sub(r'(?<![0-9])3\.40(?![0-9])','3.41',text)
text=re.sub(r'<script id="stable-root-url-v341">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
text=text[:he]+'''<script id="stable-root-url-v342">try{if(/Nangman_Integrated_Simulator_v3_42\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

m=re.search(r'const EQUIPMENT_HTML_B64="([A-Za-z0-9+/=]+)";',text)
if not m: raise SystemExit('equipment iframe payload missing')
h=base64.b64decode(m.group(1)).decode('utf-8')

css='''<style id="auto-equip-v342-css">
#rk218 .auto339-grade{display:inline-flex;align-items:center;gap:4px;margin-left:6px}
#rk218 .auto339-inline{display:flex;gap:5px;flex-wrap:wrap;align-items:center;margin-top:6px}
#rk218 .auto339-region{display:inline-flex;padding:2px 7px;border:1px solid #d8a7e6;border-radius:999px;background:#fff2ff;color:#9a2db8;font-weight:800}
#rk218 .auto339-material{display:inline-flex;padding:2px 7px;border:1px solid #e6c07b;border-radius:999px;background:#fff8e8;color:#9a6700;font-weight:800}
#rk218 .auto339-mang{display:inline-flex;padding:2px 7px;border:1px solid #84c9b3;border-radius:999px;background:#effbf7;color:#177154;font-weight:800}\n#rk218 .auto342-cardgrid{display:grid;grid-template-columns:minmax(0,1fr) minmax(300px,380px);gap:14px;align-items:start}\n#rk218 .auto342-slots{border-left:1px solid #e1e5e9;padding-left:12px;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}\n#rk218 .auto342-slot{border:1px solid #dde3e8;border-radius:7px;background:#f8fafc;padding:7px 9px;font-size:12px}\n#rk218 .auto342-slot b{display:block;font-size:10px;color:#6b7280;margin-bottom:2px}\n#rk218 .auto342-total{grid-column:1/-1;border-color:#b9c7d8;background:#f0f6fc;font-weight:800}\n@media(max-width:760px){#rk218 .auto342-cardgrid{grid-template-columns:1fr}#rk218 .auto342-slots{border-left:0;border-top:1px solid #e1e5e9;padding-left:0;padding-top:10px}}
</style>\n'''
h=h.replace('</head>',css+'</head>',1)

start=h.find('/* auto-equip-v341 */')
end=h.find('window.rk218Open=open;',start)
if start<0 or end<0: raise SystemExit('auto block boundary missing')

auto_js=r'''/* auto-equip-v342 */
(function(){
 const A={lv:90,equipId:0,npcId:0,prop:'',specialId:0,count:100,mud:500,scan:600,mj:20,results:[],top:[],parentScroll:0};
 const $=s=>document.querySelector(s), esc339=s=>String(s??'').replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]));
 function configs339(){return Object.values(EQUIP_DATA.equipment||{}).filter(e=>[90,100].includes(Number(e.lv))&&craftRoutesForEquip218(Number(e.id)).length&&!isUniqueCraft(Number(e.id))).sort((a,b)=>Number(a.type)-Number(b.type)||String(ename(a)).localeCompare(String(ename(b)),'ko'))}
 function selectedCfg339(){return EQUIP_DATA.equipment?.[String(A.equipId)]||null}
 function routeList339(){const c=selectedCfg339();if(!c)return[];return craftRoutesForEquip218(Number(c.id)).filter(rt=>!A.npcId||Number(rt?.npc?.id)===Number(A.npcId))}
 function propChoices339(){const c=selectedCfg339();if(!c)return[];const out=[];for(const [p,v] of Object.entries(c.exts||{})){if(Array.isArray(v)&&Number(v[0])>0&&KO_PROP_EXACT[p])out.push(p)}return out.sort((a,b)=>propLabel218(a).localeCompare(propLabel218(b),'ko'))}
 function matChoices339(){const c=selectedCfg339();return c?specialMaterialsForEquip(c):[]}
 function fill339(id,items,value,label){const s=$(id);if(!s)return;s.innerHTML='';for(const it of items){const o=new Option(label(it),String(it.value));s.add(o)}if(items.some(x=>String(x.value)===String(value)))s.value=String(value)}
 function refresh339(){
   fill339('#a339lv',[{value:90},{value:100}],A.lv,x=>x.value+'급');
   const eqs=configs339().filter(e=>Number(e.lv)===A.lv).map(e=>({value:e.id,e}));if(!eqs.some(x=>Number(x.value)===Number(A.equipId)))A.equipId=Number(eqs[0]?.value||0);
   fill339('#a339equip',eqs,A.equipId,x=>`${tname(x.e.type)} · ${ename(x.e)}`);
   const routes=craftRoutesForEquip218(A.equipId),npcs=[];const seen=new Set();for(const r of routes){const id=Number(r?.npc?.id||0);if(!id||seen.has(id))continue;seen.add(id);npcs.push({value:id,r})}npcs.unshift({value:0,r:null});if(!npcs.some(x=>Number(x.value)===Number(A.npcId)))A.npcId=0;
   fill339('#a339npc',npcs,A.npcId,x=>x.value===0?'전체 지역':routeDisplayName(x.r));
   const ps=propChoices339().map(p=>({value:p,p}));if(!ps.some(x=>x.value===A.prop))A.prop=ps[0]?.value||'';fill339('#a339prop',ps,A.prop,x=>propLabel218(x.p));
   const mats=[{value:0,m:null},...matChoices339().map(m=>({value:m.id,m}))];if(!mats.some(x=>Number(x.value)===Number(A.specialId)))A.specialId=0;fill339('#a339mat',mats,A.specialId,x=>x.value===0?'재료 없음':x.m.name);
 }
 function makeFlags339(base,prop){
   const curve=rkXlCurve237(base,prop,A.mud,A.scan);if(!curve||!curve.front?.length)return null;
   const pool=curve.front.filter(x=>x.steps?.length);if(!pool.length)return null;
   pool.sort((a,b)=>b.total-a.total||a.mud-b.mud);const best=pool[0],max=Math.max(0,...best.steps.map(x=>Number(x.at)||0));if(!max)return null;
   const flags=Array(max).fill(false);for(const s of best.steps){const i=Number(s.at)-1;if(i>=0)flags[i]=true}
   try{const p=rkXilianPlanNative233(toWasmEquip(base),flags);return{best,flags,plan:p,equip:p.equip||base}}catch(_){return null}
 }
 function propTotal339(e,p){return (e?.exts||[]).filter(x=>x.prop===p).reduce((s,x)=>s+Number(x.value||0),0)}
 function gradeBadge339(e,p){const g=rkRefineGrade256(e,p);return g.max>0?`<span class="rk-grade256 is-${g.key}"><b>${esc339(g.label)}</b><small>${g.rounded}%</small></span>`:''}
 function layerChip339(kind,label){const cls=kind==='region'?'auto339-region':kind==='material'?'auto339-material':'auto339-mang';return `<span class="${cls}">${esc339(label)}</span>`}
 function bestMang339(base){
   if(!A.specialId)return null;
   const mat=EQUIP_DATA.special?.[String(A.specialId)],info=rkMjLevelInfo273(base);if(!mat)return null;
   const allowed=specialMaterialsForEquip(base).some(x=>Number(x.id)===Number(A.specialId));if(!allowed)return null;
   let seq=[];try{seq=rkMjSequence273(base,mat,A.mj)}catch(_){return null}
   let best=null;
   for(const z of seq){const value=info.canAscend?Number(z.v100??z.value):Number(z.value),score=Number(z.pct||0)*1000000+Math.abs(value||0);
     if(!best||score>best.score){const ne=clone(base);ne.specials=[{prop:z.prop,value}];best={score,equip:ne,base:clone(base),mat,roll:{...z,value},seq,attempts:Number(z.index||z.at||0),stones:Number(z.stones||0),fromLv:info.fromLv,toLv:info.toLv,optimized90to100:info.canAscend}}
   }
   return best
 }
 function resultCard339(o,i){
   const z=o.make,e=o.equip,cfg=EQUIP_DATA.equipment[String(e.id)]||{};
   const reg=(z.region||[]).map(x=>`${propLabel218(x.prop)} +${formatPropValue(x.prop,x.value)}`),sp=(z.special||[]).map(x=>`${propLabel218(x.prop)} +${formatPropValue(x.prop,x.value)}`);
   const grade=rkRefineGrade256(e,A.prop),exts=e?.exts||[];
   const vals=[0,1,2].map(i=>exts[i]&&exts[i].prop===A.prop?formatPropValue(A.prop,exts[i].value):'—');
   const total=exts.filter(x=>x.prop===A.prop).reduce((a,x)=>a+Number(x.value||0),0);
   const regionInline=reg.map(x=>layerChip339('region','지역 '+x)).join(''),materialInline=sp.map(x=>layerChip339('material','재료 '+x)).join('');
   const mj=o.mj?layerChip339('mang',`망정 #${o.mj.roll?.index||o.mj.attempts} ${o.mj.mat?.name||''} · ${propLabel218(o.mj.roll?.prop)} +${formatPropValue(o.mj.roll?.prop,o.mj.roll?.value)}`):layerChip339('mang',A.specialId?`망정 ${A.mj}회 · 선택 재료 결과 없음`:'망정 · 재료 미선택');
   return `<div class="auto339-result" data-a339="${i}"><div class="auto342-cardgrid"><div><div class="auto339-title"><div><b>${esc339(e.name||ename(cfg))}</b><span class="meta"> · 제작 #${z.index} · ${esc339(routeDisplayName(o.rt))}</span></div><div>${qualityHtml226(z.color)} <span class="auto339-grade">${gradeBadge339(e,A.prop)}</span></div></div><div class="auto339-props"><b>제작 옵션</b> ${(z.exts||[]).map(x=>`${esc339(propLabel218(x.prop))} +${esc339(formatPropValue(x.prop,x.value))}`).join(' · ')||'없음'}</div><div class="auto339-inline">${regionInline}${materialInline}${mj}</div></div><aside class="auto342-slots"><div class="auto342-slot"><b>1옵션</b>${esc339(vals[0])}</div><div class="auto342-slot"><b>2옵션</b>${esc339(vals[1])}</div><div class="auto342-slot"><b>3옵션</b>${esc339(vals[2])}</div><div class="auto342-slot auto342-total"><b>${esc339(propLabel218(A.prop))} 총합</b>${esc339(formatPropValue(A.prop,total))} · ${gradeBadge339(e,A.prop)}</div></aside></div></div>`
 }
 function renderAutoResults339(){
   const res=$('#a339res');if(!res)return;const top=A.results.slice(0,80);A.top=top;res.innerHTML=top.map(resultCard339).join('')||'<p class="note218">결과가 없습니다.</p>';
   res.querySelectorAll('[data-a339]').forEach(el=>el.onclick=()=>{const o=top[Number(el.dataset.a339)];if(!o)return;try{A.parentScroll=(window.parent&&window.parent!==window)?window.parent.scrollY:window.scrollY}catch(_){A.parentScroll=0}showDetailTop233(o,'auto','xl')});
 }
 async function run339(){
   if(!ensureRngLoaded()){const p=$('#a339prog');if(p)p.textContent='세이브 데이터를 먼저 불러와 주세요.';return}
   const cfg=selectedCfg339(),routes=routeList339();if(!cfg||!routes.length||!A.prop)return;
   const prog=$('#a339prog'),res=$('#a339res');A.results=[];res.innerHTML='';let done=0;
   for(const rt of routes){
     const paper=rt.p?.paper||EQUIP_DATA.papers[String(rt.p?.selectId)]||{},req={equip_id:Number(cfg.id),select_id:Number(rt.p?.selectId||paper.id),npc_id:Number(rt.npc.id),min_color:Number(paper.min_color||1),max_color:Number(paper.max_color||4),special_id:Number(A.specialId||0)};
     const pre=rkMakePreviewNative233(req,A.count);for(const z of (pre.items||[])){
       done++;if(prog&&done%10===0)prog.textContent=`제작·정련·망정 분석 중 ${done}/${routes.length*A.count}`;
       let base=virtualFromMake(z,req.select_id),xl=null,finalEq=base,mj=null;
       if(Number(z.color)>=4){base=rkAscendForRefine218(base);xl=makeFlags339(base,A.prop);if(xl)finalEq=xl.equip}
       mj=bestMang339(finalEq);if(mj)finalEq=mj.equip;
       const obj={equip:finalEq,base,make:z,rt,recipe:{lvs:[A.lv],parts:[Number(cfg.type)],equipIds:[Number(cfg.id)],colors:[Number(z.color)],reqs:[{where:'exts',prop:A.prop,min:0,label:propLabel218(A.prop)}]},xl,mj,searchBudget264:{mud:A.mud,mj:A.mj},_rkXlFlags:xl?.flags||[],_rkXlN:Math.max(100,xl?.flags?.length||0),_rkMjN:Math.max(20,A.mj)};
       A.results.push(obj);if(done%10===0)await new Promise(r=>setTimeout(r,0));
     }
   }
   A.results.sort((a,b)=>propTotal339(b.equip,A.prop)-propTotal339(a.equip,A.prop)||Number(b.make.color)-Number(a.make.color)||Number(a.make.index)-Number(b.make.index));
   renderAutoResults339();if(prog)prog.textContent=`완료 · ${A.results.length}개 계산 · 상위 ${Math.min(80,A.results.length)}개 표시 · 선택 재료 망정 ${A.mj}회 자동 검색`;
 }
 window.paintAutoEquip339=function(m){
   m.innerHTML=`<details class="box218" open><summary>장비 자동 시뮬레이션</summary><div class="bbody"><div class="auto339-grid"><div class="auto339-box"><b>장비</b><div class="auto339-row"><select class="rinput" id="a339lv"></select><select class="rinput" id="a339equip"></select></div></div><div class="auto339-box"><b>지역</b><select class="rinput" id="a339npc"></select></div><div class="auto339-box"><b>목표 옵션</b><select class="rinput" id="a339prop"></select></div><div class="auto339-box"><b>최초 특수재료</b><select class="rinput" id="a339mat"></select></div></div><div class="budget" style="margin-top:10px"><label><b>제작</b><input class="num218" id="a339count" type="number" min="1" max="1000" value="${A.count}"> 회</label><label><b>정련</b><input class="num218" id="a339mud" type="number" min="0" max="2500" value="${A.mud}"> 연금니</label><label><b>정련 탐색</b><input class="num218" id="a339scan" type="number" min="50" max="3000" value="${A.scan}"> 회</label><label><b>망정</b><input class="num218" id="a339mj" type="number" min="1" max="100" value="${A.mj}"> 회</label></div><button class="rbtn primary" id="a339go">자동 시뮬레이션 시작</button><div class="auto339-progress" id="a339prog">조건을 선택하고 시작하세요.</div></div></details><div id="a339res" class="auto339-results"></div>`;
   refresh339();
   $('#a339lv').onchange=e=>{A.lv=Number(e.target.value);A.equipId=0;refresh339()};$('#a339equip').onchange=e=>{A.equipId=Number(e.target.value);A.npcId=0;A.prop='';A.specialId=0;refresh339()};$('#a339npc').onchange=e=>A.npcId=Number(e.target.value);$('#a339prop').onchange=e=>A.prop=e.target.value;$('#a339mat').onchange=e=>A.specialId=Number(e.target.value);$('#a339count').onchange=e=>A.count=Math.max(1,Math.min(1000,Number(e.target.value)||100));$('#a339mud').onchange=e=>A.mud=Math.max(0,Math.min(2500,Number(e.target.value)||0));$('#a339scan').onchange=e=>A.scan=Math.max(50,Math.min(3000,Number(e.target.value)||600));$('#a339mj').onchange=e=>A.mj=Math.max(1,Math.min(100,Number(e.target.value)||20));$('#a339go').onclick=run339;
   if(A.results.length){renderAutoResults339();const p=$('#a339prog');if(p)p.textContent=`이전 자동 시뮬레이션 결과 · ${A.results.length}개 · 망정 ${A.mj}회`;requestAnimationFrame(()=>{try{if(window.parent&&window.parent!==window)window.parent.scrollTo(0,A.parentScroll||0);else window.scrollTo(0,A.parentScroll||0)}catch(_){}})}
 };
})();

'''

h=h[:start]+auto_js+h[end:]
for tok in ['auto-equip-v342','gradeBadge339','bestMang339','renderAutoResults339','auto339-region','auto339-material','auto339-mang','auto342-slots','id="a339mj"','선택 재료 망정 ${A.mj}회 자동 검색']:
    if tok not in h: raise SystemExit('v3.42 feature missing: '+tok)

iframe_scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',h,re.I|re.S)
if not iframe_scripts: raise SystemExit('no iframe scripts')
ic=0
for i,js in enumerate(iframe_scripts):
    if not js.strip(): continue
    p=Path(f'/tmp/v342_iframe_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit('iframe JS error\n'+cp.stderr[:4000])
    ic+=1
enc=base64.b64encode(h.encode('utf-8')).decode('ascii')
text=text[:m.start(1)]+enc+text[m.end(1):]

parent_scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)
pc=0
for i,js in enumerate(parent_scripts):
    if not js.strip(): continue
    p=Path(f'/tmp/v342_parent_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit('parent JS error\n'+cp.stderr[:4000])
    pc+=1
if '<title>낭만강호 시뮬레이터 v3.42</title>' not in text[:12000]: raise SystemExit('title mismatch')
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.42','file':'Nangman_Integrated_Simulator_v3_42.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');rs=r.read_text(encoding='utf-8');rs=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.42',rs);r.write_text(rs,encoding='utf-8')
print(f'built v3.42 auto selected-material mang + slot breakdown; iframe={ic}, parent={pc}')