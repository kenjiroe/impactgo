# คู่มือนักพัฒนา (DEV)

> ระบบ static: Python มาตรฐาน + SQLite + HTML → GitHub Pages
> ไม่มี dependency ภายนอก ยกเว้น Chrome สำหรับเรนเดอร์ PNG

## 1. ภาพรวม

```
แหล่งข้อมูล 3 แหล่ง → parse → normalize → merge/dedupe → SQLite
   → คะแนนรายวัน → เว็บ static + .ics + การ์ดแชร์ → GitHub Pages
```

ผลลัพธ์ 3 ทาง: หน้าเว็บ (คนทั่วไป) · `.ics` (ปฏิทินมือถือ) · การ์ดภาพ (โซเชียล)

## 2. เริ่มใช้งาน

```bash
cd /Users/ken/impactgo
./run.sh                 # ดึงข้อมูล + สร้างเว็บ (~15 วิ)
./serve.sh               # http://localhost:8080
./admin.sh               # http://localhost:8081 (curator)
make test                # เทสต์ 3 ชุด
bash ops/check_live.sh   # เทียบ build ที่ deploy กับเครื่อง
```
ต้องมี Python 3.9+ (ใช้ `zoneinfo`) และ Chrome (สำหรับไอคอน/การ์ด)

## 3. โครงสร้างไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| `run.py` | orchestrator: ingest ทุกแหล่ง → holiday → score → assets → cards → build → print สรุป |
| `app/alert.py` | ตรวจสุขภาพท้ายรัน: fail 2 รอบติด / งานลด >30% → แจ้ง (state ที่ `data/alert_state.json`) |
| `app/fetch.py` | HTTP (urllib) + `fetch_curl` สำหรับโดเมนที่บล็อก UA + snapshot |
| `app/parse_impact.py` | parse ปฏิทินอิมแพ็ค (Joomla Event Booking) |
| `app/parse_ttm.py` | parse ThaiTicketMajor (การ์ด event) |
| `app/parse_exhibition.py` | เรียก Strapi API ของ ThailandExhibition |
| `app/normalize.py` | วันที่ไทย/พ.ศ., อาคาร/ฮอลล์, ราคา, `token_sim` |
| `app/db.py` | schema, upsert, dedupe helpers, review queue |
| `app/score.py` | คะแนน 0–4 + ช่วงชั่วโมงเสี่ยง |
| `app/holidays.py` | วันหยุดจาก Google ICS + cache 30 วัน |
| `app/build_site.py` | สร้าง `site/index.html` + `.ics` + `data.json` + `go/<ช่อง>/` landing วัดช่องทาง |
| `app/assets.py` | manifest, ไอคอน, service worker |
| `app/share_card.py` | การ์ด PNG รายสัปดาห์ (HTML→Chrome) |
| `app/curate.py` | ตรรกะ merge/keep/cancel + audit log |
| `app/details.py` | ดึงสรุปงานจากหน้างานจริง (og/meta description) ลง `event.description` |
| `admin/server.py` | หน้า curator (stdlib HTTP) |
| `db/schema.sql` | DDL + seed สถานที่/แหล่งข้อมูล |
| `tests/` | fixture HTML + เทสต์ parser/normalize |

## 4. Data flow โดยละเอียด

1. **Fetch**: `impact` 2–3 หน้า (`?start=24`), `ttm` 1 หน้า, `exhibition` API ทุกหน้า (`pagination[page]`)
2. **Snapshot**: เก็บ HTML/JSON ลง `data/snapshots/<วันที่>/` + hash (เก็บ 6 ไฟล์/หน้า/วัน)
3. **Parse**: คืน dict มาตรฐาน (ดูสัญญาด้านล่าง)
4. **Merge**: source_ref → identity hash → เทียบวัน+ความคล้ายชื่อ ≥0.6 → ถ้าไม่มั่นใจสร้างใหม่ + เข้า `review_queue`
5. **Score**: ต่ออาคาร (max type weight) × overlap × day factor (ศ/ส/อา/วันหยุด)
6. **Build**: SSR HTML (ไม่มี JS framework) + พับสัปดาห์ + heatmap
7. **Assets/Cards**: manifest/icons/sw + PNG 8 ใบ
8. **Deploy**: push → GitHub Actions (test → run → Pages)

### สัญญาข้อมูลของ adapter
```python
{
 "source_ref": str, "url": str, "title": str, "date_text": str,
 "start": date, "end": date, "venue_text": str, "venue_code": str,
 "hall_from": int|None, "hall_to": int|None, "category": str,
 "audience": str, "is_free": int|None, "price_min": int|None,
 "price_max": int|None, "status_raw": str
}
```
เพิ่มแหล่งใหม่ = เขียน `parse_x.py` คืน dict นี้ + เรียกใน `run.py` (ดู `parse_exhibition.py` เป็นตัวอย่าง)

## 5. ฐานข้อมูล

ตารางหลัก: `event`, `event_source`, `event_day`, `day_score`, `hour_risk`, `holiday`, `review_queue`, `change_log`

