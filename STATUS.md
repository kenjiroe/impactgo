# สถานะโครงการ (อัปเดต 25 ต.ค. 2026)

## ทำเสร็จแล้ว
- ท่อข้อมูล 3 แหล่ง: IMPACT (HTML), ThaiTicketMarket (HTML), ThailandExhibition (API)
- ฐานข้อมูล 44 งานที่ใช้งาน · คิวรอตรวจ 0 · audit log ทุกการแก้
- หน้าเว็บ: 8 สัปดาห์ + heatmap (กดวันที่ได้) + ตัวกรอง + สัปดาห์นำทาง + งานยาว
- ชั้นวันหยุด: วันหยุดราชการ/วันสำคัญ + ป้ายหยุดยาว + ใช้ถ่วงคะแนน
- `.ics` ต่อรายการ + ทั้งชุด (มี VALARM เตือนล่วงหน้า 1 วัน) · webcal subscribe · Google Calendar one-click
- หน้า curator (localhost:8081): รวม/แยก/ยกเลิก + rebuild อัตโนมัติ
- การ์ดภาพแชร์รายสัปดาห์ 1080×1080 (8 ใบ) + ปุ่มดาวน์โหลด/แชร์ลิงก์
- PWA-lite: manifest + ไอคอน + service worker (network-first) + ปุ่มติดตั้งบนมือถือ
- ปุ่ม i → แผง "วิธีใช้งาน" (ESC/แตะพื้นหลังปิด, เปิดผ่าน #help ได้)
- พับสัปดาห์ (เปิดสัปดาห์นี้) + ขยาย/ย่อทั้งหมด + ปุ่มลอยกลับด้านบน
- heatmap กระชับ (31px/ช่อง) + ตัวเลขนับงาน + ป้ายเดือน + ปุ่มซ่อน/แสดง (ย่ออัตโนมัติบนมือถือ)
- ขอบเขต 12 สัปดาห์ (3 เดือน) — ครอบงาน ม.ค. 2027
- Analytics แบบไม่ใช้คุกกี้ (GoatCounter code: `impactgo`)
- Deploy หลัก: **GitHub Pages** — https://kenjiroe.github.io/impactgo (อัปเดตอัตโนมัติ 06:00/12:00)
- Netlify: 301 redirect → Pages (ทุก path คงเดิม)
- เทสต์ 5 ชุดผ่าน (normalize / impact / ttm / alert / exhibition) ด้วย fixture และ dict จำลอง API
- Alert เมื่อ scraper พัง: แหล่งเดียว fail 2 รอบติด / งานรวมลด >30% → LINE push (`app/alert.py`, env `LINE_PUSH_TOKEN`+`LINE_PUSH_TO` ไม่ตั้ง = ลง log)
- Landing วัดช่องทาง `/go/line`, `/go/fb`, `/go/dm` — นับ path ใน GoatCounter แล้วพาเข้าหน้าหลัก (launch-kit ใช้ลิงก์เหล่านี้แล้ว)
- ปรับหน้าเว็บเน้นอ่าน (26 ต.ค.): ตัดการ์ดวันนี้/พรุ่งนี้, ทุกสัปดาห์เปิดค่าเริ่มต้น, ตัดปุ่ม ics/Google Calendar เหลือลิงก์ "หน้างาน", เพิ่มสรุปรายละเอียดงานที่ดึงจากหน้างานจริง (`app/details.py`) — เกณฑ์วัดเปลี่ยนจาก ics/gcal → detail + `/go/*` ตาม `ops/metrics.md`
- การ์ดงานกด-ขยาย "อ่านรายละเอียดจากหน้างาน" — เนื้อเต็มจากกล่อง `.eb-description` (ข้อความล้วน ไม่เอารูป, `<details>` native ไม่ใช้ JS) ดึงเพิ่มทีละ 8 หน้า/รันจนครบ

## ค้างอยู่ (ติดสิทธิ์/บัญชี)
1. **เริ่ม soft launch** ตาม `ops/launch-kit.md` (DM 10 ร้าน → LINE → Facebook)
2. **ลบ site เก่า `kenjiro`** บน GoatCounter (ถ้าไม่ใช้)
3. **ตัดสินใจ custom domain** (ถ้าต้องการ URL ที่จำง่ายกว่า)

## ตัวชี้วัดที่จะเริ่มนับเมื่อ deploy ใหม่
| ตัวชี้วัด | เกณฑ์ผ่าน (4 สัปดาห์) | ที่มา |
|---|---|---|
| page views | ~150 sessions/สัปดาห์ (ประมาณ) | GoatCounter |
| กด `ics` | ≥30 | GoatCounter events |
| กด `gcal` | ≥15 | GoatCounter events |
| มีคนขอรับ/ถามต่อ | ≥5 | นับมือ |

## การตัดสินใจที่ปิดแล้ว
- โดเมน: **ใช้ https://kenjiroe.github.io/impactgo ไปก่อน** (ต.ค. 2026) — เมื่อพร้อมใช้ `./deploy/set-domain.sh <domain>`

## ก้าวต่อไปตามแผน v0.5
- 26–30 ต.ค.: ตรวจข้อมูลรายวัน + แก้จุดที่คนหลุด
- 2–6 พ.ย.: soft launch (ส่งลิงก์ 10–20 คน)
- 5–8 พ.ย.: บททดสอบพีคจริง
- 9–20 พ.ย.: วัดผล
- 21 พ.ย.: ตัดสิน Go / โหมดส่วนตัว
