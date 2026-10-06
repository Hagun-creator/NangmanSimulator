from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_03.html')
DST=Path('Nangman_Integrated_Simulator_v3_04.html')
if not SRC.exists(): raise SystemExit('v3.03 source missing')
text=SRC.read_text(encoding='utf-8')

# Version bump only from v3.03 baseline.
text=text.replace('v3.03','v3.04').replace('v3_03','v3_04')
text=re.sub(r'(?<![0-9])3\.03(?![0-9])','3.04',text)
text=re.sub(r'<script id="stable-root-url-v304">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v304">try{if(/Nangman_Integrated_Simulator_v3_04\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+text[he:]

# Fix the apparently dead second daomai button.
# The handler used DOM ids as implicit window globals before entering its try/catch.
# On browsers where named DOM globals are not exposed/reliable, that throws before any UI can update.
needle="async function showDaoExchangeWindowV288(){\n daoRawBeforeResult.innerHTML='';"
replacement="""async function showDaoExchangeWindowV288(){
 const daoRawBeforeResult=document.getElementById('daoRawBeforeResult');
 const daoExchangeWindowResult=document.getElementById('daoExchangeWindowResult');
 if(!daoExchangeWindowResult){console.error('daoExchangeWindowResult not found');return;}
 if(daoRawBeforeResult)daoRawBeforeResult.innerHTML='';"""
if needle not in text: raise SystemExit('exchange handler header not found')
text=text.replace(needle,replacement,1)

# Use explicit DOM lookup for both buttons. Wrap button 2 so any rejected async error is shown instead of looking dead.
old='daoRawBeforeBtn.onclick=showDaoRawBeforeV288;daoExchangeWindowBtn.onclick=showDaoExchangeWindowV288;'
new="""(()=>{
 const b1=document.getElementById('daoRawBeforeBtn');
 const b2=document.getElementById('daoExchangeWindowBtn');
 if(b1)b1.onclick=showDaoRawBeforeV288;
 if(b2)b2.onclick=()=>Promise.resolve().then(()=>showDaoExchangeWindowV288()).catch(e=>{
   console.error('daomai exchange click failed',e);
   const out=document.getElementById('daoExchangeWindowResult');
   if(out)out.innerHTML='<div class=\"warn\">교체맥 계산 오류: '+String(e&&e.message||e)+'</div>';
 });
})();"""
if old not in text: raise SystemExit('daomai button binding not found')
text=text.replace(old,new,1)

# Guard the important behavior and the runtime fix.
for x in [
 '2. 원시 #700~천장 직전 교체맥 보기',
 'const minRaw=700;',
 "document.getElementById('daoExchangeWindowResult')",
 "document.getElementById('daoExchangeWindowBtn')",
 'showDaoExchangeWindowV288()',
 '교체맥 계산 오류:'
]:
 if x not in text: raise SystemExit('v3.04 guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.04','file':'Nangman_Integrated_Simulator_v3_04.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md')
s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.04',s)
r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.04</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v304_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.04: explicit daomai DOM binding + visible async click errors')
