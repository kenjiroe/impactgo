#!/usr/bin/env bash
# ตรวจเว็บที่ deploy อยู่: ไม่มีของเก่าค้าง + ฟีเจอร์หลักอยู่ครบ
# (ห้าม grep -q ใน pipe ภายใต้ pipefail — SIGPIPE ทำให้ match กลายเป็นไม่เจอ)
set -euo pipefail
URL="${1:-https://kenjiroe.github.io/impactgo}"
BODY=$(curl -sL --max-time 25 "$URL/?v=$(date +%s)")
LIVE=$(printf '%s' "$BODY" | grep -o 'name="impactgo-build" content="[^"]*"' | sed 's/.*content="//;s/"$//' || true)
echo "live build : ${LIVE:-ไม่พบ build id — deploy ล้มเหลว?}"
count() { printf '%s' "$BODY" | grep -c "$1" || true; }
[ "$(count 'data-goatcounter=')" -ge 1 ] && echo "analytics: on" || { echo "analytics: off"; exit 1; }
fail=0
for pat in "บันทึกลงปฏิทิน" "Google Calendar" ">หน้างาน</a>" "impactgo.netlify" 'class="now"'; do
  n=$(count "$pat")
  if [ "$n" -gt 0 ]; then echo "ของเก่าค้าง: $pat ($n)"; fail=1; fi
done
for pat in '<p class="ttl"><a ' 'details class="evmore"' 'class="evcontact"' 'class="evimg"' 'class="ahead"' 'id="heat"'; do
  n=$(count "$pat")
  if [ "$n" -ge 1 ]; then echo "มี: $pat ($n)"; else echo "ขาด: $pat"; fail=1; fi
done
if [ "$fail" = 0 ]; then echo "PASS — live ตรงกับโค้ดปัจจุบัน"; fi
exit $fail
