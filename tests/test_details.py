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
    # og:image (hotlink รูปงาน)
    assert details.extract_image(doc) == "https://www.impact.co.th/images/event/baanlaesuan-2026-banner.jpg"
    assert details.extract_image("<html><body>x</body></html>") == ""
    assert details.extract_image('<meta content="https://x.co/a.png" property="og:image">') == "https://x.co/a.png"

    # กล่องเนื้อหาเต็ม: จับข้อความใน .eb-description ตามความลึก DOM — ย่อหน้าคั่น \n
    full = details.extract_box(doc, "eb-description")
    assert "พื้นที่ปล่อยของสำหรับแบรนด์" in full and "ติดต่อผู้จัดงาน" in full, full
    assert "Price" in full and "ฟรี" in full
    assert "\n" in full and "Tel. 02 422 9999 Ext. 4133, 4175" in full, full
    # dt/dd ขึ้นบรรทัดเอง (แนวหัวข้อ/ค่าแบบหน้าต้นทาง)
    assert "\nDate\n23 ตุลาคม - 01 พฤศจิกายน 2569\nTime\n10:00-21:00\n" in "\n%s\n" % full, full
    # ปุ่มแชร์ของ Joomla (ในกล่อง) ต้องถูกตัดทิ้ง
    assert "Tweet" not in full and "Google Calendar" not in full and "Save Ical" not in full, full
    # ตัดข้อความหลังปิดกล่อง (eb-colorbox-map) และไม่มีเนื้อความจาก img/script
    assert "แผนผังฮอลล์" not in full
    assert "<" not in full and "&amp;" not in full  # tag ถูกกลืนหมด, entity ถูกแปลง
    # ไม่มีกล่องเป้า = ว่าง
    assert details.extract_box("<html><body>hi</body></html>", "eb-description") == ""
    # div ซ้อน: ปิด div นอกสุดก่อนจึงหยุด — ข้อความหลังกล่องต้องไม่ติดมา
    nested = '<div class="wrap"><div class="eb-description"><p>ในกล่อง</p></div><p>นอกกล่อง</p></div>'
    assert details.extract_box(nested, "eb-description") == "ในกล่อง"

    # แยกบล็อกติดต่อผู้จัดออกจากเนื้อหา — marker ถูกตัด (เรนเดอร์เป็นหัวข้อเอง)
    body, contact = details.split_contact(full)
    assert "พื้นที่ปล่อยของสำหรับแบรนด์" in body and "ติดต่อผู้จัด" not in body
    assert contact.startswith("AME IMAGINATIVE") and "Tel." in contact
    body2, contact2 = details.split_contact("ไม่มีบล็อกนี้")
    assert body2 == "ไม่มีบล็อกนี้" and contact2 == ""
    # marker ติดกับชื่อบริษัทในบรรทัดเดียว (ต้นทางจริงบางหน้า) — ตัดเฉพาะ marker ชื่อบริษัทต้องเหลือ
    b3, c3 = details.split_contact("เนื้อหางาน\nติดต่อผู้จัดงานAME CO.")
    assert b3 == "เนื้อหางาน" and c3 == "AME CO.", c3

    # contact_html: tel:+66 · เว็บ · Facebook · อีเมล กดได้จริง
    ch = details.contact_html(contact)
    assert 'href="tel:+6624229999"' in ch and "Ext. 4133, 4175" in ch, ch
    assert 'href="https://www.baanlaesuan.com"' in ch
    assert 'href="https://facebook.com/baanlaesuanmag"' in ch
    assert 'href="mailto:baanlaesuanweb@amarin.co.th"' in ch
    assert 'href="tel:+6624229999"' in ch
    # เบอร์ต่างประเทศที่พ่วงรหัสประเทศ → + นำหน้า · บรรทัด label หัวบล็อกถูกข้าม
    ch2 = details.contact_html("ติดต่อผู้จัดงาน\nTel. +86-20-29188153")
    assert 'href="tel:+862029188153"' in ch2 and "ติดต่อผู้จัดงาน" not in ch2, ch2
    # หมายเหตุ: บรรทัดที่ไม่ตรงรูปแบบไหน = ข้อความล้วน
    assert "<div>AME IMAGINATIVE CO., LTD.</div>" in ch
    print("PASS: details extraction")


if __name__ == "__main__":
    main()
