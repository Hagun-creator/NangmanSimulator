from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_09.html')
DST=Path('Nangman_Integrated_Simulator_v3_10.html')
if not SRC.exists(): raise SystemExit('v3.09 source missing')
text=SRC.read_text(encoding='utf-8')

text=text.replace('v3.09','v3.10').replace('v3_09','v3_10')
text=re.sub(r'(?<![0-9])3\.09(?![0-9])','3.10',text)
text=re.sub(r'<script id="stable-root-url-v309">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
text=text[:he]+'''<script id="stable-root-url-v310">try{if(/Nangman_Integrated_Simulator_v3_10\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}<\/script>\n'''+text[he:]

# Keep each wash step as one self-contained block so duplicate-skip text cannot overlap
# adjacent list items or cover the main line.
old='''   h+=`<li style="margin:6px 0"><b>${p.wash}회차</b>: #${best.lock.rawNo} ${best.lock.name} 잠금 유지 + 새 칸 ${acc}${sk?`<br><span class="good">이 회차 중복 스킵: ${sk}</span>`:''}</li>`;'''
new='''   h+=`<li style="margin:8px 0;padding:8px 10px;border:1px solid #e1e5ea;border-radius:7px;background:#fff;line-height:1.65;overflow:visible">`+\n      `<div><b>${p.wash}회차</b>: #${best.lock.rawNo} ${best.lock.name} 잠금 유지 + 새 칸 ${acc}</div>`+\n      (sk?`<div style="display:block;position:static;margin-top:5px;padding:5px 7px;border-radius:6px;background:#eef8f0;border:1px solid #b8d9be;color:#234b2a;white-space:normal;line-height:1.5"><b>이 회차 중복 스킵</b>: ${sk}</div>`:'')+\n      `</li>`;'''
if old not in text: raise SystemExit('route list renderer not found')
text=text.replace(old,new,1)

# Add a small guard style in case inherited .good styling/positioning changes later.
css='''<style id="dao-route-layout-v310">\n#daoPullRouteV290 ol{display:block!important;overflow:visible!important}\n#daoPullRouteV290 li{position:relative!important;height:auto!important;min-height:0!important;overflow:visible!important}\n#daoPullRouteV290 li>div{position:static!important;float:none!important;clear:both!important}\n</style>\n'''
he=text.lower().find('</head>')
text=text[:he]+css+text[he:]

for x in [
 '이 회차 중복 스킵</b>: ${sk}',
 'dao-route-layout-v310',
 'overflow:visible',
 'v3.10'
]:
 if x not in text: raise SystemExit('v3.10 guard missing: '+x)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.10','file':'Nangman_Integrated_Simulator_v3_10.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md')
s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.10',s)
r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.10</title>' not in text[:10000]: raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\\b[^>]*>(.*?)</script>',text,re.I|re.S)):
 p=Path(f'/tmp/v310_app_{i}.js');p.write_text(js,encoding='utf-8')
 cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
 if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.10: duplicate-skip messages rendered below each wash without overlap')
