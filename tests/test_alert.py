import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import alert  # noqa: E402


def main():
    # พลาดรอบแรกเงียบ · ครบ 2 รอบติดแจ้งครั้งเดียว · รอบถัดไปไม่สแปม
    st = {"sources": {}}
    assert alert.source_result(st, "ttm", True) is None
    assert alert.source_result(st, "ttm", False) is None
    m = alert.source_result(st, "ttm", False)
    assert m and "2 รอบติด" in m
    assert alert.source_result(st, "ttm", False) is None
    # หาย = แจ้งกลับมาทำงาน + streak รีเซ็ต
    m = alert.source_result(st, "ttm", True)
    assert m and "กลับมา" in m and st["sources"]["ttm"]["fail_streak"] == 0

    # จำนวนงานลด >30% เทียบ baseline → แจ้ง · ปกติ/รอบแรก/baseline <10 → เงียบ
    st = {"sources": {}, "last_total": 44}
    m = alert.total_result(st, 30)
    assert m and "44" in m and "30" in m
    assert st["last_total"] == 30
    assert alert.total_result(st, 31) is None
    assert alert.total_result({"sources": {}, "last_total": 8}, 3) is None
    assert alert.total_result({"sources": {}}, 30) is None

    # end_of_run: state ลงไฟล์รอดข้ามรอบ · ไฟล์พัง/หาย = เริ่มใหม่ไม่ตาย
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "state.json")
        _, msgs = alert.end_of_run(p, {"impact": False, "ttm": True, "exhibition": True})
        assert msgs == []  # fail รอบแรกบน state ใหม่ = ยังเงียบ
        st = json.load(open(p, encoding="utf-8"))
        assert st["sources"]["impact"]["fail_streak"] == 1
        assert st["sources"]["ttm"]["fail_streak"] == 0
        _, msgs = alert.end_of_run(p, {"impact": False, "ttm": True, "exhibition": True})
        assert len(msgs) == 1 and "2 รอบติด" in msgs[0]
        with open(p, "w", encoding="utf-8") as f:
            f.write("{broken")
        _, msgs = alert.end_of_run(p, {"impact": False, "ttm": True, "exhibition": True})
        assert msgs == []  # state ใหม่ → เริ่มนับ 1 ใหม่ ยังเงียบ
        _, msgs = alert.end_of_run(p, {"impact": False, "ttm": True, "exhibition": True})
        assert len(msgs) == 1 and "2 รอบติด" in msgs[0]

    print("PASS: alert rules")


if __name__ == "__main__":
    main()
