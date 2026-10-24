"""วันหยุด/วันสำคัญ จากปฏิทิน Google สาธารณะ (ICS) — cache 30 วัน"""
import datetime as dt
import re

from . import fetch

ICS_URL = "https://calendar.google.com/calendar/ical/th.th%23holiday%40group.v.calendar.google.com/public/basic.ics"


def parse_ics(raw: str):
    raw = raw.replace("\r\n", "\n").replace("\n ", "")
    out = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", raw, re.S):
        d = re.search(r"DTSTART;VALUE=DATE:(\d{8})", block)
        s = re.search(r"SUMMARY:(.*)", block)
        if not (d and s):
            continue
        desc = re.search(r"DESCRIPTION:(.*)", block)
        name = s.group(1).strip().replace("\u200b", "")
        kind = "public" if desc and "วันหยุด" in desc.group(1) else "special"
        try:
            date = dt.date(int(d.group(1)[:4]), int(d.group(1)[4:6]), int(d.group(1)[6:]))
        except ValueError:
            continue
        out.append((date, name, kind))
    return out


def refresh(con, force=False, today=None):
    today = today or dt.date.today()
    row = con.execute("SELECT max(fetched) f FROM holiday").fetchone()
    last = row["f"] if row else None
    if not force and last:
        try:
            if (today - dt.date.fromisoformat(last)).days < 30:
                return 0
        except ValueError:
            pass
    _, data = fetch.fetch_curl(ICS_URL)
    items = [x for x in parse_ics(data.decode("utf-8", "ignore"))
             if today - dt.timedelta(days=60) <= x[0] <= today + dt.timedelta(days=500)]
    con.execute("DELETE FROM holiday WHERE date >= ?", ((today - dt.timedelta(days=60)).isoformat(),))
    for date, name, kind in items:
        con.execute(
            "INSERT INTO holiday (date,name,kind) VALUES (?,?,?) ON CONFLICT(date) DO UPDATE SET name=excluded.name,kind=excluded.kind",
            (date.isoformat(), name, kind),
        )
    con.execute("UPDATE holiday SET fetched=?", (today.isoformat(),))
    con.commit()
    return len(items)


def load(con):
    return {r["date"]: dict(r) for r in con.execute("SELECT date,name,kind FROM holiday")}
