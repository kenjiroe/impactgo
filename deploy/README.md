# Deploy — 3 ทางเลือก (ไม่ต้องมีเซิร์ฟเวอร์)

เว็บเป็น **static** ทั้งหมด (`site/`) — ไม่มีฐานข้อมูลบนเซิร์ฟเวอร์ ไม่มี secret
สร้างใหม่ด้วย `./run.sh` แล้วอัปโหลดโฟลเดอร์ `site/`

## ทางที่ 1: Netlify (ง่ายที่สุด)
```bash
# ติดตั้งครั้งแรก: npm i -g netlify-cli && netlify login
./run.sh
netlify deploy --prod --dir=site
```
หรือลากโฟลเดอร์ `site` ไปวางที่ app.netlify.com/drop

## ทางที่ 2: Cloudflare Pages
- เชื่อม repo → Build command: `./run.sh` · Output directory: `site`
- ตั้ง cron ที่ Cloudflare Worker หรือใช้ GitHub Actions ด้านล่าง

## ทางที่ 3: GitHub Pages (มี workflow ให้แล้ว)
1. สร้าง repo แล้ว push โค้ดทั้งหมด
2. Settings → Pages → Source: **GitHub Actions**
3. workflow `.github/workflows/pages.yml` จะรัน:
   - ทุกวัน 06:00 และ 12:00 เวลาไทย (cron UTC `0 23,5 * * *`)
   - ทุกครั้งที่ push
   - รันเทสต์ก่อน build ทุกครั้ง

## Cron ในเครื่อง (ถ้าไม่ใช้ CI)
```
0 6,12 * * * cd /Users/ken/impactgo && ./run.sh >> data/cron.log 2>&1
```

## ข้อควรระวังตอนเปิดสาธารณะ
- ระบุชัดว่า "ไม่ใช่ข้อมูลทางการของอิมแพ็ค" (มีอยู่ในหน้า `/about` แล้ว)
- ไม่ republish รูปจากต้นทาง — ตอนนี้เว็บใช้ข้อความล้วน
- เคารพ rate limit: ดึงวันละ 2 ครั้งก็พอ
- TTM บล็อก UA บางแบบ — ถ้าย้ายไป CI ให้ตรวจว่ายังดึงได้ (ใช้ curl)
- ใส่ `robots.txt` ของเราเองถ้าไม่อยากให้ search engine index

## สิ่งที่ยังไม่มี (ต้องทำก่อนเปิดวงกว้าง)
- ระบบ login สำหรับหน้า curator (ตอนนี้ localhost เท่านั้น)
- แจ้งเตือนเมื่อ scraper พัง (ดู `ops/runbook.md`)
