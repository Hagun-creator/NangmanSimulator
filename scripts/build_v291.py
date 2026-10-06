from pathlib import Path
import re, base64, subprocess

SRC=Path('Nangman_Integrated_Simulator_v2_90.html')
DST=Path('Nangman_Integrated_Simulator_v2_91.html')
if not SRC.exists(): raise SystemExit('v2.90 source missing')
text=SRC.read_text(encoding='utf-8')

# Narrow patch: only daomai function-2 interaction. Jammaek route applies to 교체 1 only.
old="""for(let i=0;i<15;i++){const n=r.draws[i]?.name||'-';h+=`<td class=\"q4\"><button type=\"button\" class=\"linkBtn\" onclick=\"showDaoPullRouteV290(${JSON.stringify(n)},${r.rawNo},${JSON.stringify(r.name)},${i+1})\">${n}</button></td>`}"""
new="""for(let i=0;i<15;i++){
       const n=r.draws[i]?.name||'-';
       if(i===0)h+=`<td class=\"q4\"><button type=\"button\" class=\"linkBtn\" onclick=\"showDaoPullRouteV290(${JSON.stringify(n)},${r.rawNo},${JSON.stringify(r.name)},1)\">${n}</button></td>`;
       else h+=`<td class=\"q4\">${n}</td>`;
     }"""
if old not in text: raise SystemExit('v2.90 clickable-cell renderer missing')
text=text.replace(old,new,1)

text=text.replace('교체맥 이름을 누르면 잡맥법으로 그 맥을 천장맥으로 당기는 최소 세수단 경로를 계산합니다.','각 행의 <b>교체 1</b>만 잡맥법 대상입니다. 교체 1을 누르면 그 맥을 천장맥으로 당기는 최소 세수단 경로를 계산합니다. 교체 2~15는 참고용입니다.',1)

# Guard route function against non-first-column calls.
needle="function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){\n const box=document.getElementById('daoPullRouteV290');if(!box)return;"
replacement="function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol){\n const box=document.getElementById('daoPullRouteV290');if(!box)return;\n if(+sourceCol!==1){box.innerHTML='<div class=\"warn\">잡맥법 천장 이동은 각 원시맥 행의 교체 1에만 적용됩니다.</div>';return;}"
if needle not in text: raise SystemExit('route function header missing')
text=text.replace(needle,replacement,1)

# Version only; preserve all unrelated behavior.
text=text.replace('v2.90','v2.91').replace('v2_90','v2_91')
text=re.sub(r'(?<![0-9])2\.90(?![0-9])','2.91',text)
pat=r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;';m=re.search(pat,text)
if not m: raise SystemExit('equipment payload missing')
inner=base64.b64decode(m.group(1)).decode('utf-8','replace').replace('v2.90','v2.91').replace('v2_90','v2_91')
inner=re.sub(r'(?<![0-9])2\.90(?![0-9])','2.91',inner)
enc=base64.b64encode(inner.encode()).decode();text=text[:m.start()]+f'const EQUIPMENT_HTML_B64="{enc}";'+text[m.end():]
DST.write_text(text,encoding='utf-8');Path('index.html').write_text(text,encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8');s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v2.91',s);r.write_text(s,encoding='utf-8')

# Regression guards.
for x in ["const sharedSaveInput = document.getElementById('sharedSaveFile')","sharedSaveInput?.addEventListener('change'","sharedSaveText = await file.text()","JSON.parse(sharedSaveText)"]:
    if x not in text: raise SystemExit('save loader regression: '+x)
if 'daoRawBeforeBtn.onclick=showDaoRawBeforeV288' not in text: raise SystemExit('function1 changed')
if 'if(i===0)h+=' not in text: raise SystemExit('교체1-only renderer missing')
if "if(+sourceCol!==1)" not in text: raise SystemExit('route column guard missing')
if '교체 2~15는 참고용입니다.' not in text: raise SystemExit('UI explanation missing')
if 'http-equiv="Cache-Control"' not in text[:8000]: raise SystemExit('cache guard lost')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
    p=Path(f'/tmp/v291_{i}.js');p.write_text(js,encoding='utf-8');cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(f'JS syntax error {i}: {cp.stderr[:1500]}')
if '<title>낭만강호 통합 시뮬레이터 v2.91</title>' not in text[:8000]: raise SystemExit('title mismatch')
print('built v2.91')
