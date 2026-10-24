# Runbook — 1 หน้า

## ทุกวัน
```bash
cd /Users/ken/impactgo
./run.sh                 # ดึง + คำนวณ + สร้างเว็บ
tail -20 data/cron.log   # ถ้าตั้ง cron
```
ดู 3 ตัวเลขจาก output:
- `events=` ต้องใกล้เคียงเดิม (±30%)
- `merged/new` ของ ttm/exhibition
- `levels:` ต้องมี 3 และ 4 ในสัปดาห์ที่มีงานใหญ่

## ตรวจสุขภาพเร็ว
```bash
sqlite3 data/impactgo.db "SELECT count(*) FROM event WHERE status!='cancelled';"
sqlite3 data/impactgo.db "SELECT count(*) FROM review_queue WHERE resolved_at IS NULL;"
sqlite3 data/impactgo.db "SELECT max(computed_at) FROM day_score;"
```

## อาการที่พบบ่อย
| อาการ | สาเหตุ | แก้ |
|---|---|---|
| `parsed too few events` | หน้า IMPACT เปลี่ยนโครง | เปิด `data/snapshots/` ล่าสุด เทียบ selector ใน `app/parse_impact.py` |
| `ttm failed: 403` | โดเมนบล็อก UA | ใช้ `fetch_curl` (ค่า default) อย่าใส่ `-A` |
| งานหายทั้งวัน | ต้นทางลบ/เลื่อน | ตรวจหน้าเว็บจริง + เพิ่มมือผ่าน SQL/curator |
| คิวรอตรวจเยอะ | ชื่อไทย–อังกฤษ | `./admin.sh` แล้วตัดสินทีละคู่ |
| ระดับพีคเฟ้อ | งานซ้ำไม่ถูก merge | ตรวจ `review_queue` และ `event_source` |

## กู้คืน
```bash
cp data/impactgo.db data/impactgo.db.bak.$(date +%F)
sqlite3 data/impactgo.db ".backup data/impactgo.db.bak"
# re-parse จาก snapshot โดยไม่ต้องยิงเน็ต (ต้องเขียนสคริปต์แยก)
```

## Curator
```bash
./admin.sh     # http://localhost:8081
```
- **รวม** เมื่อเป็นงานเดียวกัน (วัน+อาคารเดียวกัน ชื่อต่างภาษา)
- **เก็บไว้** เมื่อเป็นคนละงาน (เช่น ASEAN LED vs Billiards)
- ทุก action เขียน `change_log`

## Weekly
- เปิด `site/index.html` ดู 8 สัปดาห์ด้วยตาอีกรอบ
- ตรวจ `https://www.impact.co.th/th/visitors/event-calendar` เทียบ 10 งาน
- ดู `review_queue` ต้องเป็น 0
