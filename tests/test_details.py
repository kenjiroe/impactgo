import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import details  # noqa: E402

FIXTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "event_detail.html")


def main():
    doc = open(FIXTURE, encoding="utf-8").read()
    d = details.extract_description(doc)
    # ต้องเอา og:description ตัวแรก (เฉพาะงาน) ไม่ใช่ generic ของเว็บ
    assert d.startswith("บ้านและสวนแฟร์ Living Festival 2026"), d
    assert "2569" in d and "generic" not in d
    # ลำดับ attribute กลับด้าน (content มาก่อน property) ก็ต้องจับได้
    assert details.extract_description('<meta content="สวัสดี งานแฟร์" property="og:description">') == "สวัสดี งานแฟร์"
    # fallback meta name=description + ตัด whitespace ยุบบรรทัด
    d2 = details.extract_description('<meta name="description" content="  a\n  b  ">')
    assert d2 == "a b", d2
    # ไม่มี meta = สตริงว่าง (ผู้เรียกเก็บ '' = ไม่ต้อง retry)
    assert details.extract_description("<html><body>x</body></html>") == ""
    print("PASS: details extraction")


if __name__ == "__main__":
    main()
