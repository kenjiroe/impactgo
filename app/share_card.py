"""สร้างการ์ดภาพแชร์รายสัปดาห์ (HTML → PNG ผ่าน Chrome headless)"""
import datetime as dt
import html
import os
import subprocess

from .build_site import TH_D, TH_M, LEVEL_TXT
from .db import ROOT

CHROME = os.environ.get("CHROME_BIN") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CI = bool(os.environ.get("CI"))
OUT = os.path.join(ROOT, "site", "share")

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{width:1080px;height:1080px;background:#f6f6f3;color:#141414;
font-family:"Sarabun","Noto Sans Thai","Thonburi",sans-serif;padding:56px 64px;display:flex;flex-direction:column}
.top{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid #141414;padding-bottom:18px}
h1{font-size:44px;letter-spacing:.3px}
.sub{font-size:24px;color:#666;margin-top:6px}
.big{font-size:120px;font-weight:800;line-height:1;letter-spacing:-2px}
.big span{font-size:34px;font-weight:600;color:#666;letter-spacing:0}
.strip7{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin-top:18px}
.strip7 .c{border-radius:10px;text-align:center;padding:10px 4px;background:#d9d9d2}
.strip7 .c span{display:block;font-size:17px;color:#444}
.strip7 .c b{display:block;font-size:28px;line-height:1.1}
.strip7 .c.lv1{background:#8fbf7a}.strip7 .c.lv2{background:#e8c44a}
.strip7 .c.lv3{background:#e8933f;color:#fff}.strip7 .c.lv4{background:#d9534f;color:#fff}
.strip7 .c.lv3 span,.strip7 .c.lv4 span{color:#fff}
.list{margin-top:16px;flex:1;overflow:hidden}
.ongoing{font-size:19px;color:#555;margin-top:14px;padding:10px 14px;background:#fff;border:1px dashed #d8d8cf;border-radius:10px}
.row{display:flex;gap:18px;align-items:flex-start;padding:12px 0;border-bottom:1px solid #e0e0d8}
.d{width:132px;flex:0 0 132px;font-size:22px;color:#666}
.d b{display:block;font-size:36px;color:#141414;line-height:1.05}
.ev{font-size:24px;font-weight:600;line-height:1.25}
.venue{font-size:18px;color:#666;margin-top:2px}
.pill{display:inline-block;font-size:18px;font-weight:700;padding:3px 10px;border-radius:99px;background:#d9d9d2;margin-top:6px}
.lv1{background:#8fbf7a}.lv2{background:#e8c44a}.lv3{background:#e8933f;color:#fff}.lv4{background:#d9534f;color:#fff}
footer{display:flex;justify-content:space-between;align-items:center;border-top:3px solid #141414;padding-top:16px;font-size:22px;color:#444}
"""


def _card_html(week_start, rows, level, total, ongoing, strip):
    days = []
    for d, lvl, evs in rows:
        titles = "".join('<div class="ev">%s</div><div class="venue">%s</div>' % (html.escape(e["title"]), html.escape(e["venue_name"])) for e in evs[:2])
        days.append('<div class="row"><div class="d">%s<b>%d</b>%s</div><div>%s<span class="pill lv%d">ระดับ %d · %s</span></div></div>'
                    % (TH_D[d.weekday()], d.day, TH_M[d.month], titles, lvl, lvl, LEVEL_TXT[lvl]))
    end = week_start + dt.timedelta(days=6)
    rng = "%d %s – %d %s" % (week_start.day, TH_M[week_start.month], end.day, TH_M[end.month])
    strip_html = "".join('<div class="c lv%d"><span>%s</span><b>%d</b></div>' % (l, TH_D[d.weekday()], d.day) for d, l in strip)
    ong = ""
    if ongoing:
        ong = '<div class="ongoing">กำลังจัดในสัปดาห์นี้: %s</div>' % html.escape(
            ", ".join("%s (ถึง %s)" % (e["title"], e["end_date"][8:10] + "/" + e["end_date"][5:7]) for e in ongoing[:2]))
    return """<!doctype html><html lang="th"><head><meta charset="utf-8"><style>%s</style></head><body>
<div class="top"><div><h1>ปฏิทินงาน เมืองทองธานี</h1><div class="sub">สัปดาห์ที่ %d · %s</div></div>
<div style="text-align:right"><div class="big">%d<span> งาน</span></div><div class="sub">ระดับสูงสุด %d · %s</div></div></div>
%s<div class="strip7">%s</div><div class="list">%s</div>
<footer><span>impactgo.netlify.app</span><span>ข้อมูลจากแหล่งสาธารณะ · ไม่ใช่ข้อมูลทางการ</span></footer>
</body></html>""" % (CSS, week_start.isocalendar()[1], rng, total, level, LEVEL_TXT[level], ong, strip_html, "".join(days))


def build_cards(con, today: dt.date, weeks: int = 8):
    os.makedirs(OUT, exist_ok=True)
    made = []
    for w in range(weeks):
        ws = today - dt.timedelta(days=today.weekday()) + dt.timedelta(days=7 * w)
        we = ws + dt.timedelta(days=6)
        evs = [dict(r) for r in con.execute(
            """SELECT e.id, e.title, e.start_date, e.end_date, v.name_th AS venue_name
               FROM event e JOIN venue v ON v.id=e.venue_id
               WHERE e.status IN ('confirmed') AND e.end_date>=? AND e.start_date<=?
                 AND e.id NOT IN (SELECT event_id FROM review_queue WHERE reason='possible_duplicate' AND resolved_at IS NULL)
               ORDER BY e.start_date""", (ws.isoformat(), we.isoformat()))]
        if not evs:
            continue
        rows, maxlvl = [], 0
        ongoing = [e for e in evs if e["start_date"] < ws.isoformat() <= e["end_date"]]
        for i in range(7):
            d = ws + dt.timedelta(days=i)
            day_evs = [e for e in evs if e["start_date"] == d.isoformat()]
            day_all = [e for e in evs if e["start_date"] <= d.isoformat() <= e["end_date"]]
            if not day_all:
                continue
            sc = con.execute("SELECT level FROM day_score WHERE date=?", (d.isoformat(),)).fetchone()
            lvl = sc["level"] if sc else 1
            maxlvl = max(maxlvl, lvl)
            if day_evs:
                rows.append((d, lvl, day_evs))
        strip = []
        for i in range(7):
            d = ws + dt.timedelta(days=i)
            sc = con.execute("SELECT level FROM day_score WHERE date=?", (d.isoformat(),)).fetchone()
            strip.append((d, sc["level"] if sc else 0))
        if not rows:
            continue
        path_html = os.path.join(OUT, "week-%02d.html" % ws.isocalendar()[1])
        with open(path_html, "w", encoding="utf-8") as f:
            f.write(_card_html(ws, rows[:4], maxlvl, len({e["id"] for e in evs}), ongoing, strip))
        png = os.path.join(OUT, "week-%02d.png" % ws.isocalendar()[1])
        if os.path.exists(CHROME):
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", *(["--no-sandbox"] if CI else []),
                            "--user-data-dir=/tmp/igcard", "--screenshot=" + png,
                            "--window-size=1080,1080", "--virtual-time-budget=2500",
                            "file://" + path_html], capture_output=True)
        made.append((ws.isocalendar()[1], os.path.exists(png)))
    return made
