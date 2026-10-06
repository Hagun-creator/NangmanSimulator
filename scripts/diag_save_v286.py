from pathlib import Path
import re, hashlib

def scripts(path):
    t=Path(path).read_text(encoding='utf-8')
    return re.findall(r'<script\b[^>]*>(.*?)</script>',t,re.I|re.S)

def report(path):
    ss=scripts(path)
    out=[f'FILE {path}',f'SCRIPTS {len(ss)}']
    for i,s in enumerate(ss):
        out.append(f'[{i}] len={len(s)} sha={hashlib.sha256(s.encode()).hexdigest()[:16]}')
        if any(k in s for k in ['sharedSave','saveFile','FileReader','addEventListener(\'change\'','addEventListener("change"','loadSave','handleSave']):
            out.append('  SAVE_RELATED')
            lines=s.splitlines()
            for j,l in enumerate(lines):
                if any(k in l for k in ['sharedSave','saveFile','FileReader','change','loadSave','handleSave','JSON.parse']):
                    out.append(f'  {j+1}: {l[:500]}')
    return '\n'.join(out)

text=report('Nangman_Integrated_Simulator_v2_84.html')+'\n\n'+report('Nangman_Integrated_Simulator_v2_85.html')+'\n'
Path('diag_save_v286.txt').write_text(text,encoding='utf-8')
