from pathlib import Path
import re, subprocess, json

SRC=Path('Nangman_Integrated_Simulator_v3_36.html')
DST=Path('Nangman_Integrated_Simulator_v3_37.html')
if not SRC.exists(): raise SystemExit('v3.36 source missing')
text=SRC.read_text(encoding='utf-8')

# Version bump only.
text=text.replace('v3.36','v3.37').replace('v3_36','v3_37')
text=re.sub(r'(?<![0-9])3\.36(?![0-9])','3.37',text)

# Product name rename everywhere visible in the document.
text=text.replace('낭만강호 통합 시뮬레이터','낭만강호 시뮬레이터')

# Stable-root script version bump.
text=re.sub(r'<script id="stable-root-url-v336">.*?</script>\s*','',text,flags=re.S)
he=text.lower().find('</head>')
if he<0: raise SystemExit('head end missing')
head_script='''<script id="stable-root-url-v337">try{if(/Nangman_Integrated_Simulator_v3_37\\.html/i.test(location.pathname)){history.replaceState(null,'','/NangmanSimulator/');}}catch(e){}</script>\n'''
text=text[:he]+head_script+text[he:]

# Remove/hide drop-related navigation and its directly linked panel without touching equipment simulator logic.
# We intentionally do this at DOM level because older revisions used different ids/classes for the drop view.
body_end=text.lower().rfind('</body>')
if body_end<0: raise SystemExit('body end missing')
drop_cleanup=r'''<script id="remove-drop-ui-v337">
(function(){
  function isDropText(s){return /(?:드랍|드롭)/.test((s||'').replace(/\s+/g,' '));}
  function hidePanelByControl(el){
    const ids=[];
    for(const a of ['data-target','data-tab','data-pane','aria-controls']){
      const v=el.getAttribute&&el.getAttribute(a);if(v)ids.push(v.replace(/^#/,''));
    }
    const href=el.getAttribute&&el.getAttribute('href');if(href&&href.startsWith('#'))ids.push(href.slice(1));
    for(const id of ids){const p=document.getElementById(id);if(p)p.remove();}
  }
  function clean(){
    const candidates=[...document.querySelectorAll('button,a,[role="tab"],[data-tab],[data-target],.tab,.tab-btn,.nav-item,.menu-item')];
    for(const el of candidates){
      if(!isDropText(el.textContent))continue;
      hidePanelByControl(el);
      const li=el.closest('li');
      (li||el).remove();
    }
    // Remove standalone cards/sections whose heading itself is a drop feature heading.
    const heads=[...document.querySelectorAll('h1,h2,h3,h4,.section-title,.card-title')];
    for(const h of heads){
      if(!isDropText(h.textContent))continue;
      const box=h.closest('section,.card,.panel,.tab-pane');
      if(box)box.remove(); else h.remove();
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',clean,{once:true});else clean();
})();
</script>\n'''
text=text[:body_end]+drop_cleanup+text[body_end:]

# Guards: name changed, old visible name gone, drop cleanup installed, engine untouched markers retained.
if '낭만강호 통합 시뮬레이터' in text: raise SystemExit('old product name remains')
if '낭만강호 시뮬레이터 v3.37' not in text[:12000]: raise SystemExit('new title/version missing')
for tok in ['remove-drop-ui-v337','(?:드랍|드롭)','solutionCostFloor=Math.max(0,goalNeed*4)','BEAM_PER_CELL=8']:
    if tok not in text: raise SystemExit('v3.37 guard missing: '+tok)

DST.write_text(text,encoding='utf-8')
Path('latest.json').write_text(json.dumps({'version':'v3.37','file':'Nangman_Integrated_Simulator_v3_37.html'},ensure_ascii=False,indent=2),encoding='utf-8')
r=Path('README.md');s=r.read_text(encoding='utf-8')
s=s.replace('낭만강호 통합 시뮬레이터','낭만강호 시뮬레이터')
s=re.sub(r'현재 사이트 버전:\s*v?[0-9.]+','현재 사이트 버전: v3.37',s);r.write_text(s,encoding='utf-8')

scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',text,re.I|re.S)
if not scripts: raise SystemExit('no scripts')
checked=0
for i,js in enumerate(scripts):
    if not js.strip(): continue
    p=Path(f'/tmp/v337_{i}.js');p.write_text(js,encoding='utf-8')
    cp=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
    if cp.returncode: raise SystemExit(cp.stderr[:3000])
    checked+=1
if checked<1: raise SystemExit('no scripts checked')
print(f'built v3.37: renamed product and removed drop UI only; JS checked={checked}')
