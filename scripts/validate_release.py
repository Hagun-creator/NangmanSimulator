from pathlib import Path
import re, sys, base64

if len(sys.argv) < 2:
    raise SystemExit('usage: validate_release.py vX.YY')
ver = sys.argv[1]
fn = 'Nangman_Integrated_Simulator_' + ver.replace('.', '_') + '.html'

BAD_TOKENS = ['\\n \\n', '\\n\\n', '/n /n', '/n/n']


def check_file(path: str):
    p = Path(path)
    if not p.exists():
        raise SystemExit('missing ' + path)
    t = p.read_text(encoding='utf-8')
    if f'<title>낭만강호 통합 시뮬레이터 {ver}</title>' not in t[:7000]:
        raise SystemExit('title mismatch: ' + path)
    m = re.search(r'const\s+EQUIPMENT_HTML_B64\s*=\s*"([A-Za-z0-9+/=]+)"\s*;', t)
    if m:
        inner = base64.b64decode(m.group(1)).decode('utf-8', 'replace')
        if "window.parent.scrollTo" not in inner or "q('#rresults')" not in inner:
            raise SystemExit('search-result return guard missing')
        for bad in BAD_TOKENS:
            if bad in inner:
                raise SystemExit('newline artifact remains: ' + repr(bad))


check_file(fn)
check_file('index.html')
readme = Path('README.md').read_text(encoding='utf-8')
if f'현재 사이트 버전: {ver}' not in readme:
    raise SystemExit('README version mismatch')
print('release validation OK', ver)
