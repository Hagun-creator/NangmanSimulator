from pathlib import Path
p=Path('scripts/build_v330.py')
s=p.read_text(encoding='utf-8')
old="start=route.find(' outer:{\\n // v3.29 occurrence-tail daomai/kamek engine.')\nend=route.find('\\n if(!best){',start)\nif start<0 or end<0: raise SystemExit('v3.29 engine block missing')"
new="anchor=route.find(' const targetSkip=Math.max(0,targetShift);')\nstart=route.rfind(' outer:{',0,anchor) if anchor>=0 else -1\nend=route.find('\\n if(!best){',anchor) if anchor>=0 else -1\nif start<0 or end<0: raise SystemExit('v3.29 engine block missing by code anchor')"
if old not in s: raise SystemExit('builder detection block missing')
s=s.replace(old,new,1)
exec(compile(s,'build_v330.py','exec'),{'__name__':'__main__'})
