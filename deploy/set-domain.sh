#!/usr/bin/env bash
# เปลี่ยนโดเมนหลักใน workflow + netlify redirect
set -euo pipefail
[ $# -eq 1 ] || { echo "usage: $0 <domain>  เช่น ./deploy/set-domain.sh impactgo.com"; exit 1; }
D="$1"
cd "$(dirname "$0")/.."
python3 - "$D" <<'PY'
import sys, re
d=sys.argv[1]
p='.github/workflows/pages.yml'; t=open(p,encoding='utf-8').read()
t=re.sub(r'SITE_URL: https://[^\s]+', 'SITE_URL: https://%s' % d, t)
open(p,'w',encoding='utf-8').write(t)
p='deploy/netlify-redirect/_redirects'; t=open(p,encoding='utf-8').read()
t=re.sub(r'https://[^\s]+/:splat', 'https://%s/:splat' % d, t)
open(p,'w',encoding='utf-8').write(t)
print('updated to', d)
PY
