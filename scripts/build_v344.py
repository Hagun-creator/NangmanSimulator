from pathlib import Path
import re,subprocess,json

SRC=Path('Nangman_Integrated_Simulator_v3_43.html')
DST=Path('Nangman_Integrated_Simulator_v3_44.html')
if not SRC.exists(): raise SystemExit('v3.43 source missing')
text=SRC.read_text(encoding='utf-8')
if '</head>' not in text.lower(): raise SystemExit('v3.43 source is not normal HTML')

text=text.replace('v3.43','v3.44').replace('v3_43','v3_44')
text=re.sub(r'(?<![0-9])3\.43(?![0-9])','3.44',text)

# Remove every old stable-root helper plus any literal backslash-n immediately around it.
text=re.sub(r'\\n(?=<script id="stable-root-url-v\d+">)','',text)
text=re.sub(r'<script id="stable-root-url-v\d+">.*?</script>\s*','',text,flags=re.S)
text=re.sub(r'\\n\s*(?=</head>)','',text)

# Restore exactly one helper with a real newline, never a literal "\\n".
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
helper='<script id="stable-root-url-v344">try{if(/Nangman_Integrated_Simulator_v3_44\\.html/i.test(location.pathname)){history.replaceState(null,\'\',\'/NangmanSimulator/\');}}catch(e){}</script>\n'
text=text[:he]+helper+text[he:]

# Remove stale top-summary drop text.
text=re.sub(r'(세수\s*·\s*캐릭터 상태\s*·\s*장비 제작/정련/촉련/특수부가·망정/검왕각)\s*·\s*드랍\s*·\s*(<span id="saveDataState">)',r'\1 · \2',text)

# Guards.
head=text[:50000]
if '\\n<script id="stable-root-url' in head: raise SystemExit('visible literal backslash-n remains')
if len(re.findall(r'id="stable-root-url-v\d+"',head))!=1: raise SystemExit('stable root helper count mismatch')
if '· 드랍 ·' in head: raise SystemExit('drop summary remains')
if '<title>낭만강호 시뮬레이터 v3.44</title>' not in head: raise SystemExit('title mismatch')

scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)
checked=0
for i,js in enumerate(scripts):
    if not js.strip(): continue
    p=Path(f'/tmp/v344_parent_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit('parent JS error\n'+cp.stderr[:4000])
    checked+=1

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.44','file':'Nangman_Integrated_Simulator_v3_44.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');rs=r.read_text(encoding='utf-8');rs=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.44',rs);r.write_text(rs,encoding='utf-8')
print(f'built v3.44 head cleanup only; parent JS checked={checked}')
