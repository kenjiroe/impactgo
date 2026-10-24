# แหล่งข้อมูลและสัญญาข้อมูล (Data Sources & Contracts)

> ตรวจสอบจริงเมื่อ 23–24 ต.ค. 2026 · ทุกแหล่งเป็นหน้าสาธารณะที่เปิดให้เข้าชม (ไม่ใช่ API ทางการ)

---

## 1. ทะเบียนแหล่งข้อมูล

| # | code | แหล่ง | ให้ข้อมูล | ความสด | วิธีดึง | ความน่าเชื่อถือ | ลำดับ |
|---|---|---|---|---|---|---|---|
| 1 | `impact` | [impact.co.th/th/visitors/event-calendar](https://www.impact.co.th/th/visitors/event-calendar) | ชื่อ, วัน, อาคาร, ราคา, ลิงก์งาน | ดี (ถึง 13 ธ.ค. 2026) | HTTP + HTML parse (2 หน้า) | สูง (เจ้าของสถานที่) | 1 |
| 2 | `ttm` | [m.thaiticketmajor.com/tag/Impact Arena](https://m.thaiticketmajor.com/tag/Impact%20Arena) | คอนเสิร์ต, วันแสดง, ผังบัตร | ดี | HTTP + HTML parse | สูง (ผู้ขายบัตร) | 2 |
| 3 | `ticketmaster` | [ticketmaster.co.th](https://ticketmaster.co.th) | คอนเสิร์ตที่ประกาศล่วงหน้านาน | ดี | HTTP/Playwright | สูง | 2 |
| 4 | `livenation` | [livenationtero.co.th](https://www.livenationtero.co.th) | คอนเสิร์ต Arena | กลาง | HTTP/Playwright | สูง | 2 |
| 5 | `exhibition` | [thailandexhibition.com/thai-trade-show-lists?place=อิมแพ็ค เมืองทองธานี](https://www.thailandexhibition.com/thai-trade-show-lists) | งานแสดงสินค้า + ผู้จัด | ดี | Playwright (หน้าเรนเดอร์ JS) | กลาง-สูง | 3 |
| 6 | `mtthani` | [muangthongthani.com/th/event-whats-on](https://www.muangthongthani.com/th/event-whats-on) | **ฮอลล์ + เวลาเปิด-ปิด** | **แย่ (ค้าง ส.ค.–ก.ย. 2026)** | HTTP + HTML parse | กลาง (ข้อมูลละเอียดแต่เก่า) | 4 (ใช้เฉพาะ hall/time) |
| 7 | `allthaievent` | [allthaievent.com](https://www.allthaievent.com) | งานรวมหลายศูนย์ | ไม่แน่นอน | HTTP | ต่ำ (หน้า venue ตอบ 404 บ่อย) | 5 |
| 8 | `facebook` | FB: IMPACTVenue, BangkokLand, สภ.ปากเกร็ด, เทศบาลนครปากเกร็ด | ประกาศปิดถนน/งานใหม่/ยกเลิก | สูง | **Manual** | กลาง | คู่ขนาน |
| 9 | `line_oa` | LINE OA `@impactvenue` | ข่าวสาร/ตารางงาน | สูง | **Manual** | กลาง | คู่ขนาน |
| 10 | `holiday` | ปฏิทินวันหยุดราชการไทย | วันหยุด (ใช้ถ่วงคะแนน) | ปีละครั้ง | CSV/static | สูง | — |
| 11 | `mrt` | [mrta.co.th — สายสีชมพูส่วนต่อขยาย](https://www.mrta.co.th/th/pink-line-extension-si-rat---muang-thong-thani) | เวลาเดินรถ 06:00–24:00, 2 สถานี | ต่ำ (ไม่เปลี่ยนบ่อย) | static | สูง | — |

---

## 2. ข้อเท็จจริงที่ตรวจแล้ว (ใช้เป็น baseline)

### 2.1 ปฏิทินอิมแพ็ค (`impact`)
- แสดง **25 งาน** ตั้งแต่ 23 ต.ค. ถึง 13 ธ.ค. 2026 (หน้าแรก 24 + หน้าสอง 1)
- มีตัวกรอง: สถานะ (ปัจจุบัน/เร็ว ๆ นี้/ที่ผ่านมา), เดือน, ปี (2566–2570), ประเภทงาน 9 แบบ, สถานที่ 10 แห่ง
- **ไม่ระบุฮอลล์** ในหน้ารวม — บอกเพียง "ศูนย์แสดงสินค้า อิมแพ็ค เมืองทองธานี"
- **ไม่มีงานหลัง 13 ธ.ค. 2026** ทั้งที่งานอย่าง Stray Kids World Tour 16–17 ม.ค. 2027 ประกาศขายบัตรแล้ว (21 ก.ย. 2026)
- **ฟีด RSS/Atom มีอยู่แต่ค้างปี 2023** (10 รายการแรก) → ห้ามใช้เป็นแหล่งหลัก
- **ไม่มี iCal export** (ทดสอบ endpoint แล้วได้ 404/500)
- ตัวกรองเดือน/ปีเมื่อเรียกผ่าน query string ไม่เปลี่ยนผลลัพธ์ (ต้องโต้ตอบผ่าน JS) → scraper ต้องดึงทั้ง 2 หน้าแล้วกรองเอง

### 2.2 เว็บน้องสาว (`mtthani`)
- ให้ข้อมูลที่ดีกว่าปฏิทินหลัก: **Venue: Hall 9-11 / Hall 7 / Hall 5-6** และ **Time: 09:30–19:30**
- แต่ข้อมูล **ค้างอยู่ที่งาน ส.ค.–ก.ย. 2026** → ใช้เป็น "พจนานุกรมฮอลล์" ไม่ใช่แหล่งสด

### 2.3 เว็บขายบัตร (`ttm`, `ticketmaster`, `livenation`)
- ครอบคลุมคอนเสิร์ตและงานบันเทิงได้ดีกว่าปฏิทิน โดยเฉพาะงานที่ประกาศล่วงหน้านาน
- ตัวอย่างที่พิสูจน์ช่องว่าง: **Stray Kids World Tour <RUN IT BANGKOK> 16–17 ม.ค. 2027 @ Impact Arena** (ขายบัตรผ่าน Ticketmaster TH / Live Nation Tero)
- ThaiTicketMajor ไม่มีแอปของตัวเอง — ใช้เว็บมือถือ/แอป Explorer

### 2.4 งานแสดงสินค้า (`exhibition`)
- หน้ารายการโหลดด้วย JS → ต้องใช้ Playwright หรือเรียก endpoint ย่อย
- ให้ข้อมูล "ผู้จัดงาน" ซึ่งมีประโยชน์ต่อการติดต่อและตรวจสอบ

### 2.5 ช่องทางที่ต้องทำมือ (`facebook`, `line_oa`)
- เป็นที่ประกาศ **งานใหม่/งานยกเลิก/การปิดถนน** ที่ไม่ลงเว็บ
- แนะนำให้ curator ตรวจวันละ 5 นาที (เช้า) และบันทึกผ่านหน้า admin

---

## 3. สัญญาข้อมูล (Field Contract)

| Field | จำเป็น | แหล่งที่เชื่อถือได้ (ตามลำดับ) | ค่า fallback |
|---|---|---|---|
| `title` | ✅ | manual > impact > ttm > exhibition | — |
| `start_date`, `end_date` | ✅ | impact > ttm > exhibition | จาก `date_text` ที่ parse ได้ |
| `venue_code` | ✅ | impact > ttm > exhibition | `OTHER` + flag |
| `hall` | ⬜ | mtthani > หน้ารายละเอียดงาน > manual | `null` + `hall_confidence=low` |
| `start_time`, `end_time` | ⬜ | ttm/mtthani > หน้ารายละเอียด | default ตามประเภท + `time_confidence=default` |
| `category` | ✅ | impact category > keyword rule | `unknown` |
| `audience` | ⬜ | category + keyword | `unknown` |
| `is_free`, `price_min/max` | ⬜ | impact (มีคำว่า "ฟรี"/ราคา) | `null` |
| `organizer` | ⬜ | exhibition > หน้ารายละเอียด | `null` |
| `source_url` | ✅ | ทุกแหล่ง | — |
| `last_verified_at` | ✅ | ระบบ + curator | `null` (แสดง "ยังไม่ยืนยัน") |

**หลักความขัดแย้ง:** ถ้าสองแหล่งไม่ตรงกัน → ใช้แหล่งลำดับสูงกว่า + เก็บอีกแหล่งไว้ใน `event_source` + ตั้ง `conflict=1` ให้ curator เห็น

---

## 4. กฎ Normalization ที่ scraper ต้องทำ

### 4.1 แมปชื่อสถานที่
```
"อิมแพ็ค อารีน่า" | "IMPACT Arena" | "Impact Arena"        → ARENA
"อิมแพ็ค ชาเลนเจอร์" | "IMPACT Challenger"                 → CHALLENGER
"ศูนย์แสดงสินค้า อิมแพ็ค เมืองทองธานี" | "IMPACT Exhibition Center" → EXHIBITION
"อิมแพ็ค ฟอรั่ม" | "IMPACT Forum"                          → FORUM
"ธันเดอร์โดม" | "Thunder Dome"                             → THUNDER
"ริมทะเลสาบ เมืองทองธานี" | "IMPACT Lakeside"              → LAKESIDE
"อิมแพ็ค สปีด พาร์ค" | "IMPACT Speed Park"                 → SPEEDPARK
"เดอะ พอร์ทอล" | "The Portal"                              → PORTAL
อื่น ๆ                                                     → OTHER
```

### 4.2 ดึงฮอลล์
```
regex: (Hall|ฮอลล์)\s*(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?
"Hall 5-6" → hall_from=5, hall_to=6
"Hall 11"  → hall_from=11, hall_to=11
```
ถ้าไม่พบ → `null` (ห้ามเดาจากขนาดงาน)

### 4.3 วันที่ไทย
- รูปแบบที่ต้องรองรับ: `23 ตุลาคม - 01 พฤศจิกายน 2569`, `23-25 ตุลาคม 2569`, `31 ตุลาคม 2569`
- แปลง พ.ศ. → ค.ศ. (`-543`) ก่อนเก็บ
- เก็บ `date_text` เดิมไว้ด้วยเพื่อ audit

### 4.4 ราคา
- `"ฟรี"` → `is_free=1`
- `"7,300 (VIP) / 6,300 / ..."` → `is_free=0`, `price_min=2800`, `price_max=7300`
- `"สิทธิ์เฉพาะลูกค้า..."` → `is_free=0`, `note=invite_only`

---

## 5. ช่องว่างที่รู้อยู่แล้ว และนโยบาย

| ช่องว่าง | ผลกระทบ | นโยบาย |
|---|---|---|
| งานใน Cosmo Bazaar / Beehive / Popular Walk / ตลาดรวมใจ | คนเดินในมอลล์ไม่ถูกนับ | เปิดช่อง "แจ้งงาน" + curator เพิ่มมือ + ติดป้าย `coverage=partial` |
| งานในโรงแรม (Novotel/ibis) และงานแต่ง | กลุ่มคนเล็กแต่ต่อเนื่อง | ไม่เก็บใน MVP (ยกเว้นมีคนแจ้ง) |
| จำนวนผู้เข้าร่วมจริง | ประมาณการเท่านั้น | ใช้ความจุอาคาร + ประเภทงาน + ป้าย "ประมาณการ" |
| งานเทรดที่จำกัดผู้เข้าชม | ร้านค้าอาจเตรียมของเกิน | เพิ่มฟิลด์ `audience=trade_only` และแสดงป้าย |
| งานที่ประกาศ <48 ชม. ก่อนจัด | ข้อมูลไม่ทัน | cron 2 รอบ/วัน + curator + alert "งานใหม่กระชั้น" |

---

## 6. มารยาทการดึงข้อมูลและข้อกฎหมาย

1. ตรวจ `robots.txt` ของทุกโดเมนก่อนเปิดใช้จริง และบันทึกผลไว้ใน repo
2. จำกัด **≤1 request / 2 วินาที / โดเมน**, timeout 20 วินาที, retry 3 ครั้ง ( exponential backoff )
3. ระบุ `User-Agent` ชัดเจนพร้อมช่องทางติดต่อ
4. cache 24 ชั่วโมง; หลีกเลี่ยงการยิงซ้ำเมื่อไม่มีการเปลี่ยนแปลง (ใช้ `ETag`/`Last-Modified` ถ้ามี)
5. **ไม่ republish รูปภาพหรือเนื้อหาทั้งก้อน** — ใช้ชื่องาน/วันเวลา/ลิงก์ + เครดิต
6. ไม่เก็บข้อมูลส่วนบุคคลจากหน้าเว็บ (ชื่อผู้จัด/เบอร์โทร เฉพาะที่เปิดเผยในฐานะติดต่อธุรกิจ)
7. แสดงข้อความ: "ข้อมูลรวบรวมจากแหล่งสาธารณะ อาจมีความคลาดเคลื่อน โปรดตรวจสอบกับผู้จัดก่อนเดินทาง"

> หมายเหตุ: ข้อ 6–7 เป็นแนวปฏิบัติ ไม่ใช่คำแนะนำทางกฎหมาย หากจะเปิดเป็นบริการสาธารณะควรให้ที่ปรึกษาตรวจอีกครั้ง

---

## 7. แผนตรวจสุขภาพแหล่งข้อมูล

| การตรวจ | ความถี่ | เกณฑ์ |
|---|---|---|
| HTTP status + ขนาดหน้า | ทุกครั้งที่ดึง | 200 และขนาด ±30% |
| จำนวนการ์ดที่ parse ได้ | ทุกครั้ง | ±30% ของค่าเฉลี่ย 7 วัน |
| selector ที่สำคัญยังเจอ | ทุกครั้ง | ครบ 5 selector หลัก |
| งานใหม่/หายไป | รายวัน | แจ้งเตือนถ้างานหาย >2 รายการ |
| ตรวจมือเทียบแหล่ง | สัปดาห์ละครั้ง | สุ่ม 10 งาน |
