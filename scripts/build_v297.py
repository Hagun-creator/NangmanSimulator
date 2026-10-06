from pathlib import Path
import re, base64, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v2_96.html')
DST=Path('Nangman_Integrated_Simulator_v2_97.html')
if not SRC.exists(): raise SystemExit('v2.96 source missing')
text=SRC.read_text(encoding='utf-8')

# 1) Preserve exact state immediately BEFORE the pity wash so same-wash trailing normals
#    (#854/#855 in the reported save) can recover their exact post-row normal seed.
old="const rows=[];let firstPity=null,nextPurple=null,pityState=null,guard=10000;"
new="const rows=[];let firstPity=null,nextPurple=null,pityState=null,pityBeforeState=null,guard=10000;"
if old not in text: raise SystemExit('dao window state declaration missing')
text=text.replace(old,new,1)
old="const beforeBars=+st.total_talent_bars;\n   const tr=washOnce(st);st=tr.state;"
new="const beforeBars=+st.total_talent_bars;\n   const beforeState=dc(st);\n   const tr=washOnce(st);st=tr.state;"
if old not in text: raise SystemExit('wash before-state anchor missing')
text=text.replace(old,new,1)
old="firstPity=purple;pityState=dc(st);"
new="firstPity=purple;pityState=dc(st);pityBeforeState=beforeState;"
if old not in text: raise SystemExit('first pity capture anchor missing')
text=text.replace(old,new,1)
old="return {rows,firstPity,nextPurple,pityState};"
new="return {rows,firstPity,nextPurple,pityState,pityBeforeState};"
if old not in text: raise SystemExit('dao window return anchor missing')
text=text.replace(old,new,1)

# 2) Replace v2.96's deliberate same-pity-wash blank rows with exact replay.
old=r'''   // If the pity page itself had trailing normal rows, do not invent branch seeds for them.
   const samePityWash=actual.slice(1).filter(x=>+x.wash===+d.firstPity.wash);
   if(samePityWash.length){
     rows.splice(1,0,...samePityWash.map(x=>({rawNo:x.rawNo,wash:x.wash,id:x.id,name:x.name,kind:'원시',seed:null,draws:[],samePityWash:true})));
   }
'''
new=r'''   // Recover trailing normal rows on the SAME pity wash exactly.
   // washOnce uses luck_seed only until the pity purple is accepted; after that it resumes
   // the normal seed stream. Replaying that stream from the state before the pity wash gives
   // the exact post-row seed for #854, #855, ... without guessing.
   const samePityWash=actual.slice(1).filter(x=>+x.wash===+d.firstPity.wash);
   if(samePityWash.length){
     if(!d.pityBeforeState)throw Error('천장 직전 상태가 없어 같은 회차 원시맥 교체표를 복원할 수 없습니다.');
     const pre=dc(d.pityBeforeState),preEng=engineFor(pre);
     let pseed=+pre.seed,prc=+(pre.born_talent_rc||0),pintl=!!pre.international_wash;
     const seen=new Set([+d.firstPity.id]);
     const recovered=[];
     for(const want of samePityWash){
       let ok=false,localGuard=100000;
       while(localGuard-->0){
         let id;[id,pseed]=rawNormal(pseed,preEng,pintl?prc:0);if(pintl)prc++;
         if(!preEng.allowed.has(id)||seen.has(id))continue;
         const it=BYID.get(id);if(!it)continue;
         // A second purple on a page is rejected by washOnce and does not enter `seen`.
         if(+it.weight===4)continue;
         seen.add(id);
         if(+id!==+want.id){
           throw Error(`천장 동일 회차 원시맥 재현 불일치: #${want.rawNo} ${want.name} / 재현 ${nm(id)}. 추정값은 표시하지 않습니다.`);
         }
         const branch=dc(pre);branch.seed=+pseed;if(pintl)branch.born_talent_rc=+prc;
         recovered.push({rawNo:want.rawNo,wash:want.wash,id:want.id,name:want.name,kind:'원시',seed:+pseed,draws:exchangeSequence(+pseed,branch,15)});
         ok=true;break;
       }
       if(!ok)throw Error(`#${want.rawNo} ${want.name}의 동일 회차 seed 복원 한도를 초과했습니다.`);
     }
     rows.splice(1,0,...recovered);
   }
'''
if old not in text: raise SystemExit('v2.96 same-pity blank block missing')
text=text.replace(old,new,1)

