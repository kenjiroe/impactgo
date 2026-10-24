"""ทดสอบ parser ThaiTicketMajor ด้วย snapshot จริง"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.parse_ttm import parse_page  # noqa: E402


def main():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "ttm.html")
    assert os.path.exists(path), "ไม่พบ fixture ttm.html"
    evs = parse_page(open(path, encoding="utf-8").read())
    assert len(evs) >= 10, len(evs)
    stray = next(e for e in evs if "STRAY KIDS" in e["title"])
    assert stray["start"].isoformat() == "2027-01-16" and stray["end"].isoformat() == "2027-01-17"
    assert stray["venue_code"] == "ARENA"
    joji = next(e for e in evs if "JOJI" in e["title"])
    assert joji["venue_code"] == "EXHIBITION" and joji["hall_from"] == 5
    print(f"PASS: {len(evs)} ttm events")


if __name__ == "__main__":
    main()
