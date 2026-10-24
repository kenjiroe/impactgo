# สถานะโครงการ (อัปเดต 25 ต.ค. 2026)

## ทำเสร็จแล้ว
- ท่อข้อมูล 3 แหล่ง: IMPACT (HTML), ThaiTicketMarket (HTML), ThailandExhibition (API)
- ฐานข้อมูล 44 งานที่ใช้งาน · คิวรอตรวจ 0 · audit log ทุกการแก้
- หน้าเว็บ: 8 สัปดาห์ + heatmap (กดวันที่ได้) + ตัวกรอง + สัปดาห์นำทาง + งานยาว
- ชั้นวันหยุด: วันหยุดราชการ/วันสำคัญ + ป้ายหยุดยาว + ใช้ถ่วงคะแนน
- `.ics` ต่อรายการ + ทั้งชุด · ปุ่ม Google Calendar one-click
- หน้า curator (localhost:8081): รวม/แยก/ยกเลิก + rebuild อัตโนมัติ
- Analytics แบบไม่ใช้คุกกี้ (GoatCounter code: `impactgo`)
- Deploy ขึ้น Netlify แล้ว (แต่ยังเป็น build เก่า — ดูด้านล่าง)
- เทสต์ 3 ชุดผ่าน (normalize / impact / ttm) ด้วย fixture คงที่

## ค้างอยู่ (ติดสิทธิ์/บัญชี)
1. **อัปโหลด build ใหม่** — `dist/impactgo-site.zip` → Netlify site `impactgo` → Deploys → ลากโฟลเดอร์ `site`
   ตรวจด้วย `bash ops/check_live.sh` ต้องได้ `MATCH`
2. **Auto-update** — ต้องมี GitHub repo แล้วเปิด Pages/Actions (workflow เตรียมไว้)
3. **ลบ site เก่า `kenjiro`** บน GoatCounter (ถ้าไม่ใช้)

## ตัวชี้วัดที่จะเริ่มนับเมื่อ deploy ใหม่
| ตัวชี้วัด | เกณฑ์ผ่าน (4 สัปดาห์) | ที่มา |
|---|---|---|
| page views | ~150 sessions/สัปดาห์ (ประมาณ) | GoatCounter |
| กด `ics` | ≥30 | GoatCounter events |
| กด `gcal` | ≥15 | GoatCounter events |
| มีคนขอรับ/ถามต่อ | ≥5 | นับมือ |

## ก้าวต่อไปตามแผน v0.5
- 26–30 ต.ค.: ตรวจข้อมูลรายวัน + แก้จุดที่คนหลุด
- 2–6 พ.ย.: soft launch (ส่งลิงก์ 10–20 คน)
- 5–8 พ.ย.: บททดสอบพีคจริง
- 9–20 พ.ย.: วัดผล
- 21 พ.ย.: ตัดสิน Go / โหมดส่วนตัว
