from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_04.html')
DST=Path('Nangman_Integrated_Simulator_v3_05.html')
if not SRC.exists(): raise SystemExit('v3.04 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.04','v3.05').replace('v3_04','v3_05')
text=re.sub(r'(?<![0-9])3\.04(?![0-9])','3.05',text)
text=re.sub(r'<script id="stable-root-url-v304">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v305">try{if(/Nangman_Integrated_Simulator_v3_05\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# v3.01+ regression: the second daomai table retained a call to daoV296Key(),
# but that helper is absent from the current integrated script. Cache is optional,
# so remove only this stale dependency and always recompute on click.
old=""" const cacheKey=daoV296Key()+'|pre700-v303';
 if(DAO_V296_EXCHANGE_CACHE&&DAO_V296_EXCHANGE_CACHE.key===cacheKey){
   renderDaoExchangeV296(DAO_V296_EXCHANGE_CACHE.pack);
   return;
 }
"""
if old not in text:
    # tolerate version-propagated cache suffix if it changed elsewhere
    m=re.search(r" const cacheKey=daoV296Key\(\)\+'\|pre700-[^']+';\n if\(DAO_V296_EXCHANGE_CACHE&&DAO_V296_EXCHANGE_CACHE\.key===cacheKey\)\{\n   renderDaoExchangeV296\(DAO_V296_EXCHANGE_CACHE\.pack\);\n   return;\n \}\n",text)
    if not m: raise SystemExit('stale daoV296Key cache block not found')
    text=text[:m.start()]+text[m.end():]
else:
    text=text.replace(old,'',1)

old_assign='   DAO_V296_EXCHANGE_CACHE={key:cacheKey,pack};\n   renderDaoExchangeV296(pack);'
if old_assign not in text: raise SystemExit('cache assignment block not found')
text=text.replace(old_assign,'   renderDaoExchangeV296(pack);',1)

# Keep visible error reporting and all #700+/route behavior intact.
for x in [
 '2. 원시 #700~천장 직전 교체맥 보기',
 'const minRaw=700;',
 "document.getElementById('daoExchangeWindowBtn')",
 '교체맥 계산 오류:',
 'renderDaoExchangeV296(pack);',
 'function showDaoPullRouteV290(targetName,sourceRaw,sourceName,sourceCol)'
]:
 if x not in text: raise SystemExit('v3.05 guard missing: '+x)
if 'daoV296Key()' in text: raise SystemExit('stale daoV296Key reference remains')

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.05','file':'Nangman_Integrated_Simulator_v3_05.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md')
s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.05',s)
r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.05</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v305_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.05: removed undefined daoV296Key cache dependency; #700 exchange table unchanged')
