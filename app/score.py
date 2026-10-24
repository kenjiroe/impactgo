"""คำนวณระดับความคึกคักรายวัน + ช่วงชั่วโมงเสี่ยง"""
import datetime as dt
import json

TYPE_W = {
    "concert": 1.3, "public_fair": 1.2, "family": 1.2, "exam": 1.0,
    "sport": 1.0, "special": 0.9, "trade": 0.8, "congress": 0.6, "unknown": 0.7,
}

HOURS = {
    "concert": [("17:00", "19:30", "in"), ("21:30", "23:30", "out")],
    "public_fair": [("09:30", "11:00", "in"), ("19:30", "21:00", "out")],
    "family": [("09:30", "11:00", "in"), ("19:30", "21:00", "out")],
    "trade": [("08:30", "10:00", "in"), ("17:00", "18:30", "out")],
    "congress": [("08:00", "09:00", "in"), ("16:30", "18:00", "out")],
    "exam": [("07:00", "08:30", "in"), ("15:30", "17:00", "out")],
    "sport": [("16:00", "18:00", "in"), ("20:00", "21:30", "out")],
    "special": [("17:00", "19:00", "in"), ("21:00", "22:30", "out")],
    "unknown": [("16:00", "18:00", "in"), ("20:00", "21:30", "out")],
}


def level_of(raw: float) -> int:
    if raw < 0.1:
        return 0
    if raw < 2.5:
        return 1
    if raw < 4.4:
        return 2
    if raw < 7.5:
        return 3
    return 4


def recompute(con, start: dt.date, days: int = 70):
    hol = {r["date"]: r["kind"] for r in con.execute("SELECT date,kind FROM holiday")}
    for i in range(days):
        d = start + dt.timedelta(days=i)
        rows = con.execute(
            """SELECT e.id, e.title, e.category, e.hall_from, v.code AS venue_code,
                      v.building_weight, v.name_th
               FROM event_day ed
               JOIN event e ON e.id = ed.event_id
               JOIN venue v ON v.id = e.venue_id
               WHERE ed.date = ? AND e.status IN ('confirmed','tentative')
                 AND e.id NOT IN (SELECT event_id FROM review_queue
                                  WHERE reason='possible_duplicate' AND resolved_at IS NULL)""",
            (d.isoformat(),),
        ).fetchall()

        by_venue = {}
        for r in rows:
            w = TYPE_W.get(r["category"], 0.7) * float(r["building_weight"])
            cur = by_venue.get(r["venue_code"])
            if cur is None or w > cur["w"]:
                by_venue[r["venue_code"]] = {"w": w, "name": r["name_th"], "titles": []}
            by_venue[r["venue_code"]]["titles"].append(r["title"])

        n = len(by_venue)
        raw = sum(v["w"] for v in by_venue.values())
        if n > 1:
            raw *= min(1.3, 1 + 0.1 * (n - 1))
        if d.weekday() in (4, 5, 6) or hol.get(d.isoformat()) == "public":
            raw *= 1.15

        lvl = level_of(raw)
        headline = " + ".join(sorted({t for v in by_venue.values() for t in v["titles"]}))[:120] if rows else ""
        expl = json.dumps(
            {"buildings": [{"code": k, "name": v["name"], "score": round(v["w"], 2)} for k, v in by_venue.items()]},
            ensure_ascii=False,
        )
        con.execute(
            """INSERT INTO day_score (date,event_count,building_count,buildings,raw_score,level,headline,explanation,computed_at)
               VALUES (?,?,?,?,?,?,?,?,datetime('now'))
               ON CONFLICT(date) DO UPDATE SET event_count=excluded.event_count, building_count=excluded.building_count,
                 buildings=excluded.buildings, raw_score=excluded.raw_score, level=excluded.level,
                 headline=excluded.headline, explanation=excluded.explanation, computed_at=datetime('now')""",
            (d.isoformat(), len(rows), n, json.dumps(sorted(by_venue.keys())), round(raw, 2), lvl,
             headline, expl),
        )

        con.execute("DELETE FROM hour_risk WHERE date=?", (d.isoformat(),))
        if rows:
            seen = set()
            for cat in {r["category"] for r in rows}:
                for (a, b, direction) in HOURS.get(cat, HOURS["unknown"]):
                    if (a, b, direction) in seen:
                        continue
                    seen.add((a, b, direction))
                    con.execute(
                        "INSERT INTO hour_risk (date,time_from,time_to,direction,level,reason) VALUES (?,?,?,?,?,?)",
                        (d.isoformat(), a, b, direction, lvl, cat),
                    )
    con.commit()
