from pathlib import Path
p=Path('Nangman_Integrated_Simulator_v2_87.html')
t=p.read_text(encoding='utf-8')

def cut(start_marker,end_marker):
    a=t.find(start_marker)
    if a<0:return f'MISSING {start_marker}'
    b=t.find(end_marker,a+len(start_marker))
    if b<0:b=min(len(t),a+30000)
    return t[a:b]
parts=[
'=== EXCHANGE ===\n'+cut('function exchangeSequence(','function exchangeNRows('),
'=== RAW2 ===\n'+cut('async function analyzeRawUntilSecondPurple()','function '),
'=== PITYDAO ===\n'+cut('async function analyzeFirstPityDaomai()','async function analyzePityShift()'),
'=== WASHONCE ===\n'+cut('function washOnce(','function '),
]
Path('diag_v288_functions.txt').write_text('\n\n'.join(parts),encoding='utf-8')
