from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_13.html')
DST=Path('Nangman_Integrated_Simulator_v3_14.html')
if not SRC.exists(): raise SystemExit('v3.13 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.13','v3.14').replace('v3_13','v3_14')
text=re.sub(r'(?<![0-9])3\.13(?![0-9])','3.14',text)
text=re.sub(r'<script id="stable-root-url-v313">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v314">try{if(/Nangman_Integrated_Simulator_v3_14\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Replace route search only: target Born seed is sufficient; do not re-check pity/exchange 1..15.
a=text.find('async function showDaoPullRouteV290(')
b=text.find('\nasync function showDaoExchangeWindowV288(){',a)
if a<0 or b<0: raise SystemExit('route boundary missing')
route=text[a:b]
route=re.sub(r"\n const targetPity=row\.pity\?\.name\|\|targetName\|\|'';\n const targetDraws=\(row\.draws\|\|\[\]\)\.slice\(0,15\)\.map\(x=>x\.name\);",'',route,count=1)
route=route.replace('실제 washOnce 상태만 탐색하며 seed·천장·교체 1~15가 모두 일치해야 성공합니다.','실제 washOnce 상태만 탐색하며 목표 Born seed에 정확히 도달하면 성공합니다.')
old_goal=""" function pityName(st){const t=(st.talents||[]).find(t=>+BYID.get(+t.id)?.weight===4);return t?nm(t.id):''}
 function goal(before,after,tr){
   if(!tr.result.was_pity)return false;
   if(+before.seed!==targetSeed)return false;
   if(pityName(after)!==targetPity)return false;
   const got=exchangeSequence(+after.luck_seed,after,15).map(x=>x.name);
   if(got.length<targetDraws.length)return false;
   for(let i=0;i<targetDraws.length;i++)if(got[i]!==targetDraws[i])return false;
   return true;
 }
"""
new_goal=""" function pityName(st){const t=(st.talents||[]).find(t=>+BYID.get(+t.id)?.weight===4);return t?nm(t.id):''}
 function goal(before,after,tr){
   return !!tr.result.was_pity && +before.seed===targetSeed;
 }
"""
if old_goal not in route: raise SystemExit('goal block missing')
route=route.replace(old_goal,new_goal,1)
start=route.find(' const heap=[],seen=new Map();')
end=route.find('\n if(!best){',start)
if start<0 or end<0: raise SystemExit('heap block missing')
new_search=r''' const pages=[];
 let scan=normalize(base),scanGuard=3000;
 while(scanGuard-->0){
   const tr=washOnce(scan);scan=normalize(tr.state);
   if(tr.result.got_gold)break;
   pages.push(dc(scan));
 }
 if(scanGuard<=0){box.innerHTML='<div class="warn">기본 천장 이전 상태 재현 한도를 초과했습니다.</div>';return}

 let best=null,checked=0;
 const MAX_NEAR_PAGES=Math.min(120,pages.length),maxHold=24;
 // Check closest-to-pity pages first; stop after the first distance band that has a valid seed route.
 for(let dist=0;dist<MAX_NEAR_PAGES;dist++){
   const pg=pages[pages.length-1-dist];if(!pg)break;
   let bandBest=null;
   const n=Math.min(slots,(pg.talents||[]).length);
   const sets=lockSets(n).filter(x=>x.length>0);
   for(const idxs of sets){
     let st=dc(pg),cost=0,path=[];
     st.talents=st.talents.map((t,i)=>({...t,locked:idxs.includes(i)}));
     if(st.talents.filter(t=>t.locked).length>=slots)continue;
     for(let hold=1;hold<=maxHold;hold++){
       let tr;const before=dc(st);
       try{tr=washOnce(before)}catch(e){break}
       st=tr.state;cost+=+tr.result.pills_used||0;checked++;
       const step={locks:idxs.map(i=>({id:+before.talents[i].id,name:nm(before.talents[i].id)})),pills:+tr.result.pills_used||0,beforeSeed:+before.seed,afterSeed:+st.seed,talents:(tr.result.talents||[]).map(t=>nm(t.id)),wasPity:!!tr.result.was_pity};
       path.push(step);
       if(goal(before,st,tr)){
         const cand={cost,st:dc(st),path:dc(path),checked,dist};
         if(!bandBest||cand.cost<bandBest.cost)bandBest=cand;
         break;
       }
       if(tr.result.got_gold)break;
       const ids=new Set(idxs.map(i=>+pg.talents[i].id));
       st.talents=st.talents.map(t=>({...t,locked:ids.has(+t.id)}));
     }
   }
   if(bandBest){best=bandBest;break}
   if(dist%8===7){box.innerHTML=`<div class="warn">천장 가까운 순서로 탐색 중 · ${dist+1}/${MAX_NEAR_PAGES}회차 범위 · 후보 ${checked.toLocaleString()}개</div>`;await uiYield();}
 }
'''
route=route[:start]+new_search+route[end:]
route=route.replace("실제 상태 ${expanded.toLocaleString()}개를 탐색했지만 확정 경로를 찾지 못했습니다.${expanded>=NODE_LIMIT?' 탐색 한도에 도달했으므로 최소경로를 추정해서 표시하지 않습니다.':''}","천장에 가까운 ${MAX_NEAR_PAGES}개 회차에서 실제 후보 ${checked.toLocaleString()}개를 검사했지만 목표 seed 경로를 찾지 못했습니다.")
route=route.replace('탐색 상태: ${best.expanded.toLocaleString()}개','검사 후보: ${best.checked.toLocaleString()}개 · 천장에서 ${best.dist}회차 앞 후보군')
route=route.replace('성공 조건: 천장 직전 Born seed = ${targetSeed} · 천장 자맥 = ${targetPity} · 교체 1~15 전부 일치','성공 조건: 천장 발생 직전 Born seed = ${targetSeed}')
route=route.replace('검증 완료 최소비용 경로','목표 seed 도달 최소비용 경로')
route=route.replace(' · 실제 천장 <b>${pityName(best.st)}</b>','')
for bad in ['expanded>=NODE_LIMIT','best.expanded','targetPity','targetDraws','exchangeSequence(+after.luck_seed']:
 if bad in route: raise SystemExit('slow verification remains: '+bad)
text=text[:a]+route+text[b:]

# Remove skip column/text from table UI.
text=text.replace('<th>필요 생략</th>','')
text=text.replace('<th>목표 seed 이동 순번</th>','')
text=re.sub(r'<td class="num">\$\{rr\?\.shift\?\?\'-\'\}</td>', '', text)
text=text.replace('필요 생략','')
text=text.replace('목표 seed 이동 순번','')
text=text.replace('각 행은 해당 원시맥이 천장 직전 일반맥이 되도록 뒤의 일반맥을 생략했을 때의 직후 seed를 기준으로 계산합니다. ','각 행은 해당 원시맥 직후 seed를 기준으로 계산합니다. ')

# Strongly highlight actual default pity row.
style='''\n<style id="dao-default-pity-v314">\n#daoExchangeWindowResult tr.dao-default-pity>td{background:#fff3b0!important;border-top:3px solid #8a5a00!important;border-bottom:3px solid #8a5a00!important;font-weight:800}\n#daoExchangeWindowResult tr.dao-default-pity>td:first-child{border-left:3px solid #8a5a00!important}\n#daoExchangeWindowResult tr.dao-default-pity>td:last-child{border-right:3px solid #8a5a00!important}\n.dao-default-pity-badge{display:inline-block;margin-left:6px;padding:3px 8px;border-radius:999px;background:#8a5a00;color:#fff;font-size:11px;font-weight:800}\n</style>\n'''
he=text.lower().find('</head>');text=text[:he]+style+text[he:]
ex=text.find('async function showDaoExchangeWindowV288(){')
pos=text.find('h+=`<tr><td class="num">${r.rawNo}',ex)
if pos<0: raise SystemExit('exchange row renderer missing')
text=text[:pos]+text[pos:].replace('h+=`<tr><td class="num">${r.rawNo}', 'h+=`<tr class="${+r.rawNo===+d.firstPity.rawNo?\'dao-default-pity\':\'\'}"><td class="num">${r.rawNo}',1)
text=text.replace("<b>${r.name}</b></button></td>","<b>${r.name}</b>${+r.rawNo===+d.firstPity.rawNo?'<span class=\"dao-default-pity-badge\">기본 천장 · 0 이동</span>':''}</button></td>",1)

for x in ['MAX_NEAR_PAGES','목표 seed 도달 최소비용 경로','dao-default-pity-v314','기본 천장 · 0 이동','return !!tr.result.was_pity && +before.seed===targetSeed']:
 if x not in text: raise SystemExit('guard missing: '+x)
if '필요 생략</th>' in text: raise SystemExit('skip column remains')

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.14','file':'Nangman_Integrated_Simulator_v3_14.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.14',s);r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.14</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v314_app_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.14: near-pity seed-only search, skip UI removed, default pity highlighted')
