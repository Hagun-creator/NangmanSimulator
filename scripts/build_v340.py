from pathlib import Path
import re,base64,subprocess,json
SRC=Path('Nangman_Integrated_Simulator_v3_37.html')
DST=Path('Nangman_Integrated_Simulator_v3_40.html')
if not SRC.exists(): raise SystemExit('v3.37 source missing')
text=SRC.read_text(encoding='utf-8')
text=text.replace('v3.37','v3.40').replace('v3_37','v3_40')
text=re.sub(r'(?<![0-9])3\\.37(?![0-9])','3.39',text)
text=re.sub(r'<script id="stable-root-url-v338">.*?</script>\\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v340">try{if(/Nangman_Integrated_Simulator_v3_40\\\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\\n'''+text[he:]
m=re.search(r'const EQUIPMENT_HTML_B64="([A-Za-z0-9+/=]+)";',text)
if not m: raise SystemExit('equipment iframe payload missing')
h=base64.b64decode(m.group(1)).decode('utf-8')
old='<button data-v="find">장비 찾기</button><button data-v="region">지역별 제작 목록</button>'
new='<button data-v="find">장비 찾기</button><button data-v="auto">자동 시뮬레이션</button><button data-v="region">지역별 제작 목록</button>'
if old not in h: raise SystemExit('equipment nav anchor missing')
h=h.replace(old,new,1)
old="else if(v==='jianwang')paintJianwang(m)"
new="else if(v==='jianwang')paintJianwang(m);else if(v==='auto')paintAutoEquip339(m)"
if old not in h: raise SystemExit('equipment open anchor missing')
h=h.replace(old,new,1)
css=r'''<style id="auto-equip-v340-css">
#rk218 .auto339-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
#rk218 .auto339-box{border:1px solid #d9dee5;border-radius:9px;background:#fff;padding:10px}
#rk218 .auto339-box b{display:block;margin-bottom:6px}
#rk218 .auto339-row{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
#rk218 .auto339-results{display:grid;gap:9px;margin-top:12px}
#rk218 .auto339-result{border:1px solid #d9dee5;border-radius:9px;background:#fff;padding:11px;cursor:pointer}
#rk218 .auto339-result:hover{border-color:#7c8fb5;background:#f8fbff}
#rk218 .auto339-title{display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap}
#rk218 .auto339-props{font-size:12px;line-height:1.6;margin-top:6px}
#rk218 .auto339-refine{margin-top:7px;padding-top:7px;border-top:1px dashed #d9dee5;font-size:12px;line-height:1.55}
#rk218 .auto339-progress{margin:8px 0;font-size:12px;color:#56606b}
@media(max-width:760px){#rk218 .auto339-grid{grid-template-columns:1fr}}
</style>'''
h=h.replace('</head>',css+'\n</head>',1)
js=r'''
/* auto-equip-v340 */
(function(){
 const A={lv:90,equipId:0,npcId:0,prop:'',specialId:0,count:100,mud:500,scan:600,results:[]};
 const $=s=>document.querySelector(s), esc339=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
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
 function resultCard339(o,i){
   const z=o.make,e=o.equip,cfg=EQUIP_DATA.equipment[String(e.id)]||{},reg=(z.region||[]).map(x=>`${propLabel218(x.prop)} +${formatPropValue(x.prop,x.value)}`).join(' · ')||'없음',sp=(z.special||[]).map(x=>`${propLabel218(x.prop)} +${formatPropValue(x.prop,x.value)}`).join(' · ')||'없음';
   const before=propTotal339(o.base,A.prop),after=propTotal339(e,A.prop),grade=rkRefineGrade256(e,A.prop);const ref=o.xl?`정련 후 <b>${esc339(propLabel218(A.prop))} ${esc339(formatPropValue(A.prop,after))}</b> · ${grade.label} ${grade.rounded}% · 연금니 기준 ${o.xl.best.mud}`:'정련 대상 아님/경로 없음';
   return `<div class="auto339-result" data-a339="${i}"><div class="auto339-title"><div><b>${esc339(e.name||ename(cfg))}</b><span class="meta"> · 제작 #${z.index} · ${esc339(routeDisplayName(o.rt))}</span></div><div>${qualityHtml226(z.color)}</div></div><div class="auto339-props"><b>제작 옵션</b> ${(z.exts||[]).map(x=>`${esc339(propLabel218(x.prop))} +${esc339(formatPropValue(x.prop,x.value))}`).join(' · ')||'없음'}<br><b>지역</b> ${esc339(reg)}<br><b>재료</b> ${esc339(sp)}</div><div class="auto339-refine"><b>목표 ${esc339(propLabel218(A.prop))}</b> 제작 ${esc339(formatPropValue(A.prop,before))} → ${ref}</div></div>`
 }
 async function run339(){
   if(!ensureRngLoaded()){const p=$('#a339prog');if(p)p.textContent='세이브 데이터를 먼저 불러와 주세요.';return}
   const cfg=selectedCfg339(),routes=routeList339();if(!cfg||!routes.length||!A.prop)return;
   const prog=$('#a339prog'),res=$('#a339res');A.results=[];res.innerHTML='';let done=0;
   for(const rt of routes){
     const paper=rt.p?.paper||EQUIP_DATA.papers[String(rt.p?.selectId)]||{},req={equip_id:Number(cfg.id),select_id:Number(rt.p?.selectId||paper.id),npc_id:Number(rt.npc.id),min_color:Number(paper.min_color||1),max_color:Number(paper.max_color||4),special_id:Number(A.specialId||0)};
     const pre=rkMakePreviewNative233(req,A.count);for(const z of (pre.items||[])){
       done++;if(prog&&done%10===0)prog.textContent=`제작 결과 분석 중 ${done}/${routes.length*A.count}`;
       let base=virtualFromMake(z,req.select_id),xl=null,finalEq=base;
       if(Number(z.color)>=4){base=rkAscendForRefine218(base);xl=makeFlags339(base,A.prop);if(xl)finalEq=xl.equip}
       const obj={equip:finalEq,base,make:z,rt,recipe:{lvs:[A.lv],parts:[Number(cfg.type)],equipIds:[Number(cfg.id)],colors:[Number(z.color)],reqs:[{where:'exts',prop:A.prop,min:0,label:propLabel218(A.prop)}]},xl,searchBudget264:{mud:A.mud,mj:20},_rkXlFlags:xl?.flags||[],_rkXlN:Math.max(100,xl?.flags?.length||0)};
       A.results.push(obj);
       if(done%20===0)await new Promise(r=>setTimeout(r,0));
     }
   }
   A.results.sort((a,b)=>propTotal339(b.equip,A.prop)-propTotal339(a.equip,A.prop)||Number(b.make.color)-Number(a.make.color)||Number(a.make.index)-Number(b.make.index));
   const top=A.results.slice(0,80);res.innerHTML=top.map(resultCard339).join('')||'<p class="note218">결과가 없습니다.</p>';if(prog)prog.textContent=`완료 · ${A.results.length}개 계산 · 상위 ${top.length}개 표시`;
   res.querySelectorAll('[data-a339]').forEach(el=>el.onclick=()=>{const o=top[Number(el.dataset.a339)];if(o)showDetailTop233(o,'auto','xl')});
 }
 window.paintAutoEquip339=function(m){
   m.innerHTML=`<details class="box218" open><summary>장비 자동 시뮬레이션</summary><div class="bbody"><div class="auto339-grid"><div class="auto339-box"><b>장비</b><div class="auto339-row"><select class="rinput" id="a339lv"></select><select class="rinput" id="a339equip"></select></div></div><div class="auto339-box"><b>지역</b><select class="rinput" id="a339npc"></select></div><div class="auto339-box"><b>목표 옵션</b><select class="rinput" id="a339prop"></select></div><div class="auto339-box"><b>최초 특수재료</b><select class="rinput" id="a339mat"></select></div></div><div class="budget" style="margin-top:10px"><label><b>제작</b><input class="num218" id="a339count" type="number" min="1" max="1000" value="${A.count}"> 회</label><label><b>정련</b><input class="num218" id="a339mud" type="number" min="0" max="2500" value="${A.mud}"> 연금니</label><label><b>정련 탐색</b><input class="num218" id="a339scan" type="number" min="50" max="3000" value="${A.scan}"> 회</label></div><button class="rbtn primary" id="a339go">자동 시뮬레이션 시작</button><div class="auto339-progress" id="a339prog">조건을 선택하고 시작하세요.</div></div></details><div id="a339res" class="auto339-results"></div>`;
   refresh339();
   $('#a339lv').onchange=e=>{A.lv=Number(e.target.value);A.equipId=0;refresh339()};$('#a339equip').onchange=e=>{A.equipId=Number(e.target.value);A.npcId=0;A.prop='';A.specialId=0;refresh339()};$('#a339npc').onchange=e=>A.npcId=Number(e.target.value);$('#a339prop').onchange=e=>A.prop=e.target.value;$('#a339mat').onchange=e=>A.specialId=Number(e.target.value);$('#a339count').onchange=e=>A.count=Math.max(1,Math.min(1000,Number(e.target.value)||100));$('#a339mud').onchange=e=>A.mud=Math.max(0,Math.min(2500,Number(e.target.value)||0));$('#a339scan').onchange=e=>A.scan=Math.max(50,Math.min(3000,Number(e.target.value)||600));$('#a339go').onclick=run339;
 };
})();
'''
marker='window.rk218Open=open;window.addEventListener(\'load\',mount);'
if marker not in h: raise SystemExit('equipment injection marker missing')
h=h.replace(marker,js+'\n'+marker,1)
for tok in ['data-v="auto"','paintAutoEquip339','자동 시뮬레이션 시작','rkXlCurve237',"showDetailTop233(o,'auto','xl')"]:
    if tok not in h: raise SystemExit('v3.40 iframe token missing: '+tok)
iframe_scripts=re.findall(r'<script\\b[^>]*>(.*?)</script>',h,re.I|re.S)
for i,js0 in enumerate(iframe_scripts):
    if not js0.strip(): continue
    p=Path(f'/tmp/v340_iframe_{i}.js');p.write_text(js0,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
enc=base64.b64encode(h.encode('utf-8')).decode('ascii')
text=text[:m.start(1)]+enc+text[m.end(1):]
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.40','file':'Nangman_Integrated_Simulator_v3_40.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');rs=r.read_text(encoding='utf-8');rs=re.sub(r'현재 사이트 버전:\\s*v?[0-9.]+','현재 사이트 버전: v3.40',rs);r.write_text(rs,encoding='utf-8')
if '<title>낭만강호 시뮬레이터 v3.40</title>' not in text[:12000]: raise SystemExit('parent title mismatch')
parent_scripts=re.findall(r'<script\\b[^>]*>(.*?)</script>',text,re.I|re.S)
checked=0
for i,js0 in enumerate(parent_scripts):
    if not js0.strip(): continue
    p=Path(f'/tmp/v340_parent_{i}.js');p.write_text(js0,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
    checked+=1
print(f'built v3.40 equipment auto simulation; parent JS checked={checked}, iframe JS checked={len(iframe_scripts)}')
