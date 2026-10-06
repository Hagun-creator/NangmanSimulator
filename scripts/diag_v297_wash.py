from pathlib import Path
s=Path('Nangman_Integrated_Simulator_v2_96.html').read_text(encoding='utf-8')
keys=['function washOnce','const washOnce','let washOnce','function rawNormal','function exchangeSequence','function stateFromSave']
out=[]
for k in keys:
    i=s.find(k)
    out.append(f'{k} => {i}')
    if i>=0:
        out.append('\n--- '+k+' ---\n'+s[i:i+9000])
Path('diag_v297_wash.txt').write_text('\n'.join(out),encoding='utf-8')
print('\n'.join(x for x in out if '=>' in x))
