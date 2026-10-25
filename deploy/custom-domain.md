# ใช้โดเมนของตัวเองกับ GitHub Pages

## 1) ซื้อ/เตรียมโดเมน
- `.com` ประมาณ 350–500 บาท/ปี (Cloudflare Registrar, Namecheap)
- `.app` / `.dev` ต้อง HTTPS เท่านั้น (GitHub Pages รองรับ)
- `.in.th` ต้องใช้เอกสารนิติบุคคล/บุคคลไทย

## 2) ตั้ง DNS ที่ผู้ให้บริการโดเมน

**apex (โดเมนเปล่า เช่น impactgo.com)**
```
A     185.199.108.153
A     185.199.109.153
A     185.199.110.153
A     185.199.111.153
AAAA  2606:50c0:8000::153
AAAA  2606:50c0:8001::153
AAAA  2606:50c0:8002::153
AAAA  2606:50c0:8003::153
```
**www**
```
CNAME  www  →  kenjiroe.github.io
```

## 3) เปิดใน GitHub
1. https://github.com/kenjiroe/impactgo/settings/pages
2. **Custom domain** → พิมพ์โดเมน → Save
3. รอ DNS check ผ่าน (5 นาที – 24 ชม.)
4. ติ๊ก **Enforce HTTPS**

> หลังตั้งเสร็จ `kenjiroe.github.io/impactgo` จะ redirect ไปโดเมนใหม่อัตโนมัติ

## 4) อัปเดตโค้ดให้ลิงก์ชี้โดเมนใหม่
```bash
cd /Users/ken/impactgo
./deploy/set-domain.sh impactgo.com
git add -A && git commit -m "domain: switch to impactgo.com" && git push
```
สคริปต์จะแก้:
- `SITE_URL` ใน `.github/workflows/pages.yml` (ใช้กับลิงก์ webcal)
- เป้าหมายใน `deploy/netlify-redirect/_redirects`

## 5) อัปเดต Netlify redirect
```bash
cd deploy/netlify-redirect && zip -q /Users/ken/impactgo/dist/netlify-redirect.zip _redirects
```
แล้วอัปโหลด `dist/netlify-redirect.zip` ที่ Netlify → Deploys

## 6) ตรวจ
```bash
curl -sI https://impactgo.com | head -3          # 200 + server: GitHub.com
curl -sI https://www.impactgo.com | head -3      # 301 → apex
curl -sI https://impactgo.netlify.app/ | grep -i location   # 301 → โดเมนใหม่
bash ops/check_live.sh https://impactgo.com
```
