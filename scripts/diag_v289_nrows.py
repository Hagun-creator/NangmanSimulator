from pathlib import Path
p=Path('Nangman_Integrated_Simulator_v2_88.html')
t=p.read_text(encoding='utf-8')
def cut(a,b):
 s=t.find(a)
 if s<0:return 'MISSING '+a
 e=t.find(b,s+len(a))
 if e<0:e=min(len(t),s+40000)
 return t[s:e]
out=[]
for a,b in [
 ('function exchangeNRows(','function '),
 ('async function calcN','function '),
 ('function calcN','function '),
 ('function buildCandidates','function '),
 ('function calcCandidates','function '),
 ('function makeCandidate','function '),
]: out.append('\n=== '+a+' ===\n'+cut(a,b))
Path('diag_v289_nrows.txt').write_text('\n'.join(out),encoding='utf-8')