# 3) Same-wash rows now have real draws, so remove the conditional '-' renderer.
old="h+=r.samePityWash?`<td class=\"muted\">-</td>`:`<td class=\"q4\">${n}</td>`;"
new="h+=`<td class=\"q4\">${n}</td>`;"
if old not in text: raise SystemExit('same-pity blank renderer missing')
text=text.replace(old,new,1)

text=text.replace('천장 이후 실제 원시 흐름과 교체맥 15개 계산 중... 최초 1회만 계산합니다.',
                  '천장 이후 실제 원시 흐름과 교체맥 15개 계산 중... 같은 천장 회차 후속 원시맥도 정확한 seed로 복원합니다.',1)
text=text.replace('원시맥 순서는 새 RNG 생성이 아니라 <b>washOnce() 실제 원시 흐름</b>을 사용합니다. 같은 세이브/조건에서는 최초 1회 계산 후 캐시되어 다시 누르면 즉시 표시됩니다.',
                  '원시맥 순서는 새 RNG 생성이 아니라 <b>washOnce() 실제 원시 흐름</b>을 사용합니다. 천장과 같은 세수 회차에 이어지는 일반 원시맥도 천장 직전 상태에서 normal seed를 재생해 각 행의 교체 1~15를 표시합니다. 같은 세이브/조건에서는 최초 1회 계산 후 캐시되어 다시 누르면 즉시 표시됩니다.',1)

# 4) Version bump only outside the focused daomai fix.
text=text.replace('v2.96','v2.97').replace('v2_96','v2_97')
text=re.sub(r'(?<![0-9])2\.96(?![0-9])','2.97',text)
text=re.sub(r'<script id="stable-root-url-v296">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v297">try{if(/Nangman_Integrated_Simulator_v2_97\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Embedded equipment: display-version bump only; no equipment behavior edits.
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;'
m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace')
inner=inner.replace('v2.96','v2.97').replace('v2_96','v2_97')
inner=re.sub(r'(?<![0-9])2\.96(?![0-9])','2.97',inner)
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{base64.b64encode(inner.encode()).decode()}";'+text[m.end():]

DST.write_text(text,encoding='utf-8')
Path('index.html').write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v2.97','file':'Nangman_Integrated_Simulator_v2_97.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.97',s);r.write_text(s,encoding='utf-8')

# Regression guards: unrelated working systems must remain.
for x in [
    "sharedSaveText = await file.text()","JSON.parse(sharedSaveText)",
    'daoRawBeforeBtn.onclick=showDaoRawBeforeV288','daoDeleteCandidatesV295','dao-pull-v295',
    'DAO_V296_EXCHANGE_CACHE','border-top:3px solid currentColor',
    'pityBeforeState','samePityWash','exchangeSequence(+pseed,branch,15)',
    '천장 동일 회차 원시맥 재현 불일치'
]:
    if x not in text: raise SystemExit('regression '+x)
if 'samePityWash?`<td class="muted">-</td>`' in text: raise SystemExit('same-pity blank renderer remains')
if DST.read_text(encoding='utf-8')!=Path('index.html').read_text(encoding='utf-8'): raise SystemExit('index/versioned mismatch')
if '<title>낭만강호 통합 시뮬레이터 v2.97</title>' not in text[:10000]: raise SystemExit('title mismatch')
if '현재 사이트 버전: v2.97' not in r.read_text(encoding='utf-8'): raise SystemExit('README mismatch')

for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v297_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:1500])
print('built v2.97')
