import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import parse_exhibition as X  # noqa: E402


def row(title, menu="", times=("2027-01-16T00:00:00.000Z", "2027-01-17T00:00:00.000Z")):
    return {"id": 33045, "attributes": {"title": title, "menu_of_event": menu,
                                        "event_time": list(times),
                                        "place": "อิมแพ็ค อารีน่า เมืองทองธานี"}}


def main():
    # world tour ต้องเป็น concert แม้ title ไม่มีคำว่า concert (บั๊ก 16 ม.ค. 2027)
    e = X._map(row("Stray Kids World Tour <RUN IT BANGKOK>"))
    assert e and e["category"] == "concert" and e["venue_code"] == "ARENA"
    assert e["start"].isoformat() == "2027-01-16" and e["end"].isoformat() == "2027-01-17"
    assert X._map(row("Dua Lipa Radical Optimism Tour"))["category"] == "concert"
    assert X._map(row("NuNew 1st Concert “DREAM CATCHER”"))["category"] == "concert"
    # หมวดจาก API ภาษาไทย / trade / งานแฟร์ทั่วไป
    assert X._map(row("งานประจำปี", menu="คอนเสิร์ต"))["category"] == "concert"
    assert X._map(row("งานแฟร์ใหญ่ประจำปี", menu="Trade Show"))["category"] == "trade"
    assert X._map(row("งานแสดงสินค้าทั่วไป"))["category"] == "public_fair"
    assert X._map(row("ไม่มีวันที่", times=())) is None
    print("PASS: exhibition category")


if __name__ == "__main__":
    main()
