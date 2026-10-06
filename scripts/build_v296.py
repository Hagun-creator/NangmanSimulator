from pathlib import Path
import re, base64, subprocess, json
SRC=Path('Nangman_Integrated_Simulator_v2_95.html'); DST=Path('Nangman_Integrated_Simulator_v2_96.html')
if not SRC.exists(): raise SystemExit('v2.95 source missing')
text=SRC.read_text(encoding='utf-8')

# Narrow patch: the baseline pity row stays non-clickable, but its exchange 1~15 values must remain visible.
old="""if(r.kind==='천장'){\n       h+=`<tr><td class=\"num\">${r.rawNo}</td><td class=\"num\">${r.wash}</td><td>기본 천장</td><td class=\"q4\"><b>${r.name}</b><div class=\"small\">조작 없음 · 클릭 불가</div></td>`;\n       for(let i=0;i<15;i++)h+=`<td class=\"muted\">-</td>`;\n     }else{"""
new="""if(r.kind==='천장'){\n       h+=`<tr><td class=\"num\">${r.rawNo}</td><td class=\"num\">${r.wash}</td><td>기본 천장</td><td class=\"q4\"><b>${r.name}</b><div class=\"small\">조작 없음 · 클릭 불가</div></td>`;\n       for(let i=0;i<15;i++){const n=r.draws[i]?.name||'-';h+=`<td class=\"q4\">${n}</td>`;}\n     }else{"""
if old not in text: raise SystemExit('v2.95 baseline pity row renderer missing')
text=text.replace(old,new,1)

text=text.replace('<b>기본 천장</b> 행은 조작 없이 나오는 결과라 클릭할 수 없습니다. 그 다음 <b>일반 원시맥</b> 행부터 클릭 가능하며, 천장 자맥을 제외한 일반맥 기준으로 생략 1개, 2개…를 다시 계산합니다. 각 행의 교체 1~15는 참고용입니다.',
                  '<b>기본 천장</b> 행은 조작 없이 나오는 결과라 클릭할 수 없습니다. 다만 그 천장 상태에서 이어지는 <b>교체 1~15</b>는 그대로 표시합니다. 그 다음 <b>일반 원시맥</b> 행부터 클릭 가능하며, 천장 자맥을 제외한 일반맥 기준으로 생략 1개, 2개…를 계산합니다.',1)

# Version bump only outside this focused renderer fix.
text=text.replace('v2.95','v2.96').replace('v2_95','v2_96'); text=re.sub(r'(?<![0-9])2\.95(?![0-9])','2.96',text)
text=re.sub(r'<script id="stable-root-url-v295">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v296">try{if(/Nangman_Integrated_Simulator_v2_96\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Embedded equipment: version label only; no behavior changes.
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;';m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace').replace('v2.95','v2.96').replace('v2_95','v2_96')
inner=re.sub(r'(?<![0-9])2\.95(?![0-9])','2.96',inner)
text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{base64.b64encode(inner.encode()).decode()}";'+text[m.end():]
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v2.96','file':'Nangman_Integrated_Simulator_v2_96.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.96',s);r.write_text(s,encoding='utf-8')

# Regression guards: untouched save loader and daomai interactions must remain.
for x in ["sharedSaveText = await file.text()","JSON.parse(sharedSaveText)",'daoRawBeforeBtn.onclick=showDaoRawBeforeV288','dao-pull-v295','daoDeleteCandidatesV295','조작 없음 · 클릭 불가']:
    if x not in text: raise SystemExit('regression '+x)
if 'for(let i=0;i<15;i++){const n=r.draws[i]?.name||\'-\';h+=`<td class="q4">${n}</td>`;}' not in text:
    raise SystemExit('baseline pity exchange 1~15 renderer missing')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v296_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:1500])
if '<title>낭만강호 통합 시뮬레이터 v2.96</title>' not in text[:10000]: raise SystemExit('title mismatch')
print('built v2.96')
