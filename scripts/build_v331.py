from pathlib import Path
import re, subprocess, json

BASE=Path('Nangman_Integrated_Simulator_v3_29.html')
PATCHER=Path('scripts/build_v330.py')
DST=Path('Nangman_Integrated_Simulator_v3_31.html')
if not BASE.exists(): raise SystemExit('v3.29 known-good base missing')
if not PATCHER.exists(): raise SystemExit('v3.30 patch source missing')
base0=BASE.read_text(encoding='utf-8')
patchsrc=PATCHER.read_text(encoding='utf-8')

# Pull the intended v3.30 engine literal from the patch source, not from the broken generated HTML.
m=re.search(r"new=r'''(.*?)'''\nroute=route\[:start\]\+new\+route\[end:\]",patchsrc,re.S)
if not m: raise SystemExit('cannot extract v3.30 engine literal')
new_engine=m.group(1)
if 'function makeEpisodes()' not in new_engine or 'function validateMulti(' not in new_engine:
    raise SystemExit('v3.30 multi-episode engine literal incomplete')

# Extract the intended multi-episode output insertion too.
mo=re.search(r"route=route\[:pos\]\+r'''(.*?)''' \+ route\[pos:\]",patchsrc,re.S)
if not mo: raise SystemExit('cannot extract v3.30 output insertion')
output_insert=mo.group(1)

# Version-only transformation of the known-good v3.29 base.
base=base0.replace('v3.29','v3.31').replace('v3_29','v3_31')
base=re.sub(r'(?<![0-9])3\.29(?![0-9])','3.31',base)
base=re.sub(r'<script id="stable-root-url-v\d+">.*?</script>\s*','',base,flags=re.S)
he=base.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
base=base[:he]+'''<script id="stable-root-url-v331">try{if(/Nangman_Integrated_Simulator_v3_31\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''+base[he:]

def bounds(s):
    a=s.find('async function showDaoPullRouteV290(')
    b=s.find('\nasync function showDaoExchangeWindowV288(){',a)
    if a<0 or b<0: raise SystemExit('route boundary missing')
    return a,b

def balanced_block_end(s,start):
    # start points at ' outer:{'. Count JS braces. Template ${...} and object braces are balanced too.
    p=s.find('{',start)
    if p<0: return -1
    depth=0; quote=None; esc=False; line_comment=False; block_comment=False
    i=p
    while i<len(s):
        c=s[i]; n=s[i+1] if i+1<len(s) else ''
        if line_comment:
            if c=='\n': line_comment=False
            i+=1; continue
        if block_comment:
            if c=='*' and n=='/': block_comment=False; i+=2; continue
            i+=1; continue
        if quote:
            if esc: esc=False; i+=1; continue
            if c=='\\': esc=True; i+=1; continue
            # For template literals, still count ${...} by temporarily leaving quote until its matching } is hard;
            # braces inside ${} are balanced in our generated code, so simply ignore literal text braces.
            if c==quote: quote=None
            i+=1; continue
        if c=='/' and n=='/': line_comment=True; i+=2; continue
        if c=='/' and n=='*': block_comment=True; i+=2; continue
        if c in ("'",'"','`'): quote=c; i+=1; continue
        if c=='{': depth+=1
        elif c=='}':
            depth-=1
            if depth==0: return i+1
        i+=1
    return -1

a,b=bounds(base)
route=base[a:b]
anchor=route.find(' const targetSkip=Math.max(0,targetShift);')
start=route.rfind(' outer:{',0,anchor) if anchor>=0 else -1
if start<0: raise SystemExit('v3.29 outer engine start missing')
end=balanced_block_end(route,start)
if end<0: raise SystemExit('v3.29 outer engine end missing')
old_engine=route[start:end]
if 'occurrencePlans' not in old_engine: raise SystemExit('unexpected v3.29 engine block')
route=route[:start]+new_engine+route[end:]

# Insert only the v3.30 multi-episode renderer before the legacy renderer.
out_anchor=" const lockNames=best.lockRawSlots.length?best.lockRawSlots.map(x=>`#${x.rawNo} ${x.name}`).join(' + '):best.lockIds.map(id=>nm(id)).join(' + ');"
pos=route.find(out_anchor)
if pos<0: raise SystemExit('legacy output anchor missing')
if 'best.multiEpisodes&&best.multiEpisodes.length' not in route:
    route=route[:pos]+output_insert+route[pos:]

# Route sanity: the old occurrence-tail engine must be gone and the new engine must be self-contained.
if 'function occurrencePlans(want)' in route: raise SystemExit('old v3.29 engine tail remains')
for token in ['function makeEpisodes()','function composeRoutes(','function validateMulti(','best.multiEpisodes']:
    if token not in route: raise SystemExit('new route token missing: '+token)

prefix=base[:a]; suffix=base[b:]
out=prefix+route+suffix

# Hard guard: outside showDaoPullRouteV290 is byte-for-byte the transformed v3.29 base.
oa,ob=bounds(out)
if out[:oa] != prefix or out[ob:] != suffix:
    raise SystemExit('REGRESSION: code outside daomai route function changed')
for token in ['FileReader','JSON.parse','localStorage','addEventListener','type="file"','세이브','불러오기']:
    if (prefix+suffix).count(token)!=(out[:oa]+out[ob:]).count(token):
        raise SystemExit('REGRESSION save/load token changed: '+token)

DST.write_text(out,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.31','file':'Nangman_Integrated_Simulator_v3_31.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md'); s=r.read_text(encoding='utf-8')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.31',s); r.write_text(s,encoding='utf-8')
if '<title>낭만강호 통합 시뮬레이터 v3.31</title>' not in out[:10000]: raise SystemExit('title mismatch')

# REAL JS syntax validation. This intentionally uses \b, not the broken literal \\b regex from older builders.
scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',out,re.I|re.S)
if not scripts: raise SystemExit('no scripts found for syntax validation')
checked=0
for i,js in enumerate(scripts):
    if not js.strip(): continue
    p=Path(f'/tmp/v331_app_{i}.js'); p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
    checked+=1
if checked<1: raise SystemExit('no non-empty scripts validated')
print(f'built v3.31: balanced route-only replacement; save/load outside route preserved; JS scripts checked={checked}')
