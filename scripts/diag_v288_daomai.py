from pathlib import Path
import re
p=Path('Nangman_Integrated_Simulator_v2_87.html')
t=p.read_text(encoding='utf-8')
keys=['도맥법','천장','원시맥','교체맥','pity','raw','damai','daomai','도법']
lines=t.splitlines()
out=[]
for i,l in enumerate(lines):
    if any(k.lower() in l.lower() for k in keys):
        a=max(0,i-4); b=min(len(lines),i+5)
        out.append(f'\n--- {i+1} ---')
        for j in range(a,b): out.append(f'{j+1}: {lines[j][:2000]}')
Path('diag_v288_daomai.txt').write_text('\n'.join(out),encoding='utf-8')
print('matches',len(out))
