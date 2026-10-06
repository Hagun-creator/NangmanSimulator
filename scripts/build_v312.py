from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_11.html')
DST=Path('Nangman_Integrated_Simulator_v3_12.html')
if not SRC.exists(): raise SystemExit('v3.11 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.11','v3.12').replace('v3_11','v3_12')
text=re.sub(r'(?<![0-9])3\.11(?![0-9])','3.12',text)
text=re.sub(r'<script id="stable-root-url-v311">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v312">try{if(/Nangman_Integrated_Simulator_v3_12\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# 1) Stop using the arbitrary #700 window. Capture the whole pre-pity normal stream,
# then only display the six normals immediately before the first pity.
text=text.replace('const minRaw=700;','const minRaw=0;',1)
text=text.replace("if(guard<=0)throw Error('원시 #700 이후 천장 직전 흐름 계산 한도를 초과했습니다.');","if(guard<=0)throw Error('첫 천장 직전 흐름 계산 한도를 초과했습니다.');",1)
old="""   const usablePre=candidates.filter(x=>+x.rawNo<=+currentPrev.rawNo).sort((a,b)=>a.rawNo-b.rawNo);
   if(!usablePre.length)throw Error('원시 #700 이후 천장 직전 후보 일반맥이 없습니다.');

   // Validation extension: continue the normal raw stream for 100 accepted raws after pity.
   // Purple pity/exchange uses luck_seed; the ordinary raw seed continues independently.
   const post=[];
   let postSeed=+seed,postRc=+rc,postRaw=+currentPrev.rawNo,postWash=washNo;
   while(post.length<100&&guard-->0){
     postWash++;
     const seenPost=new Set();let acceptedPost=0;
     while(acceptedPost<slots&&post.length<100&&guard-->0){
       let id;[id,postSeed]=rawNormal(postSeed,eng,intl?postRc:0);if(intl)postRc++;
       if(!eng.allowed.has(id)||seenPost.has(id))continue;
       const it=BYID.get(id);if(!it)continue;
       seenPost.add(id);acceptedPost++;postRaw++;
       post.push({rawNo:postRaw,wash:postWash,id,name:nm(id),seedAfter:+postSeed,rcAfter:+postRc,postPity:true,afterPity:postRaw-(+currentPrev.rawNo)});
     }
   }
   if(post.length<100)throw Error('천장 이후 검증용 원시맥 100개 생성 한도를 초과했습니다.');
   const usable=[...usablePre,...post];
"""
new="""   const allPre=candidates.filter(x=>+x.rawNo<=+currentPrev.rawNo).sort((a,b)=>a.rawNo-b.rawNo);
   const usablePre=allPre.slice(-6).map(x=>({...x,segment:'pre'}));
   if(!usablePre.length)throw Error('첫 천장 직전 후보 일반맥이 없습니다.');

   // After the first pity, continue the ordinary raw stream only until the NEXT natural purple.
   // These are real exchange-table rows, not a fixed-size validation tail.
   const post=[];
   let postSeed=+seed,postRc=+rc,postRaw=+currentPrev.rawNo,postWash=washNo,nextNaturalPurple=null;
   postLoop: while(guard-->0){
     postWash++;
     const seenPost=new Set();let acceptedPost=0;
     while(acceptedPost<slots&&guard-->0){
       let id;[id,postSeed]=rawNormal(postSeed,eng,intl?postRc:0);if(intl)postRc++;
       if(!eng.allowed.has(id)||seenPost.has(id))continue;
       const it=BYID.get(id);if(!it)continue;
       seenPost.add(id);acceptedPost++;postRaw++;
       if(+it.weight===4){
         nextNaturalPurple={rawNo:postRaw,wash:postWash,id,name:nm(id),seedAfter:+postSeed,rcAfter:+postRc};
         break postLoop;
       }
       post.push({rawNo:postRaw,wash:postWash,id,name:nm(id),seedAfter:+postSeed,rcAfter:+postRc,postPity:true,segment:'post'});
     }
   }
   if(!nextNaturalPurple)throw Error('첫 천장 이후 다음 원시 자맥을 찾지 못했습니다.');
   const postEndRaw=post.length?+post[post.length-1].rawNo:+currentPrev.rawNo;
   for(const x of post)x.segmentEndRaw=postEndRaw;
   for(const x of usablePre)x.segmentEndRaw=+currentPrev.rawNo;
   const usable=[...usablePre,...post];
"""
if old not in text: raise SystemExit('v3.11 post block not found')
text=text.replace(old,new,1)

old2="""   const routeRows=rows.map(r=>({
     ...r,
     firstDraw:r.pity?.name||'',
     postPity:!!r.postPity,
     shift:r.postPity?null:Math.max(0,(+currentPrev.rawNo)-(+r.rawNo))
   }));
"""
new2="""   const routeRows=rows.map(r=>({
     ...r,
     firstDraw:r.pity?.name||'',
     postPity:!!r.postPity,
     segment:r.segment|| (r.postPity?'post':'pre'),
     segmentEndRaw:+(r.segmentEndRaw??currentPrev.rawNo),
     shift:Math.max(0,+(r.segmentEndRaw??currentPrev.rawNo)-(+r.rawNo)),
     nextPurpleName:r.postPity?(nextNaturalPurple?.name||''):d.firstPity.name,
     nextPurpleRaw:r.postPity?(nextNaturalPurple?.rawNo||0):d.firstPity.rawNo
   }));
"""
if old2 not in text: raise SystemExit('routeRows block not found')
text=text.replace(old2,new2,1)

# Make post-pity rows clickable too and show their required skip count in the same column.
pat=re.compile(r'''     h\+=`<tr><td class="num">\$\{r\.rawNo\}</td><td class="num">\$\{r\.wash\}</td><td class="num">\$\{r\.postPity\?`천장후 \+\$\{r\.afterPity\}`:\(rr\?\.shift\?\?'-'\)\}</td>`\+\n       \(r\.postPity\?`<td><b>\$\{r\.name\}</b> <span class="small">\(검증\)</span></td>`:`<td><button type="button" class="linkBtn dao-pull-v295" data-raw="\$\{r\.rawNo\}" data-source="\$\{encodeURIComponent\(r\.name\)\}"><b>\$\{r\.name\}</b></button></td>`\)\+\n       `<td class="q4"><b>\$\{r\.pity\?\.name\|\|'-'\}</b></td>`;''')
m=pat.search(text)
if not m: raise SystemExit('post row renderer not found')
repl='''     h+=`<tr><td class="num">${r.rawNo}</td><td class="num">${r.wash}</td><td class="num">${rr?.shift??'-'}</td>`+\n       `<td><button type="button" class="linkBtn dao-pull-v295" data-raw="${r.rawNo}" data-source="${encodeURIComponent(r.name)}"><b>${r.name}</b></button></td>`+\n       `<td class="q4"><b>${r.pity?.name||'-'}</b></td>`;'''
text=text[:m.start()]+repl+text[m.end():]

# Clicking a post-pity row must report how many accepted normal raws must be skipped
# before the next natural purple boundary. Keep the existing exact pre-pity route logic untouched.
old3=""" const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!row||row.postPity){box.innerHTML='<div class=\"warn\">최소루트 계산은 천장 이전 원시맥만 선택할 수 있습니다.</div>';return}
 const target=row.firstDraw||targetName||'';
"""
new3=""" const row=DAO_V290_ROUTE_ROWS.find(x=>+x.rawNo===+sourceRaw);
 if(!row){box.innerHTML='<div class=\"warn\">선택한 원시맥 행을 찾지 못했습니다.</div>';return}
 const target=row.firstDraw||targetName||'';
 if(row.postPity){
   const needDel=Math.max(0,+row.segmentEndRaw-(+sourceRaw));
   box.innerHTML=`<div class=\"good\"><b>${sourceName}</b> 기준 → 교체 후보 <b>${target}</b></div>`+
     `<div class=\"small\" style=\"line-height:1.7;margin:6px 0\">다음 원시 자맥: <b>#${row.nextPurpleRaw} ${row.nextPurpleName}</b><br>`+
     `선택한 원시맥: #${sourceRaw} ${sourceName}<br>이 원시맥 기준 결과를 당기려면 필요한 일반맥 생략 수: <b>${needDel}개</b></div>`;
   return;
 }
"""
if old3 not in text: raise SystemExit('route post rejection block not found')
text=text.replace(old3,new3,1)

# Labels/descriptions only.
text=text.replace('2. 원시 #700~천장 이후 100 교체맥 보기','2. 자맥 구간별 교체맥 보기',1)
text=text.replace('원시 #700부터 천장 직전 + 천장 이후 100개까지 천장/교체맥 15개 계산 중...','첫 천장 직전 6개 + 첫 천장 이후 다음 원시 자맥 직전까지 교체맥 15개 계산 중...',1)
text=text.replace('원시 #700~천장 직전 + 천장 이후 100개 원시맥별 교체맥 검증표','첫 천장 직전 6개 + 다음 원시 자맥 직전까지 교체맥 표',1)
text=text.replace('먼저 원시 #700~천장 이후 100 교체맥 표를 계산하세요.','먼저 자맥 구간별 교체맥 표를 계산하세요.',1)

# Explanatory copy: replace the v3.09 fixed-window wording if present.
text=text.replace('2번은 원시 #700부터 천장 직전 일반맥과 천장 이후 일반 원시맥 100개를 검증용으로 표시합니다.','2번은 첫 천장 직전 일반맥 6개와, 첫 천장 이후부터 다음 원시 자맥 직전까지 각 일반 원시맥의 교체 1~15를 표시합니다.',1)

for x in ['slice(-6)','nextNaturalPurple','segmentEndRaw','2. 자맥 구간별 교체맥 보기','필요한 일반맥 생략 수']:
 if x not in text: raise SystemExit('v3.12 guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.12','file':'Nangman_Integrated_Simulator_v3_12.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.12',s);r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.12</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v312_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.12: 6 pre-pity rows + full post-pity interval until next natural purple; all rows clickable for skip count')
