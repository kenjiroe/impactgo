import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import normalize as N  # noqa: E402


def main():
    d = N.parse_date_text("16 ม.ค. 2570 - 17 ม.ค. 2570")
    assert d and d[0].isoformat() == "2027-01-16" and d[1].isoformat() == "2027-01-17"
    d = N.parse_date_text("23 ตุลาคม - 01 พฤศจิกายน 2569")
    assert d[0].isoformat() == "2026-10-23" and d[1].isoformat() == "2026-11-01"
    assert N.venue_code("อิมแพ็ค เอ็กซิบิชั่น ฮอลล์ 5, เมืองทองธานี") == "EXHIBITION"
    assert N.venue_code("อิมแพ็ค อารีน่า เมืองทองธานี") == "ARENA"
    assert N.hall_range("ฮอลล์ 5-6") == (5, 6)
    assert N.token_sim("บ้านและสวนแฟร์ Living Festival 2026", "บ้านและสวนแฟร์ LIVING FESTIVAL 2026") > 0.9
    assert N.token_sim("Thailand Mobile Expo 2026 & AI Expo 2026", "Thailand Mobile EXPO 2026") > 0.6
    # กฎ ARENA: งานที่อารีน่าแท็กแฟร์/ไม่ระบุ = คอนเสิร์ต (เคสจริง Maroon 5 Asia 2027) — อย่างอื่นไม่แตะ
    assert N.fix_category("public_fair", "ARENA") == "concert"
    assert N.fix_category("unknown", "ARENA") == "concert"
    assert N.fix_category("concert", "ARENA") == "concert"
    assert N.fix_category("trade", "ARENA") == "trade"
    assert N.fix_category("public_fair", "EXHIBITION") == "public_fair"
    print("PASS: normalize")


if __name__ == "__main__":
    main()
