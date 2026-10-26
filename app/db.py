"""SQLite helpers + upsert"""
import datetime as dt
import hashlib
import os
import sqlite3

from . import normalize as N

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "data", "impactgo.db")
SCHEMA = os.path.join(ROOT, "db", "schema.sql")


def connect(path: str = DB_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db(con):
    with open(SCHEMA, encoding="utf-8") as f:
        con.executescript(f.read())
    cols = {r[1] for r in con.execute("PRAGMA table_info(event)")}
    for c in ("description", "description_full"):
        if c not in cols:
            con.execute("ALTER TABLE event ADD COLUMN %s TEXT" % c)
    con.commit()


def source_id(con, code="impact"):
    row = con.execute("SELECT id FROM source WHERE code=?", (code,)).fetchone()
    return row["id"]


def venue_id(con, code):
    row = con.execute("SELECT id, building_weight FROM venue WHERE code=?", (code,)).fetchone()
    return row["id"], row["building_weight"]


def identity_hash(title, venue_code, start):
    key = f"{N.normalize_title(title)}|{venue_code}|{start.isoformat()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def upsert_event(con, ev, src_id, verified=None):
    vid, _ = venue_id(con, ev["venue_code"])
    ih = identity_hash(ev["title"], ev["venue_code"], ev["start"])
    con.execute(
        """
        INSERT INTO event (identity_hash,title,title_norm,venue_id,hall_from,hall_to,hall_confidence,
                           start_date,end_date,time_confidence,category,audience,is_free,price_min,price_max,
                           detail_url,status,confidence,last_verified_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(identity_hash) DO UPDATE SET
            title=excluded.title, title_norm=excluded.title_norm, venue_id=excluded.venue_id,
            hall_from=excluded.hall_from, hall_to=excluded.hall_to,
            start_date=excluded.start_date, end_date=excluded.end_date,
            category=excluded.category, audience=excluded.audience,
            is_free=excluded.is_free, price_min=excluded.price_min, price_max=excluded.price_max,
            detail_url=excluded.detail_url, status=excluded.status, updated_at=datetime('now')
        """,
        (ih, ev["title"], N.normalize_title(ev["title"]), vid, ev["hall_from"], ev["hall_to"],
         "high" if ev["hall_from"] else "low", ev["start"].isoformat(), ev["end"].isoformat(),
         "default", ev["category"], ev["audience"], ev["is_free"], ev["price_min"], ev["price_max"],
         ev["url"], "confirmed", "high" if ev["venue_code"] != "OTHER" else "medium", verified),
    )
    row = con.execute("SELECT id FROM event WHERE identity_hash=?", (ih,)).fetchone()
    eid = row["id"]
    con.execute(
        """INSERT OR IGNORE INTO event_source (event_id,source_id,source_ref,source_title,is_primary)
           VALUES (?,?,?,?,1)""",
        (eid, src_id, ev["source_ref"], ev["title"]),
    )
    con.execute("DELETE FROM event_day WHERE event_id=?", (eid,))
    d = ev["start"]
    while d <= ev["end"]:
        con.execute("INSERT INTO event_day (event_id,date) VALUES (?,?)", (eid, d.isoformat()))
        d += dt.timedelta(days=1)
    return eid


def purge_missing(con, src_id, seen_ids, today):
    """ทำเครื่องหมาย cancelled เฉพาะงานที่หายไปและยังไม่ถึงวันจัด"""
    rows = con.execute(
        """SELECT e.id, e.title, e.start_date FROM event e
           JOIN event_source es ON es.event_id=e.id
           WHERE es.source_id=? AND e.status='confirmed' AND e.start_date>=?""",
        (src_id, today.isoformat()),
    ).fetchall()
    n = 0
    for r in rows:
        if str(r["id"]) not in seen_ids:
            con.execute("UPDATE event SET status='tentative', updated_at=datetime('now') WHERE id=?", (r["id"],))
            con.execute(
                "INSERT INTO change_log (entity,entity_id,change_type,field,old_value,new_value,reason) VALUES (?,?,?,?,?,?,?)",
                ("event", r["id"], "update", "status", "confirmed", "tentative", "ไม่พบในต้นทางรอบล่าสุด"),
            )
            n += 1
    return n


def find_identity(con, ih):
    row = con.execute("SELECT id FROM event WHERE identity_hash=?", (ih,)).fetchone()
    return row["id"] if row else None


def find_by_source_ref(con, src_id, ref):
    row = con.execute(
        "SELECT event_id FROM event_source WHERE source_id=? AND source_ref=?", (src_id, ref)
    ).fetchone()
    return row["event_id"] if row else None


def find_candidates(con, venue_code, start, end):
    rows = con.execute(
        """SELECT e.id FROM event e JOIN venue v ON v.id=e.venue_id
           WHERE v.code=? AND e.start_date=? AND e.end_date=? AND e.status!='cancelled'""",
        (venue_code, start.isoformat(), end.isoformat()),
    ).fetchall()
    return [r["id"] for r in rows]


def attach_source(con, event_id, src_id, ref, title, primary=0):
    con.execute(
        """INSERT INTO event_source (event_id,source_id,source_ref,source_title,is_primary)
           VALUES (?,?,?,?,?)
           ON CONFLICT(event_id,source_id,source_ref) DO UPDATE SET last_seen_at=datetime('now')""",
        (event_id, src_id, ref, title, primary),
    )


def update_title(con, event_id, title):
    con.execute(
        "UPDATE event SET title=?, title_norm=?, updated_at=datetime('now') WHERE id=?",
        (title, N.normalize_title(title), event_id),
    )


def find_candidates_by_dates(con, start, end):
    rows = con.execute(
        """SELECT e.id, e.title, v.code AS venue_code FROM event e JOIN venue v ON v.id=e.venue_id
           WHERE e.start_date=? AND e.end_date=? AND e.status!='cancelled'""",
        (start.isoformat(), end.isoformat()),
    ).fetchall()
    return [dict(r) for r in rows]


def add_review(con, event_id, reason, priority=2):
    row = con.execute(
        "SELECT id FROM review_queue WHERE event_id=? AND reason=? AND resolved_at IS NULL",
        (event_id, reason),
    ).fetchone()
    if not row:
        con.execute("INSERT INTO review_queue (event_id,reason,priority) VALUES (?,?,?)",
                    (event_id, reason, priority))