```sql
-- งานที่ยังใช้งาน
SELECT count(*) FROM event WHERE status!='cancelled';
-- งานที่มีปัญหาซ้ำ
SELECT * FROM review_queue WHERE resolved_at IS NULL;
-- คะแนนสัปดาห์นี้
SELECT date,level,event_count FROM day_score WHERE date>=date('now') ORDER BY date LIMIT 14;
```
กู้ backup: `sqlite3 data/impactgo.db ".backup data/impactgo.db.bak"`

## 6. การให้คะแนน

```
building_score = max(type_weight ของงานในอาคาร) × building_weight
raw = Σ building_score × overlap(1+0.1×(n-1), cap 1.3) × day_factor(1.15 ถ้า ศ/ส/อา/วันหยุด)
level: <0.1=0, <2.5=1, <4.4=2, <7.5=3, ≥7.5=4
```
แก้ที่ `app/score.py` (`TYPE_W`, `HOURS`, `level_of`) — หลังแก้ให้รัน `run.py` แล้วเทียบกับงานจริง 2–3 วันก่อนเชื่อ

## 7. หน้าเว็บ

- ทุกอย่างอยู่ใน `app/build_site.py` (CSS + HTML + JS เป็น string)
- `details.week` = พับสัปดาห์, **เปิดทุกสัปดาห์ด้วย `open` (SSR)** — ตัดการ์ดวันนี้/พรุ่งนี้ด้านบนแล้ว (26 ต.ค. 2026)
- heatmap: `.cell` → `#d-YYYY-MM-DD`, ซ่อนอัตโนมัติเมื่อ `innerWidth<640`
- ปุ่ม `i` → `#help` dialog; ปุ่มแชร์ → `navigator.share`
- แก้ CSS ระวัง: อย่าแทนบล็อกใหญ่ด้วย `str.replace` โดยไม่ตรวจว่าแมตช์ (เคยทำให้กฎหาย)

## 8. Env vars

| ตัวแปร | ใช้ที่ | ค่า |
|---|---|---|
| `GOATCOUNTER_CODE` | build_site | `impactgo` (ถ้าไม่ใส่ = ไม่มี analytics) |
| `SITE_URL` | build_site | `https://kenjiroe.github.io/impactgo` |
| `CHROME_BIN` | assets/share_card | macOS: path Chrome · CI: `/usr/bin/google-chrome` |
| `CI` | assets/share_card | เปิด `--no-sandbox` |
| `LINE_PUSH_TOKEN` | alert.notify | LINE Messaging API token — ไม่ตั้ง = แจ้งลง log อย่างเดียว |
| `LINE_PUSH_TO` | alert.notify | user ID ผู้รับ push |

## 9. Deploy

- **GitHub Pages** (หลัก): `.github/workflows/pages.yml` — cron `0 23,5 * * *` UTC = 06:00/12:00 ไทย
- **Netlify**: static redirect 301 → Pages (`deploy/netlify-redirect/_redirects`)
- **โดเมน**: `./deploy/set-domain.sh <domain>` แล้วทำตาม `deploy/custom-domain.md`
- ตรวจ: `bash ops/check_live.sh <url>`

## 10. เทสต์และ fixture

```bash
make test
```
- `tests/fixtures/impact.html`, `ttm.html` = snapshot จริง ใช้เทสต์แบบไม่ต่อเน็ต
- ถ้าหน้าเว็บต้นทางเปลี่ยนโครง: อัปเดต fixture + แก้ selector + รันเทสต์
- **อย่า** ให้เทสต์อ้าง snapshot สด (เคยพังเพราะหน้าเปลี่ยน)

## 11. Troubleshooting

| อาการ | สาเหตุ | แก้ |
|---|---|---|
| `ttm failed: 403` | โดเมนบล็อก UA | ใช้ `fetch_curl` (ห้ามใส่ `-A` Mozilla) |
| `parsed too few events` | selector เปลี่ยน | เปิด snapshot ล่าสุด เทียบ `parse_impact.py` |
| ไอคอน/การ์ดไม่เกิดบน CI | ไม่มี Chrome | ตั้ง `CHROME_BIN` + `CI=1` |
| Pages deploy 404 | ยังไม่เปิด Pages / source ไม่ใช่ Actions | Settings → Pages → GitHub Actions |
| analytics ไม่ขึ้น | ไม่ได้ส่ง `GOATCOUNTER_CODE` | เพิ่มใน workflow env |
| หน้าเว็บเก่าค้าง | service worker cache | เปลี่ยน build id (อัตโนมัติ) หรือ hard refresh |

## 12. Convention

- UI เป็นไทย วันที่ ISO ใน DB, แสดง `dd/mm`
- commit: `<area>: <สิ่งที่ทำ>` (เช่น `heatmap: compact cells`)
- ห้าม commit `data/`, `site/`, `dist/` (อยู่ใน `.gitignore`)
- ทุกการแก้ข้อมูลด้วยมือต้องลง `change_log`

## 13. Roadmap ที่ยังไม่ทำ

ดูฉบับรวม: [`docs/ROADMAP.md`](ROADMAP.md) — งาน dev ต่อช่องทาง + เงื่อนไข trigger (ทำก่อน launch / เฟส 2 หลัง Go 21 พ.ย. / ยังห้ามทำ)
