#!/usr/bin/env bash
# เทียบ build ที่ deploy อยู่กับไฟล์ในเครื่อง
set -euo pipefail
URL="${1:-https://impactgo.netlify.app}"
cd "$(dirname "$0")/.."
LOCAL=$(grep -o 'name="impactgo-build" content="[^"]*"' site/index.html | sed 's/.*content="//;s/"$//')
BODY=$(curl -sL --max-time 25 "$URL/?v=$(date +%s)")
LIVE=$(printf '%s' "$BODY" | grep -o 'name="impactgo-build" content="[^"]*"' | sed 's/.*content="//;s/"$//' || true)
echo "local : ${LOCAL}"
echo "live  : ${LIVE:-ไม่พบ build id (deploy เก่ามาก)}"
if [ -n "$LIVE" ] && [ "$LOCAL" = "$LIVE" ]; then
  echo "MATCH — deploy ตรงกับเครื่อง"
else
  echo "DIFF — ต้องอัปโหลด dist/impactgo-site.zip ใหม่"
fi
printf '%s' "$BODY" | grep -q 'data-goatcounter=' && echo "analytics: on" || echo "analytics: off"
