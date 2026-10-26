"""สร้างเว็บ static + ไฟล์ .ics จากฐานข้อมูล"""
import datetime as dt
import html
import json
import os

from .db import ROOT

SITE = os.path.join(ROOT, "site")
GO_CHANNELS = ("line", "fb", "dm")
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
.hrow{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.infobtn{flex:0 0 auto;width:34px;height:34px;border-radius:50%;border:1px solid #666;background:transparent;color:#fff;font-family:Georgia,serif;font-style:italic;font-size:17px;line-height:1;cursor:pointer}
.infobtn:hover{background:#fff;color:#111}
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:40}
.help{position:fixed;z-index:41;left:50%;top:50%;transform:translate(-50%,-50%);width:min(92vw,460px);max-height:82vh;overflow:auto;background:#fff;border-radius:14px;box-shadow:0 20px 60px rgba(0,0,0,.3)}
.helphead{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid #e3e3dd;position:sticky;top:0;background:#fff}
.helphead h2{margin:0;font-size:16px}
.helpclose{font:inherit;font-size:22px;line-height:1;background:none;border:0;cursor:pointer;padding:2px 6px}
.helpbody{padding:12px 16px 18px;font-size:13px;color:#333}
.helpbody p{margin:0 0 9px}
header{background:#141414;color:#fff;padding:22px 0 18px;margin-bottom:14px}
header h1{margin:0;font-size:22px;letter-spacing:.2px}
header p{margin:6px 0 0;color:#bdbdbd;font-size:12.5px}
.pill{display:inline-block;font-size:11px;font-weight:700;padding:2px 8px;border-radius:99px;color:#111;background:var(--lv0)}
.pill.lv1{background:var(--lv1)}.pill.lv2{background:var(--lv2)}
.pill.lv3{background:var(--lv3);color:#fff}.pill.lv4{background:var(--lv4);color:#fff}
.heat{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:0 0 12px}
.heat h2{display:flex;justify-content:space-between;align-items:center;font-size:13px;margin:0 0 6px;color:var(--mut);font-weight:600}
.heatbtn{font:inherit;font-size:11px;padding:3px 9px;border-radius:99px;border:1px solid var(--line);background:#fff;color:#555;cursor:pointer}
.heat .months{display:flex;gap:5px;flex-wrap:wrap;margin:0 0 6px}
.heat .mchip{font-size:10.5px;color:#666;background:#f4f4ef;border:1px solid #e6e6de;border-radius:99px;padding:2px 8px}
.heat .mchip b{color:#141414}
.heat .grid[hidden],.heat .legend[hidden],.heat .months[hidden]{display:none}
.heat .grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:3px}
.heat .wd{font-size:9.5px;color:var(--mut);text-align:center;padding-bottom:1px}
.heat .cell{position:relative;height:31px;border-radius:5px;background:var(--lv0);font-size:11px;color:#333;display:flex;align-items:center;justify-content:center;text-decoration:none;font-weight:600}
.heat .cell .cnt{position:absolute;bottom:1px;right:3px;font-size:8px;font-weight:700;font-style:normal;opacity:.55;line-height:1}
.heat .cell.blank{background:transparent}
.heat .cell.lv1{background:var(--lv1)}.heat .cell.lv2{background:var(--lv2)}
.heat .cell.lv3{background:var(--lv3);color:#fff}.heat .cell.lv4{background:var(--lv4);color:#fff}
.heat .legend{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-top:7px;font-size:10.5px;color:var(--mut)}
.heat .dot{width:9px;height:9px;border-radius:3px;display:inline-block;background:var(--lv0)}
.heat .dot.lv1{background:var(--lv1)}.heat .dot.lv2{background:var(--lv2)}
.heat .dot.lv3{background:var(--lv3)}.heat .dot.lv4{background:var(--lv4)}
.sharerow{display:flex;gap:6px;flex-wrap:wrap;margin:2px 0 8px}
.sharebtn{display:inline-block;margin-right:0;cursor:pointer;font-family:inherit;font-size:12.5px;text-decoration:none;color:#141414;border:1px solid #141414;border-radius:99px;padding:8px 13px;background:#fff}
.filters{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px}
.filters button{font:inherit;font-size:12.5px;padding:8px 13px;min-height:38px;border-radius:99px;border:1px solid var(--line);
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
.ev .desc{font-size:12.5px;color:var(--mut);margin:4px 0 0;line-height:1.45;
display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.ev a{color:#1a5fb4;text-decoration:none;font-size:12.5px;padding:8px 11px;border:1px solid #dcdcd4;border-radius:8px;display:inline-flex;align-items:center;min-height:38px;background:#fbfbf8}
.ev .acts{margin-top:5px;display:flex;gap:12px;flex-wrap:wrap}
.none{color:var(--mut);font-size:13px;padding:4px 0}
.ahead{font-size:12px;color:var(--mut);margin:0 0 10px;padding:8px 10px;background:#fff;border:1px dashed var(--line);border-radius:8px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.ahead b{color:#333;margin-right:2px}
.ahead .chip{display:inline-flex;align-items:center;padding:4px 10px;border:1px solid var(--line);border-radius:99px;background:var(--card);color:var(--ink);font-size:12px;text-decoration:none;line-height:1.4}
a.chip:hover{border-color:#a9a99c;background:#f2f2ec}
.ongoing{font-size:10.5px;color:var(--mut);margin:2px 0 3px;letter-spacing:.3px}
.ev.mini{background:#fbfbf8;border-style:dashed;padding:7px 10px}
.ev.mini .ttl{font-size:12.5px;font-weight:600}
section.week{scroll-margin-top:10px}
.day{scroll-margin-top:14px}
.day:target{background:#fff;outline:2px solid #141414;border-radius:10px;padding-left:8px;padding-right:8px;transition:background .2s}
.wctl{display:flex;gap:6px;margin:2px 0 6px}
.wctl button{font:inherit;font-size:11.5px;padding:5px 10px;border-radius:99px;border:1px solid var(--line);background:#fff;cursor:pointer;color:#444}
.widx{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 8px}
.widx a{font-size:11.5px;color:#444;border:1px solid var(--line);background:#fff;border-radius:99px;padding:3px 9px;text-decoration:none}
.tag.hol{background:#fde2e2;border:1px solid #e0a8a8;color:#7a2b2b}
.tag.obs{background:#eef0f4;border:1px solid #d5d9e0;color:#555}
.tag.lw{background:#fff3cd;border:1px solid #e5c97a;color:#6b5223}
.big{display:inline-block;font-size:10px;background:#f1e7d6;border:1px solid #d9c6a3;color:#6b5223;border-radius:5px;padding:0 5px;vertical-align:2px}
.week{scroll-margin-top:10px;margin:0 0 4px}
details.week>summary{list-style:none;cursor:pointer;display:flex;gap:10px;align-items:baseline;padding:12px 0;border-top:1px solid var(--line)}
details.week>summary::-webkit-details-marker{display:none}
.wtitle{font-size:13px;color:var(--mut);font-weight:600;white-space:nowrap}
.wsum{font-size:11.5px;color:#8a8a82;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0}
.chev{margin-left:auto;font-size:12px;color:#999;transition:transform .15s}
details[open]>summary .chev{transform:rotate(180deg)}
.totop{position:fixed;right:16px;bottom:18px;width:44px;height:44px;border-radius:50%;border:1px solid #141414;background:#141414;color:#fff;font-size:18px;cursor:pointer;z-index:30;box-shadow:0 6px 18px rgba(0,0,0,.2)}
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
            "BEGIN:VALARM",
            "TRIGGER:-PT15H",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{ics_escape('พรุ่งนี้มีงาน: ' + e['title'])}",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines))


def build_go_pages(goat=""):
    """landing วัดช่องทาง /go/<ช่อง>/ — นับ path ใน GoatCounter (no-JS pixel) แล้วพาเข้าหน้าหลัก (docs/ROADMAP.md #2)"""
    for slug in GO_CHANNELS:
        d = os.path.join(SITE, "go", slug)
        os.makedirs(d, exist_ok=True)
        pixel = '<img hidden alt="" src="https://%s.goatcounter.com/count?p=/go/%s">' % (goat, slug) if goat else ""
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(
                '<!doctype html><html lang="th"><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width,initial-scale=1">'
                "<title>ImpactGo — ปฏิทินงานเมืองทองธานี</title>"
                '<meta http-equiv="refresh" content="1;url=../../">'
                '</head><body><p style="font-family:system-ui,sans-serif">กำลังพาไปปฏิทิน… '
                '<a href="../../">เปิดเอง</a></p>' + pixel + "</body></html>"
            )


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

    hol = {r["date"]: dict(r) for r in con.execute("SELECT date,name,kind FROM holiday")}
    long_weekend = set()
    for ds, h in hol.items():
        if h["kind"] != "public":
            continue
        d0 = dt.date.fromisoformat(ds)
        if d0.weekday() == 4:
            long_weekend.update({(d0 + dt.timedelta(days=1)).isoformat(), (d0 + dt.timedelta(days=2)).isoformat()})
        if d0.weekday() == 0:
            long_weekend.update({(d0 - dt.timedelta(days=1)).isoformat(), (d0 - dt.timedelta(days=2)).isoformat()})

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

    def hbadge(ds):
        h = hol.get(ds)
        if not h:
            return '<span class="tag lw">หยุดยาว</span>' if ds in long_weekend else ""
        cls = "hol" if h["kind"] == "public" else "obs"
        label = "วันหยุด" if h["kind"] == "public" else "วันสำคัญ"
        extra = ' <span class="tag lw">หยุดยาว</span>' if ds in long_weekend else ""
        return '<span class="tag %s">%s · %s</span>%s' % (cls, label, esc(h["name"]), extra)

    parts = []
    parts.append('<!doctype html><html lang="th"><head><meta charset="utf-8">')
    parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    parts.append("<title>ปฏิทินงาน เมืองทองธานี — ImpactGo</title>")
    parts.append('<meta name="description" content="รวมงานล่วงหน้า %d สัปดาห์ในเมืองทองธานี '
                 'พร้อมระดับความคึกคักและรายละเอียดของแต่ละงาน">' % weeks)
    parts.append('<meta property="og:title" content="ปฏิทินงาน เมืองทองธานี">')
    parts.append('<meta property="og:description" content="งานล่วงหน้า %d สัปดาห์ + ระดับความคึกคัก">' % weeks)
    parts.append('<meta name="theme-color" content="#141414">')
    parts.append('<link rel="manifest" href="manifest.json">')
    parts.append('<link rel="apple-touch-icon" href="apple-touch-icon.png">')
    parts.append('<meta name="apple-mobile-web-app-capable" content="yes">')
    parts.append('<meta name="apple-mobile-web-app-status-bar-style" content="black">')
    parts.append('<meta name="apple-mobile-web-app-title" content="ImpactGo">')
    build_id = "%s-%d" % (dt.datetime.now().strftime("%Y%m%d-%H%M"), len(evs))
    parts.append('<meta name="impactgo-build" content="%s">' % build_id)
    parts.append("<style>%s</style></head><body>" % CSS)
    parts.append(
        '<header><div class="wrap hrow"><div><h1>ปฏิทินงาน เมืองทองธานี</h1>'
        '<p>รวมงานล่วงหน้า %d สัปดาห์ · อัปเดต %s · ข้อมูลจากแหล่งสาธารณะ</p></div>'
        '<button class="infobtn" id="infobtn" type="button" aria-label="วิธีใช้งาน" aria-expanded="false" data-goatcounter-click="help">i</button>'
        '</div></header>'
        % (weeks, dt.datetime.now().strftime("%d/%m/%Y %H:%M"))
    )
    parts.append('<main class="wrap">')

    parts.append('<section class="heat" id="heat"><h2><span>ภาพรวม %d สัปดาห์</span>'
                 '<button type="button" id="heattoggle" class="heatbtn">ซ่อน</button></h2>' % weeks)
    months = []
    d0 = start
    while d0 < end:
        key = (d0.year, d0.month)
        if not months or months[-1][0] != key:
            months.append([key, 0, 0])
        months[-1][1] += 1
        if by_day.get(d0.isoformat()):
            months[-1][2] += 1
        d0 += dt.timedelta(days=1)
    parts.append('<div class="months">%s</div><div class="grid">' % "".join(
        '<span class="mchip">%s <b>%d</b> วันมีงาน</span>' % (TH_M[m[0][1]], m[2]) for m in months))
    for wd in TH_D:
        parts.append('<div class="wd">%s</div>' % wd)
    for _ in range(start.weekday()):
        parts.append('<div class="cell blank"></div>')
    d = start
    while d < end:
        info = days.get(d.isoformat(), {})
        lvl = int(info.get("level", 0) or 0)
        n = len(by_day.get(d.isoformat(), []))
        hname = (" · " + hol[d.isoformat()]["name"]) if d.isoformat() in hol else ""
        lw = " · หยุดยาว" if d.isoformat() in long_weekend else ""
        cnt = '<i class="cnt">%d</i>' % n if n >= 2 else ""
        if n:
            parts.append('<a class="cell lv%d" href="#d-%s" title="%d %s · ระดับ %d · %d งาน%s%s · กดเพื่อดูรายการ">'
                         '<span>%d</span>%s</a>'
                         % (lvl, d.isoformat(), d.day, TH_M[d.month], lvl, n, hname, lw, d.day, cnt))
        else:
            parts.append('<div class="cell lv%d" title="%d %s · ไม่มีงาน%s%s"><span>%d</span></div>'
                         % (lvl, d.day, TH_M[d.month], hname, lw, d.day))
        d += dt.timedelta(days=1)
    legend = "".join('<i class="dot lv%d"></i><span>%d %s</span>' % (i, i, LEVEL_TXT[i]) for i in range(5))
    parts.append('</div><div class="legend"><span>ระดับ:</span>%s<span style="margin-left:auto">กดวันที่เพื่อดูรายการ</span></div></section>' % legend)

    share_png = os.path.join(SITE, "share", "week-%02d.png" % today.isocalendar()[1])
    if os.path.exists(share_png):
        parts.append('<div class="sharerow"><a class="sharebtn" href="share/week-%02d.png" target="_blank" '
                     'data-goatcounter-click="share">ดาวน์โหลดการ์ดแชร์สัปดาห์นี้ (PNG)</a>'
                     '<button class="sharebtn" type="button" id="sharelink" data-goatcounter-click="share-link">แชร์ลิงก์</button></div>'
                     % today.isocalendar()[1])
    parts.append(
        '<div class="filters" role="group" aria-label="ตัวกรอง">'
        '<button data-f="all" aria-pressed="true">ทั้งหมด</button>'
        '<button data-f="concert" aria-pressed="false">คอนเสิร์ต</button>'
        '<button data-f="public_fair" aria-pressed="false">งานแสดงสินค้า</button>'
        '<button data-f="congress" aria-pressed="false">ประชุม</button>'
        '<button data-f="free" aria-pressed="false">ฟรี</button></div>'
    )

    ahead = con.execute(
        """SELECT title, start_date, end_date, category, detail_url FROM event
           WHERE status!='cancelled' AND start_date>=? ORDER BY start_date LIMIT 6""",
        (end.isoformat(),),
    ).fetchall()
    if ahead:
        chips = []
        for a in ahead:
            s = dt.date.fromisoformat(a["start_date"])
            e2 = dt.date.fromisoformat(a["end_date"])
            rng = s.strftime("%d/%m/%y") if s == e2 else "%s–%s" % (s.strftime("%d/%m/%y"), e2.strftime("%d/%m/%y"))
            t = a["title"] if len(a["title"]) <= 46 else a["title"][:45] + "…"
            label = "%s · %s · %s" % (CAT_TXT.get(a["category"], "อื่น ๆ"), t, rng)
            chip = '<span class="chip">%s</span>' % esc(label)
            if a["detail_url"]:
                chip = '<a class="chip" href="%s" target="_blank" rel="noopener" data-goatcounter-click="detail">%s</a>' % (
                    esc(a["detail_url"]), esc(label))
            chips.append(chip)
        parts.append('<div class="ahead"><b>ไกลกว่า %d สัปดาห์:</b>%s</div>' % (weeks, "".join(chips)))

    idx = []
    _c = start
    while _c < end:
        _ws = _c - dt.timedelta(days=_c.weekday())
        if not idx or idx[-1] != _ws:
            idx.append(_ws)
        _c = _ws + dt.timedelta(days=7)
    if idx:
        parts.append('<div class="wctl"><button type="button" id="expandall">ขยายทั้งหมด</button>'
                     '<button type="button" id="collapseall">ย่อทั้งหมด</button></div>')
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
        ev_days = [x for x in week_days if by_day.get(x.isoformat())]
        lvmax = max([int(days.get(x.isoformat(), {}).get("level", 0) or 0) for x in ev_days] or [0])
        first = by_day[ev_days[0].isoformat()][0]["title"] if ev_days else ""
        if ev_days:
            short = first if len(first) <= 34 else first[:33] + "…"
            wsum = "%d วันมีงาน · สูงสุดระดับ %d · %s" % (len(ev_days), lvmax, short)
        else:
            wsum = "ว่างทั้งสัปดาห์"
        parts.append('<details class="week" id="w%d" open><summary><span class="wtitle">สัปดาห์ที่ %d · %s</span>'
                     '<span class="wsum">%s</span><span class="chev">▾</span></summary>'
                     % (ws.isocalendar()[1], ws.isocalendar()[1], label, esc(wsum)))
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
            parts.append('<div class="dhead"><span class="pill lv%d">ระดับ %d · %s</span>%s<span class="win">%s</span>'
                         '<a class="up" href="#heat" aria-label="กลับไปภาพรวม">↑ ภาพรวม</a></div>'
                         % (lvl, lvl, LEVEL_TXT[lvl], hbadge(dd.isoformat()), esc(win)))
            starts = [e for e in items if e["start_date"] == dd]
            ongoing = [e for e in items if e["start_date"] < dd]
            if ongoing:
                parts.append('<div class="ongoing">กำลังจัดอยู่</div>')
                for e in ongoing:
                    acts = ('<div class="acts"><a href="%s" target="_blank" rel="noopener" '
                            'data-goatcounter-click="detail">หน้างาน</a></div>' % esc(e["detail_url"])) if e["detail_url"] else ""
                    parts.append(
                        '<article class="ev mini" data-tags="%s %s">'
                        '<p class="ttl">%s</p>'
                        '<div class="meta"><span>%s</span><span>ถึง %s</span></div>'
                        "%s</article>"
                        % (e["category"], "free" if e["is_free"] else "paid", esc(e["title"]),
                           esc(e["venue_name"]), e["end_date"].strftime("%d/%m"), acts)
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
                longb = ' <span class="big">งานยาว</span>' if (e["end_date"] - e["start_date"]).days >= 6 else ""
                desc = '<p class="desc">%s</p>' % esc(e["description"][:280]) if e.get("description") else ""
                acts = ('<div class="acts"><a href="%s" target="_blank" rel="noopener" '
                        'data-goatcounter-click="detail">หน้างาน</a></div>' % esc(e["detail_url"])) if e["detail_url"] else ""
                parts.append(
                    '<article class="ev" data-tags="%s">'
                    '<p class="ttl">%s%s</p>'
                    '<div class="meta"><span>%s</span><span>%s</span><span>%s</span></div>'
                    "%s%s</article>"
                    % (" ".join(tags), esc(e["title"]), longb, esc(e["venue_name"]), date_txt, esc(price), desc, acts)
                )
            if not starts and not ongoing:
                parts.append('<div class="none">— ไม่มีงาน —</div>')
            parts.append("</div></div>")
        if not any_event:
            parts.append('<div class="none">ว่างทั้งสัปดาห์</div>')
        parts.append("</details>")
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
        '<li>วันหยุด/วันสำคัญ: ปฏิทิน Google สาธารณะ (วันหยุดราชการไทย)</li>'
        '<li>งานรอตรวจ (อาจซ้ำ/ข้อมูลไม่ครบ): %d รายการ</li>'
        '<li>สรุปรายละเอียดงานดึงจากหน้าเว็บของผู้จัดโดยอัตโนมัติ</li>'
        '<li>การใช้งาน: นับ page view และการกดลิงก์ แบบไม่ใช้คุกกี้ ไม่ระบุตัวตน</li>'
        '<li>ติดตั้งบนมือถือ: iOS → แชร์ → เพิ่มไปที่หน้าจอโฮม · Android → เมนู → ติดตั้งแอป</li></ul></section>'
        % (dt.datetime.now().strftime("%d/%m/%Y %H:%M"), ", ".join(srcs), queued)
    )
    parts.append("</main>")
    parts.append('<button class="totop" id="totop" type="button" aria-label="กลับด้านบน" hidden>↑</button>')
    parts.append(('''<div class="overlay" id="overlay" hidden></div>
<div class="help" id="help" role="dialog" aria-modal="true" aria-labelledby="helptitle" hidden>
  <div class="helphead"><h2 id="helptitle">วิธีใช้งาน</h2>
    <button class="helpclose" id="helpclose" type="button" aria-label="ปิด">×</button></div>
  <div class="helpbody">
    <p><b>ปฏิทินนี้คืออะไร</b> — รวมงานล่วงหน้า %d สัปดาห์ในเมืองทองธานี จาก 3 แหล่ง (อิมแพ็ค, ไทยทิคเก็ตเมเจอร์, ไทยแลนด์เอ็กซิบิชั่น)</p>
    <p><b>ระดับ 0–4</b> — ประเมินความคึกคักจากขนาดอาคาร × ประเภทงาน × จำนวนงานซ้อน และวันหยุด <i>ไม่ใช่จำนวนคนจริง</i></p>
    <p><b>กดช่องวันที่</b> ในภาพรวม เพื่อกระโดดไปรายการของวันนั้น วันที่ไม่มีงานจะกดไม่ได้</p>
    <p><b>รายละเอียดงาน</b> — สรุปสั้นดึงจากหน้างานของผู้จัด กด "หน้างาน" เพื่ออ่านเต็มและตรวจข้อมูลล่าสุดก่อนเดินทาง</p>
    <p><b>ติดตั้งบนมือถือ</b> — iOS: แชร์ → เพิ่มไปที่หน้าจอโฮม · Android: เมนู → ติดตั้งแอป</p>
    <p><b>ข้อจำกัด</b> — ข้อมูลจากแหล่งสาธารณะ งานอาจเลื่อน/ยกเลิกได้ โปรดตรวจสอบกับผู้จัดก่อนเดินทาง</p>
  </div>
</div>''') % weeks)
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
        "const sl=document.getElementById('sharelink');"
        "if(sl){sl.addEventListener('click',async()=>{const url=location.href.split('#')[0];"
        "const data={title:'ปฏิทินงาน เมืองทองธานี',text:'งานล่วงหน้า 8 สัปดาห์ + ระดับคนแน่น',url};"
        "if(navigator.share){try{await navigator.share(data)}catch(e){}}"
        "else{try{await navigator.clipboard.writeText(url);sl.textContent='คัดลอกลิงก์แล้ว';}"
        "catch(e){window.prompt('คัดลอกลิงก์:',url)}}});}"
        "const ib=document.getElementById('infobtn'),hp=document.getElementById('help'),ov=document.getElementById('overlay'),hc=document.getElementById('helpclose');"
        "function openHelp(){hp.hidden=false;ov.hidden=false;ib.setAttribute('aria-expanded','true');hc.focus();}"
        "function closeHelp(){hp.hidden=true;ov.hidden=true;ib.setAttribute('aria-expanded','false');}"
        "if(ib){ib.addEventListener('click',openHelp);hc.addEventListener('click',closeHelp);ov.addEventListener('click',closeHelp);"
        "document.addEventListener('keydown',e=>{if(e.key==='Escape')closeHelp()});"
        "if(location.hash==='#help')openHelp();}"
        "const hb=document.getElementById('heattoggle'),hg=document.querySelector('.heat .grid'),hl=document.querySelector('.heat .legend'),hm=document.querySelector('.heat .months');"
        "if(hb){hb.addEventListener('click',()=>{const hide=!hg.hidden;hg.hidden=hide;if(hl)hl.hidden=hide;if(hm)hm.hidden=hide;hb.textContent=hide?'แสดง':'ซ่อน';});"
        "if(window.innerWidth<640){hg.hidden=true;if(hl)hl.hidden=true;if(hm)hm.hidden=true;hb.textContent='แสดง';}}"
        "const tt=document.getElementById('totop');"
        "if(tt){addEventListener('scroll',()=>{tt.hidden=scrollY<600},{passive:true});"
        "tt.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));}"
        "function openHash(){const h=location.hash;if(!h||h==='#help')return;const el=document.querySelector(h);if(!el)return;const d=el.closest('details');if(d)d.open=true;el.scrollIntoView();}"
        "addEventListener('load',openHash);addEventListener('hashchange',openHash);"
        "document.querySelectorAll('.widx a').forEach(a=>a.addEventListener('click',()=>{const t=document.querySelector(a.getAttribute('href'));if(t&&t.tagName==='DETAILS')t.open=true;}));"
        "const ea=document.getElementById('expandall'),ca=document.getElementById('collapseall');"
        "if(ea)ea.addEventListener('click',()=>document.querySelectorAll('details.week').forEach(d=>d.open=true));"
        "if(ca)ca.addEventListener('click',()=>document.querySelectorAll('details.week').forEach(d=>d.open=false));"
        "if('serviceWorker' in navigator){addEventListener('load',()=>navigator.serviceWorker.register('sw.js').catch(()=>{}))}"
        "</script></body></html>"
    )

    if goat:
        parts.insert(-1, '<script data-goatcounter="https://%s.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>' % goat)
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(parts))

    make_ics(evs, os.path.join(SITE, "events.ics"), "ปฏิทินงาน เมืองทองธานี")
    for e in evs:
        make_ics([e], os.path.join(SITE, "ics", "%s.ics" % e["id"]), e["title"])
    build_go_pages(goat)

    payload = [{
        "id": e["id"], "title": e["title"], "venue": e["venue_code"], "venue_name": e["venue_name"],
        "start": e["start_date"].isoformat(), "end": e["end_date"].isoformat(),
        "category": e["category"], "audience": e["audience"], "is_free": e["is_free"],
        "price_min": e["price_min"], "price_max": e["price_max"], "url": e["detail_url"],
    } for e in evs]
    with open(os.path.join(SITE, "data.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": dt.datetime.now().isoformat(), "events": payload}, f, ensure_ascii=False, indent=1)

    return len(evs)
