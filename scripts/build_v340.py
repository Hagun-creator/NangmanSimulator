from pathlib import Path
import re,base64,subprocess,json

SRC=Path('Nangman_Integrated_Simulator_v3_39.html')
DST=Path('Nangman_Integrated_Simulator_v3_40.html')
if not SRC.exists(): raise SystemExit('v3.39 source missing')
text=SRC.read_text(encoding='utf-8')
if '</head>' not in text.lower(): raise SystemExit('v3.39 source is not normal HTML')

text=text.replace('v3.39','v3.40').replace('v3_39','v3_40')
text=re.sub(r'(?<![0-9])3\.39(?![0-9])','3.40',text)
text=re.sub(r'<script id="stable-root-url-v339">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
text=text[:he]+'''<script id="stable-root-url-v340">try{if(/Nangman_Integrated_Simulator_v3_40\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>
'''+text[he:]

m=re.search(r'const EQUIPMENT_HTML_B64="([A-Za-z0-9+/=]+)";',text)
if not m: raise SystemExit('equipment iframe payload missing')
h=base64.b64decode(m.group(1)).decode('utf-8')

bad='\\nwindow.rk218Open=open;window.addEventListener(\'load\',mount);'
good='\nwindow.rk218Open=open;window.addEventListener(\'load\',mount);'
if bad not in h: raise SystemExit('expected v3.39 literal backslash-n bug not found')
h=h.replace(bad,good,1)
if bad in h: raise SystemExit('literal backslash-n remains')
for tok in ['data-v="auto"','paintAutoEquip339','자동 시뮬레이션 시작','rkXlCurve237',"showDetailTop233(o,'auto','xl')"]:
    if tok not in h: raise SystemExit('auto feature missing: '+tok)

iframe_scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',h,re.I|re.S)
if not iframe_scripts: raise SystemExit('no iframe scripts found')
iframe_checked=0
for i,js in enumerate(iframe_scripts):
    if not js.strip(): continue
    p=Path(f'/tmp/v340_iframe_{i}.js'); p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit('iframe JS error\n'+cp.stderr[:4000])
    iframe_checked+=1

enc=base64.b64encode(h.encode('utf-8')).decode('ascii')
text=text[:m.start(1)]+enc+text[m.end(1):]

parent_scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)
if not parent_scripts: raise SystemExit('no parent scripts found')
parent_checked=0
for i,js in enumerate(parent_scripts):
    if not js.strip(): continue
    p=Path(f'/tmp/v340_parent_{i}.js'); p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit('parent JS error\n'+cp.stderr[:4000])
    parent_checked+=1

if '<title>낭만강호 시뮬레이터 v3.40</title>' not in text[:12000]: raise SystemExit('title mismatch')
DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.40','file':'Nangman_Integrated_Simulator_v3_40.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md'); rs=r.read_text(encoding='utf-8'); rs=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.40',rs); r.write_text(rs,encoding='utf-8')
print(f'built v3.40: fixed equipment iframe parse bug; iframe JS checked={iframe_checked}, parent JS checked={parent_checked}')
