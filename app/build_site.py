"""สร้างเว็บ static + ไฟล์ .ics จากฐานข้อมูล"""
import datetime as dt
import html
import json
import os
from urllib.parse import quote

from .db import ROOT

SITE = os.path.join(ROOT, "site")
TH_D = ["จ.", "อ.", "พ.", "พฤ.", "ศ.", "ส.", "อา."]
TH_M = ["", "ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
LEVEL_TXT = {0: "ว่าง", 1: "เบา", 2: "ปานกลาง", 3: "หนัก", 4: "หนักมาก"}
CAT_TXT = {
    "concert": "คอนเสิร์ต", "public_fair": "งานแสดงสินค้า", "trade": "งานเทรด",
    "congress": "ประชุม/สัมมนา", "exam": "งานสอบ", "sport": "กีฬา",
    "family": "ครอบครัว", "special": "อีเวนต์พิเศษ", "unknown": "อื่น ๆ",
}

CSS = """
:root{--bg:#f6f6f3;--card:#fff;--ink:#141414;--mut:#6b6b6b;--line:#e3e3dd;
--lv0:#d9d9d2;--lv1:#8fbf7a;--lv2:#e8c44a;--lv3:#e8933f;--lv4:#d9534f}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font-family:"Sarabun","Noto Sans Thai","Thonburi",system-ui,-apple-system,sans-serif;line-height:1.5}
.wrap{max-width:820px;margin:0 auto;padding:0 16px}
header{background:#141414;color:#fff;padding:22px 0 18px;margin-bottom:14px}
header h1{margin:0;font-size:22px;letter-spacing:.2px}
header p{margin:6px 0 0;color:#bdbdbd;font-size:12.5px}
.now{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0 0 12px}
@media(max-width:560px){.now{grid-template-columns:1fr}}
.ncard{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.ncard .k{font-size:11.5px;color:var(--mut);text-transform:uppercase;letter-spacing:.6px}
.ncard .t{font-size:15px;font-weight:700;margin:4px 0 6px}
.ncard .m{font-size:12.5px;color:var(--mut)}
.pill{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:99px;color:#111;background:var(--lv0)}
.pill.lv1{background:var(--lv1)}.pill.lv2{background:var(--lv2)}
.pill.lv3{background:var(--lv3);color:#fff}.pill.lv4{background:var(--lv4);color:#fff}
.heat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:0 0 14px}
.heat h2{font-size:13px;margin:0 0 8px;color:var(--mut);font-weight:600}
.heat .grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:4px}
.heat .wd{font-size:10px;color:var(--mut);text-align:center;padding-bottom:2px}
.heat a.cell{text-decoration:none}
.heat a.cell:hover{outline:2px solid #141414;outline-offset:1px}
.heat .cell{aspect-ratio:1;border-radius:5px;background:var(--lv0);font-size:10px;color:#333;
display:flex;align-items:flex-end;justify-content:center;padding:2px}
.heat .cell.blank{background:transparent}
.heat .cell.lv1{background:var(--lv1)}.heat .cell.lv2{background:var(--lv2)}
.heat .cell.lv3{background:var(--lv3);color:#fff}.heat .cell.lv4{background:var(--lv4);color:#fff}
.heat .legend{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:8px;font-size:11px;color:var(--mut)}
.heat .dot{width:10px;height:10px;border-radius:3px;display:inline-block;background:var(--lv0)}
.heat .dot.lv1{background:var(--lv1)}.heat .dot.lv2{background:var(--lv2)}
.heat .dot.lv3{background:var(--lv3)}.heat .dot.lv4{background:var(--lv4)}
.filters{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px}
.filters button{font:inherit;font-size:12.5px;padding:6px 11px;border-radius:99px;border:1px solid var(--line);
background:#fff;color:#333;cursor:pointer}
.filters button[aria-pressed="true"]{background:#141414;color:#fff;border-color:#141414}
.week{margin:0 0 14px}
.week h2{font-size:12.5px;color:var(--mut);margin:16px 0 6px;font-weight:600;letter-spacing:.3px}
.day{display:grid;grid-template-columns:56px 1fr;gap:10px;padding:10px 0;border-top:1px solid var(--line)}
.day .d{font-size:11px;color:var(--mut);text-align:center}
.day .d b{display:block;font-size:20px;color:var(--ink);line-height:1.1}
.dhead{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:4px}
.dhead .win{font-size:11px;color:var(--mut)}
.dhead .up{margin-left:auto;font-size:11px;color:#666;text-decoration:none}
.ev{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:9px 11px;margin-bottom:6px}
.ev .ttl{font-size:14px;font-weight:600;margin:0 0 2px}
.ev .meta{font-size:12px;color:var(--mut)}
.ev .meta span+span:before{content:" · "}
.ev a{color:#1a5fb4;text-decoration:none;font-size:12px}
.ev .acts{margin-top:5px;display:flex;gap:12px;flex-wrap:wrap}
.none{color:var(--mut);font-size:13px;padding:4px 0}
.ahead{font-size:12px;color:var(--mut);margin:0 0 10px;padding:8px 10px;background:#fff;border:1px dashed var(--line);border-radius:8px}
.ahead b{color:#333}
.ongoing{font-size:10.5px;color:var(--mut);margin:2px 0 3px;letter-spacing:.3px}
.ev.mini{background:#fbfbf8;border-style:dashed;padding:7px 10px}
.ev.mini .ttl{font-size:12.5px;font-weight:600}
section.week{scroll-margin-top:10px}
.day{scroll-margin-top:14px}
.day:target{background:#fff;outline:2px solid #141414;border-radius:10px;padding-left:8px;padding-right:8px;transition:background .2s}
.widx{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 8px}
.widx a{font-size:11.5px;color:#444;border:1px solid var(--line);background:#fff;border-radius:99px;padding:3px 9px;text-decoration:none}
.big{display:inline-block;font-size:10px;background:#f1e7d6;border:1px solid #d9c6a3;color:#6b5223;border-radius:5px;padding:0 5px;vertical-align:2px}
.about{margin:22px 0 10px;padding:14px;background:#fff;border:1px solid var(--line);border-radius:10px;font-size:12.5px;color:#444}
.about h3{margin:0 0 6px;font-size:13.5px}
.about ul{margin:6px 0 0 18px;padding:0}
footer{padding:18px 0 40px;color:var(--mut);font-size:11.5px;text-align:center}
"""


def esc(s):
    return html.escape(s or "", quote=True)


def ics_escape(s):
    return (s or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def make_ics(events, path, name="ImpactGo"):
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ImpactGo//TH//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{ics_escape(name)}", "X-WR-TIMEZONE:Asia/Bangkok"]
    stamp = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    for e in events:
        end = e["end_date"] + dt.timedelta(days=1)
        desc = f"{CAT_TXT.get(e['category'], '')} · {e['venue_name']} · ที่มา: {e['detail_url']}"
        lines += [
            "BEGIN:VEVENT",
            f"UID:{e['identity_hash']}@impactgo.local",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{e['start_date'].strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
            f"SUMMARY:{ics_escape(e['title'])}",
            f"LOCATION:{ics_escape(e['venue_name'])}",
            f"DESCRIPTION:{ics_escape(desc)}",
            f"URL:{e['detail_url'] or ''}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines))


def build(con, today: dt.date, weeks: int = 8):
    goat = os.environ.get("GOATCOUNTER_CODE", "").strip()
    os.makedirs(SITE, exist_ok=True)
    os.makedirs(os.path.join(SITE, "ics"), exist_ok=True)
    start = today
    end = today + dt.timedelta(days=weeks * 7)

    evs = con.execute(
        """SELECT e.*, v.code AS venue_code, v.name_th AS venue_name
           FROM event e JOIN venue v ON v.id=e.venue_id
           WHERE e.status IN ('confirmed','tentative') AND e.end_date>=? AND e.start_date<?
             AND e.id NOT IN (SELECT event_id FROM review_queue
                              WHERE reason='possible_duplicate' AND resolved_at IS NULL)
           ORDER BY e.start_date, e.title""",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    evs = [dict(r) for r in evs]
    for e in evs:
        e["start_date"] = dt.date.fromisoformat(e["start_date"])
        e["end_date"] = dt.date.fromisoformat(e["end_date"])

    days = {r["date"]: dict(r) for r in con.execute(
        "SELECT * FROM day_score WHERE date>=? AND date<?", (start.isoformat(), end.isoformat()))}
    hours = {}
    for r in con.execute("SELECT * FROM hour_risk WHERE date>=? AND date<? ORDER BY time_from",
                         (start.isoformat(), end.isoformat())):
        hours.setdefault(r["date"], []).append(r)

    by_day = {}
    for e in evs:
        d = max(e["start_date"], start)
        while d <= min(e["end_date"], end - dt.timedelta(days=1)):
            by_day.setdefault(d.isoformat(), []).append(e)
            d += dt.timedelta(days=1)

    def card(d):
        info = days.get(d.isoformat(), {})
        lvl = int(info.get("level", 0) or 0)
        items = by_day.get(d.isoformat(), [])
        t = items[0]["title"] if items else "ไม่มีงานในปฏิทิน"
        if len(items) > 1:
            t += " +%d งาน" % (len(items) - 1)
        return (
            '<div class="ncard"><div class="k">%s %d %s</div>'
            '<div class="t">%s</div>'
            '<div class="m"><span class="pill lv%d">ระดับ %d · %s</span></div></div>'
            % (TH_D[d.weekday()], d.day, TH_M[d.month], esc(t), lvl, lvl, LEVEL_TXT[lvl])
        )

    parts = []
    parts.append('<!doctype html><html lang="th"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append("<title>ปฏิทินงาน เมืองทองธานี — ImpactGo</title>")
    parts.append('<meta name="description" content="รวมงานล่วงหน้า 8 สัปดาห์ในเมืองทองธานี '
                 'พร้อมระดับความคึกคักและปุ่มเพิ่มลงปฏิทิน">')
    parts.append('<meta property="og:title" content="ปฏิทินงาน เมืองทองธานี">')
    parts.append('<meta property="og:description" content="งานล่วงหน้า 8 สัปดาห์ + ระดับความคึกคัก">')
    parts.append('<meta name="theme-color" content="#141414">')
    build_id = "%s-%d" % (dt.datetime.now().strftime("%Y%m%d-%H%M"), len(evs))
    parts.append('<meta name="impactgo-build" content="%s">' % build_id)
    parts.append("<style>%s</style></head><body>" % CSS)
    parts.append(
        '<header><div class="wrap"><h1>ปฏิทินงาน เมืองทองธานี</h1>'
        '<p>รวมงานล่วงหน้า %d สัปดาห์ · อัปเดต %s · ข้อมูลจากแหล่งสาธารณะ</p></div></header>'
        % (weeks, dt.datetime.now().strftime("%d/%m/%Y %H:%M"))
    )
    parts.append('<main class="wrap">')
    parts.append('<section class="now">%s%s</section>' % (card(today), card(today + dt.timedelta(days=1))))

    parts.append('<section class="heat" id="heat"><h2>ภาพรวม %d สัปดาห์</h2><div class="grid">' % weeks)
    for wd in TH_D:
        parts.append('<div class="wd">%s</div>' % wd)
    for _ in range(start.weekday()):
        parts.append('<div class="cell blank"></div>')
    d = start
    while d < end:
        info = days.get(d.isoformat(), {})
        lvl = int(info.get("level", 0) or 0)
        n = len(by_day.get(d.isoformat(), []))
        if n:
            parts.append('<a class="cell lv%d" href="#d-%s" title="%d %s · ระดับ %d · %d งาน · กดเพื่อดูรายการ">%d</a>'
                         % (lvl, d.isoformat(), d.day, TH_M[d.month], lvl, n, d.day))
        else:
            parts.append('<div class="cell lv%d" title="%d %s · ไม่มีงาน">%d</div>'
                         % (lvl, d.day, TH_M[d.month], d.day))
        d += dt.timedelta(days=1)
    legend = "".join('<i class="dot lv%d"></i><span>%d %s</span>' % (i, i, LEVEL_TXT[i]) for i in range(5))
    parts.append('</div><div class="legend"><span>ระดับ:</span>%s<span style="margin-left:auto">กดวันที่เพื่อดูรายการ</span></div></section>' % legend)

    parts.append(
        '<div class="filters" role="group" aria-label="ตัวกรอง">'
        '<button data-f="all" aria-pressed="true">ทั้งหมด</button>'
        '<button data-f="concert" aria-pressed="false">คอนเสิร์ต</button>'
        '<button data-f="public_fair" aria-pressed="false">งานแสดงสินค้า</button>'
        '<button data-f="congress" aria-pressed="false">ประชุม</button>'
        '<button data-f="free" aria-pressed="false">ฟรี</button></div>'
    )

    ahead = con.execute(
        """SELECT title, start_date, end_date FROM event
           WHERE status!='cancelled' AND start_date>=? ORDER BY start_date LIMIT 3""",
        (end.isoformat(),),
    ).fetchall()
    if ahead:
        items = []
        for a in ahead:
            s = dt.date.fromisoformat(a["start_date"])
            e2 = dt.date.fromisoformat(a["end_date"])
            rng = s.strftime("%d/%m/%y") if s == e2 else "%s–%s" % (s.strftime("%d/%m/%y"), e2.strftime("%d/%m/%y"))
            items.append("%s <span>(%s)</span>" % (esc(a["title"]), rng))
        parts.append('<div class="ahead"><b>ไกลกว่า %d สัปดาห์:</b> %s</div>' % (weeks, " · ".join(items)))

    idx = []
    _c = start
    while _c < end:
        _ws = _c - dt.timedelta(days=_c.weekday())
        if not idx or idx[-1] != _ws:
            idx.append(_ws)
        _c = _ws + dt.timedelta(days=7)
    if idx:
        parts.append('<nav class="widx" aria-label="ข้ามไปสัปดาห์">%s</nav>' % "".join(
            '<a href="#w%d">%s</a>' % (w.isocalendar()[1],
                                       ("สัปดาห์นี้" if w <= start else "%d %s" % (w.day, TH_M[w.month]))) for w in idx))

    cur = start
    while cur < end:
        ws = cur - dt.timedelta(days=cur.weekday())
        week_days = [ws + dt.timedelta(days=i) for i in range(7)]
        week_days = [x for x in week_days if start <= x < end]
        if not week_days:
            break
        we = week_days[-1]
        if ws == we:
            label = "%d %s" % (ws.day, TH_M[ws.month])
        elif ws.month == we.month:
            label = "%d–%d %s" % (ws.day, we.day, TH_M[ws.month])
        else:
            label = "%d %s – %d %s" % (ws.day, TH_M[ws.month], we.day, TH_M[we.month])
        parts.append('<section class="week" id="w%d"><h2>สัปดาห์ที่ %d · %s</h2>' % (ws.isocalendar()[1], ws.isocalendar()[1], label))
        any_event = False
        for dd in week_days:
            items = by_day.get(dd.isoformat(), [])
            if not items:
                continue
            any_event = True
            info = days.get(dd.isoformat(), {})
            lvl = int(info.get("level", 0) or 0)
            hs = hours.get(dd.isoformat(), [])
            def _mins(x):
                a, b = x.split(":")
                return int(a) * 60 + int(b)
            def _merge(items, direction):
                iv = sorted((_mins(h["time_from"]), _mins(h["time_to"])) for h in items if h["direction"] == direction)
                out = []
                for a, b in iv:
                    if out and a <= out[-1][1]:
                        out[-1] = (out[-1][0], max(out[-1][1], b))
                    else:
                        out.append((a, b))
                return ["%02d:%02d–%02d:%02d" % (a // 60, a % 60, b // 60, b % 60) for a, b in out]
            seg = []
            if _merge(hs, "in"):
                seg.append("เข้า " + ", ".join(_merge(hs, "in")))
            if _merge(hs, "out"):
                seg.append("ออก " + ", ".join(_merge(hs, "out")))
            win = (" · คนแน่น " + " | ".join(seg)) if seg else ""
            parts.append('<div class="day" id="d-%s">' % dd.isoformat())
            parts.append('<div class="d">%s<b>%d</b>%s</div><div>' % (TH_D[dd.weekday()], dd.day, TH_M[dd.month]))
            parts.append('<div class="dhead"><span class="pill lv%d">ระดับ %d · %s</span><span class="win">%s</span>'
                         '<a class="up" href="#heat" aria-label="กลับไปภาพรวม">↑ ภาพรวม</a></div>'
                         % (lvl, lvl, LEVEL_TXT[lvl], esc(win)))
            starts = [e for e in items if e["start_date"] == dd]
            ongoing = [e for e in items if e["start_date"] < dd]
            if ongoing:
                parts.append('<div class="ongoing">กำลังจัดอยู่</div>')
                for e in ongoing:
                    parts.append(
                        '<article class="ev mini" data-tags="%s %s">'
                        '<p class="ttl">%s</p>'
                        '<div class="meta"><span>%s</span><span>ถึง %s</span></div>'
                        '<div class="acts"><a href="ics/%s.ics" data-goatcounter-click="ics">บันทึกลงปฏิทิน</a>'
                        '<a href="%s" target="_blank" rel="noopener" data-goatcounter-click="gcal">Google Calendar</a>'
                        '<a href="%s" target="_blank" rel="noopener" data-goatcounter-click="detail">หน้างาน</a></div></article>'
                        % (e["category"], "free" if e["is_free"] else "paid", esc(e["title"]),
                           esc(e["venue_name"]), e["end_date"].strftime("%d/%m"), e["id"],
                           "https://calendar.google.com/calendar/render?action=TEMPLATE&text=%s&dates=%s/%s&location=%s" % (
                               quote(e["title"]), e["start_date"].strftime("%Y%m%d"),
                               (e["end_date"] + dt.timedelta(days=1)).strftime("%Y%m%d"), quote(e["venue_name"])),
                           esc(e["detail_url"]))
                    )
            for e in starts:
                tags = [e["category"], "free" if e["is_free"] else "paid"]
                if e["is_free"]:
                    price = "ฟรี"
                elif e["price_min"]:
                    price = "%s–%s บาท" % (format(e["price_min"], ","), format(e["price_max"], ","))
                else:
                    price = "ไม่ระบุราคา"
                if e["start_date"] == e["end_date"]:
                    date_txt = e["start_date"].strftime("%d/%m")
                else:
                    date_txt = "%s–%s" % (e["start_date"].strftime("%d/%m"), e["end_date"].strftime("%d/%m"))
                gday = (e["end_date"] + dt.timedelta(days=1)).strftime("%Y%m%d")
                gurl = ("https://calendar.google.com/calendar/render?action=TEMPLATE&text=%s"
                        "&dates=%s/%s&location=%s&details=%s") % (
                    quote(e["title"]), e["start_date"].strftime("%Y%m%d"), gday,
                    quote(e["venue_name"]), quote("ที่มา: ImpactGo · " + (e["detail_url"] or "")))
                longb = ' <span class="big">งานยาว</span>' if (e["end_date"] - e["start_date"]).days >= 6 else ""
                parts.append(
                    '<article class="ev" data-tags="%s">'
                    '<p class="ttl">%s%s</p>'
                    '<div class="meta"><span>%s</span><span>%s</span><span>%s</span></div>'
                    '<div class="acts"><a href="ics/%s.ics" data-goatcounter-click="ics">บันทึกลงปฏิทิน</a>'
                    '<a href="%s" target="_blank" rel="noopener" data-goatcounter-click="gcal">Google Calendar</a>'
                    '<a href="%s" target="_blank" rel="noopener" data-goatcounter-click="detail">หน้างาน</a></div></article>'
                    % (" ".join(tags), esc(e["title"]), longb, esc(e["venue_name"]), date_txt, esc(price),
                       e["id"], gurl, esc(e["detail_url"]))
                )
            if not starts and not ongoing:
                parts.append('<div class="none">— ไม่มีงาน —</div>')
            parts.append("</div></div>")
        if not any_event:
            parts.append('<div class="none">ว่างทั้งสัปดาห์</div>')
        parts.append("</section>")
        cur = ws + dt.timedelta(days=7)

    queued = con.execute("SELECT count(*) c FROM review_queue WHERE resolved_at IS NULL").fetchone()["c"]
    srcs = [r["name"] for r in con.execute(
        """SELECT DISTINCT s.name FROM event_source es JOIN source s ON s.id=es.source_id
           ORDER BY s.trust_rank""")]
    parts.append(
        '<section class="about"><h3>เกี่ยวกับข้อมูล</h3>'
        '<p>รวบรวมจากปฏิทินกิจกรรมของอิมแพ็ค (สาธารณะ) · เป็นข้อมูลเพื่อการวางแผน ไม่ใช่ข้อมูลทางการ</p>'
        '<ul><li>อัปเดตล่าสุด: %s</li>'
        '<li>ระดับ 0–4 ประเมินจากขนาดอาคาร × ประเภทงาน × จำนวนงานซ้อน (ไม่ใช่จำนวนคนจริง)</li>'
        '<li>วันที่ไม่แสดงในรายการ = ไม่มีงานในปฏิทิน</li>'
        '<li>งานอาจเลื่อน/ยกเลิกได้ — ตรวจสอบกับผู้จัดก่อนเดินทาง</li>'
        '<li>แหล่งข้อมูล: %s</li>'
        '<li>งานรอตรวจ (อาจซ้ำ/ข้อมูลไม่ครบ): %d รายการ</li>'
        '<li>การใช้งาน: นับ page view และคลิก .ics แบบไม่ใช้คุกกี้ ไม่ระบุตัวตน</li>'
        '<li>เพิ่มทั้งปฏิทิน: <a href="events.ics" data-goatcounter-click="ics-all">ดาวน์โหลด .ics</a></li></ul></section>'
        % (dt.datetime.now().strftime("%d/%m/%Y %H:%M"), ", ".join(srcs), queued)
    )
    parts.append("</main>")
    parts.append('<footer>ImpactGo · ข้อมูลจาก impact.co.th · ไม่ใช่ข้อมูลทางการของอิมแพ็ค</footer>')
    parts.append(
        "<script>"
        "const btns=[...document.querySelectorAll('.filters button')];"
        "btns.forEach(b=>b.addEventListener('click',()=>{"
        "btns.forEach(x=>x.setAttribute('aria-pressed',x===b));"
        "const f=b.dataset.f;"
        "document.querySelectorAll('.ev').forEach(el=>{"
        "const tags=el.dataset.tags.split(' ');"
        "el.style.display=(f==='all'||tags.includes(f))?'':'none';});"
        "document.querySelectorAll('.day').forEach(d=>{"
        "const evs=[...d.querySelectorAll('.ev')];"
        "d.style.display=evs.some(e=>e.style.display!=='none')?'':'none';});"
        "}));"
        "</script></body></html>"
    )

    if goat:
        parts.insert(-1, '<script data-goatcounter="https://%s.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>' % goat)
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

    make_ics(evs, os.path.join(SITE, "events.ics"), "ปฏิทินงาน เมืองทองธานี")
    for e in evs:
        make_ics([e], os.path.join(SITE, "ics", "%s.ics" % e["id"]), e["title"])

    payload = [{
        "id": e["id"], "title": e["title"], "venue": e["venue_code"], "venue_name": e["venue_name"],
        "start": e["start_date"].isoformat(), "end": e["end_date"].isoformat(),
        "category": e["category"], "audience": e["audience"], "is_free": e["is_free"],
        "price_min": e["price_min"], "price_max": e["price_max"], "url": e["detail_url"],
    } for e in evs]
    with open(os.path.join(SITE, "data.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": dt.datetime.now().isoformat(), "events": payload}, f, ensure_ascii=False, indent=1)

    return len(evs)
