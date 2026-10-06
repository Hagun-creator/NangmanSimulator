from pathlib import Path
import re, subprocess, json

BASE=Path('Nangman_Integrated_Simulator_v3_29.html')
DONOR=Path('Nangman_Integrated_Simulator_v3_30.html')
DST=Path('Nangman_Integrated_Simulator_v3_31.html')
if not BASE.exists(): raise SystemExit('v3.29 known-good base missing')
if not DONOR.exists(): raise SystemExit('v3.30 route donor missing')
base=BASE.read_text(encoding='utf-8')
donor=DONOR.read_text(encoding='utf-8')

# Version changes only. All functional code outside showDaoPullRouteV290 must remain from v3.29.
def bump(s, old):
    s=s.replace('v'+old,'v3.31').replace('v'+old.replace('.','_'),'v3_31')
    s=re.sub(r'(?<![0-9])'+re.escape(old)+r'(?![0-9])','3.31',s)
    return s

base=bump(base,'3.29')
donor=bump(donor,'3.30')

# Normalize only the stable-root helper in the base document.
base=re.sub(r'<script id="stable-root-url-v\d+">.*?</script>\s*','',base,flags=re.S)
he=base.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
base=base[:he]+'''<script id="stable-root-url-v331">try{if(/Nangman_Integrated_Simulator_v3_31\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+base[he:]

# Extract ONLY the daomai/kamek route function from v3.30 donor.
def bounds(s):
    a=s.find('async function showDaoPullRouteV290(')
    b=s.find('\nasync function showDaoExchangeWindowV288(){',a)
    if a<0 or b<0: raise SystemExit('route boundary missing')
    return a,b
ba,bb=bounds(base)
da,db=bounds(donor)
donor_route=donor[da:db]
if 'function makeEpisodes()' not in donor_route or 'function validateMulti(' not in donor_route or 'best.multiEpisodes' not in donor_route:
    raise SystemExit('v3.30 multi-episode engine missing from donor')

# Surgical replacement: nothing outside the route function may change.
prefix=base[:ba]
suffix=base[bb:]
out=prefix+donor_route+suffix

# Hard regression guard: exact byte-for-byte equality outside the route function.
oa,ob=bounds(out)
if out[:oa] != prefix or out[ob:] != suffix:
    raise SystemExit('REGRESSION: code outside daomai route function changed')

# Additional save/load regression guards: counts outside route must remain exactly the known-good base counts.
base_outside=prefix+suffix
out_outside=out[:oa]+out[ob:]
for token in ['FileReader','JSON.parse','localStorage','addEventListener','type="file"','세이브','불러오기']:
    if base_outside.count(token) != out_outside.count(token):
        raise SystemExit('REGRESSION save/load token changed: '+token)

DST.write_text(out,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.31','file':'Nangman_Integrated_Simulator_v3_31.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md')
s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.31',s)
r.write_text(s,encoding='utf-8')

if '<title>낭만강호 통합 시뮬레이터 v3.31</title>' not in out[:10000]:
    raise SystemExit('title mismatch')
for i,js in enumerate(re.findall(r'<script\b[^>]*>(.*?)</script>',out,re.I|re.S)):
    p=Path(f'/tmp/v331_app_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:2000])
print('built v3.31: v3.29 known-good outside route + v3.30 daomai route only; save/load regression guard passed')
