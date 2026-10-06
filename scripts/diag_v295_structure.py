from pathlib import Path
p=Path('Nangman_Integrated_Simulator_v2_95.html')
s=p.read_text(encoding='utf-8')
keys=[
 'async function showDaoRawBeforeV288(){',
 'async function showDaoExchangeWindowV288(){',
 'function daoDeleteCandidatesV295',
 'function daoDeleteCandidatesV290',
 'function showDaoPullRouteV290',
 'DAO_V290_ROUTE_ROWS',
 'DAO_V290_WINDOW',
 'dao-pull-v295',
 'dao-pull-v294',
 'let DAO_V288_CACHE=null;',
 'async function analyzeFirstPityDaomai()'
]
out=[]
for k in keys:
    out.append(f'{k} => {s.find(k)}')
# also show snippets around exchange function and raw function boundaries
for label,k in [('raw','async function showDaoRawBeforeV288(){'),('exchange','async function showDaoExchangeWindowV288(){')]:
    i=s.find(k)
    if i>=0:
        out.append(f'--- {label} snippet ---')
        out.append(s[i:i+1800])
Path('diag_v295_structure.txt').write_text('\n'.join(out),encoding='utf-8')
print('\n'.join(out[:len(keys)]))
