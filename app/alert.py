"""ตรวจสุขภาพท้ายรัน + แจ้งเตือน — กฎตาม PLAN.md §8

state เก็บ data/alert_state.json (นอก git) เป็นหน่วยความจำข้ามรอบ:
- แหล่งเดียวกันพลาด 2 รอบติด → push ครั้งเดียว (รอบต่อ ๆ ไปเงียบ กันสแปม) · หายแล้วแจ้งว่ากลับมา
- จำนวนงานรวมลด >30% เทียบรอบสำเร็จก่อนหน้า (baseline ต้อง ≥10 งานจึงเทียบ)
push เข้า LINE ต่อเมื่อตั้ง env LINE_PUSH_TOKEN + LINE_PUSH_TO — ไม่ตั้ง = ลง log อย่างเดียว
ทุก path ต้องไม่ raise: alert พังห้ามดึง run ทั้งรันลงด้วย
"""
import json
import os
import urllib.request

LINE_API = "https://api.line.me/v2/bot/message/push"


def load_state(path):
    try:
        with open(path, encoding="utf-8") as f:
            st = json.load(f)
    except Exception:  # noqa: BLE001 — ไฟล์หาย/พัง = เริ่ม state ใหม่ ไม่มี alert ปลอม
        return {"sources": {}}
    if not isinstance(st, dict) or not isinstance(st.get("sources"), dict):
        return {"sources": {}}
    return st


def save_state(path, st):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=1)
    except OSError:
        pass


def source_result(st, name, ok):
    """อัปเดต fail_streak ของแหล่งเดียว — คืนข้อความแจ้ง (None = เงียบ)"""
    s = st["sources"].setdefault(name, {"fail_streak": 0})
    prev = s.get("fail_streak", 0)
    if ok:
        s["fail_streak"] = 0
        if prev >= 2:
            return f"[alert] {name}: กลับมาทำงานแล้ว (ก่อนหน้าพลาดติดกัน {prev} รอบ)"
        return None
    s["fail_streak"] = prev + 1
    if prev + 1 == 2:
        return f"[alert] {name}: ดึงข้อมูลพลาด 2 รอบติด — เปิด data/snapshots ล่าสุดเทียบ selector (ops/runbook.md)"
    return None


def total_result(st, total):
    """เทียบจำนวนงานรวมกับรอบสำเร็จก่อนหน้า — ลด >30% = แจ้ง"""
    prev = st.get("last_total")
    st["last_total"] = total
    if isinstance(prev, int) and prev >= 10 and total < prev * 0.7:
        pct = round((1 - total / prev) * 100)
        return f"[alert] จำนวนงานรวมลด {prev} → {total} (−{pct}%) — ตรวจ review_queue/ต้นทาง (ops/runbook.md)"
    return None


def end_of_run(state_path, sources, total=None):
    """sources: {"impact": bool, "ttm": bool, ...}; total: จำนวนงานรวมรอบนี้ (None = build ไม่สำเร็จ)
    คืน (state, รายการข้อความ)"""
    st = load_state(state_path)
    msgs = []
    for name, ok in sources.items():
        m = source_result(st, name, ok)
        if m:
            msgs.append(m)
    if total is not None:
        m = total_result(st, total)
        if m:
            msgs.append(m)
    save_state(state_path, st)
    return st, msgs


def notify(msgs):
    if not msgs:
        return
    text = "\n".join(msgs)
    print(text)
    token = os.environ.get("LINE_PUSH_TOKEN")
    to = os.environ.get("LINE_PUSH_TO")
    if not (token and to):
        print("[alert] (ตั้ง LINE_PUSH_TOKEN + LINE_PUSH_TO เพื่อรับแจ้งเข้า LINE)")
        return
    body = json.dumps({"to": to, "messages": [{"type": "text", "text": text[:4900]}]}).encode()
    req = urllib.request.Request(
        LINE_API, data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status != 200:
                print(f"[alert] line push http {r.status}")
    except Exception as exc:  # noqa: BLE001
        print(f"[alert] line push failed: {exc}")
