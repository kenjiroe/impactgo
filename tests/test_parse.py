"""ทดสอบ parser ด้วย snapshot จริง (ไม่ต้องต่อเน็ต)"""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.parse_impact import parse_page  # noqa: E402


def latest_snapshot():
    return os.path.join(os.path.dirname(__file__), "fixtures", "impact.html")


def main():
    html = open(latest_snapshot(), encoding="utf-8").read()
    evs = parse_page(html)
    assert len(evs) >= 20, len(evs)
    by_title = {e["title"]: e for e in evs}

    lykn = next(e for e in evs if "LYKN" in e["title"])
    assert lykn["venue_code"] == "ARENA", lykn["venue_code"]
    assert lykn["start"].isoformat() == "2026-10-23" and lykn["end"].isoformat() == "2026-10-25"
    assert lykn["category"] == "concert"

    baan = next(e for e in evs if "บ้านและสวนแฟร์" in e["title"])
    assert baan["venue_code"] == "CHALLENGER"
    assert baan["end"].isoformat() == "2026-11-01"
    assert baan["is_free"] == 1

    rov = next(e for e in evs if "RoV" in e["title"])
    assert rov["venue_code"] == "EXHIBITION"

    for e in evs:
        assert e["start"] <= e["end"], e["title"]
        assert e["url"].startswith("https://www.impact.co.th/")

    print(f"PASS: {len(evs)} events, {len(by_title)} titles")


if __name__ == "__main__":
    main()
