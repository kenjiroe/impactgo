"""ตรรกะสำหรับ curator: รวมงานซ้ำ / แยกไว้ / ยกเลิก + audit log"""
import datetime as dt

from . import normalize as N


def list_queue(con):
    rows = con.execute(
        """SELECT q.id AS qid, q.reason, q.priority, e.id AS eid, e.title, e.start_date, e.end_date,
                  e.detail_url, v.code AS venue_code, v.name_th AS venue,
                  (SELECT group_concat(s.code) FROM event_source es JOIN source s ON s.id=es.source_id
                    WHERE es.event_id=e.id) AS sources
           FROM review_queue q JOIN event e ON e.id=q.event_id JOIN venue v ON v.id=e.venue_id
           WHERE q.resolved_at IS NULL AND e.status!='cancelled'
           ORDER BY e.start_date, q.priority, q.id"""
    ).fetchall()
    return [dict(r) for r in rows]


def suggestions(con, ev):
    rows = con.execute(
        """SELECT e.id, e.title, e.start_date, e.end_date, v.code AS venue_code, v.name_th AS venue,
                  (SELECT group_concat(s.code) FROM event_source es JOIN source s ON s.id=es.source_id
                    WHERE es.event_id=e.id) AS sources
           FROM event e JOIN venue v ON v.id=e.venue_id
           WHERE e.start_date=? AND e.end_date=? AND e.id!=? AND e.status!='cancelled'""",
        (ev["start_date"], ev["end_date"], ev["eid"]),
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["sim"] = round(N.token_sim(ev["title"], d["title"]) + (0.1 if d["venue_code"] == ev["venue_code"] else 0), 2)
        out.append(d)
    out.sort(key=lambda x: -x["sim"])
    return out


def _resolve(con, qid, actor, note):
    con.execute(
        "UPDATE review_queue SET resolved_at=datetime('now'), resolved_by=? WHERE id=?", (actor, qid)
    )


def merge(con, qid, dup_id, target_id, actor="curator"):
    # ย้ายหลักฐานแหล่งที่มา
    for r in con.execute("SELECT source_id, source_ref, source_title, is_primary FROM event_source WHERE event_id=?", (dup_id,)):
        con.execute(
            """INSERT OR IGNORE INTO event_source (event_id,source_id,source_ref,source_title,is_primary)
               VALUES (?,?,?,?,?)""",
            (target_id, r["source_id"], r["source_ref"], r["source_title"], 0),
        )
    con.execute("DELETE FROM event_source WHERE event_id=?", (dup_id,))
    # ย้ายวัน
    for r in con.execute("SELECT date FROM event_day WHERE event_id=?", (dup_id,)):
        con.execute("INSERT OR IGNORE INTO event_day (event_id,date) VALUES (?,?)", (target_id, r["date"]))
    con.execute("DELETE FROM event_day WHERE event_id=?", (dup_id,))
    con.execute("UPDATE event SET status='cancelled', updated_at=datetime('now') WHERE id=?", (dup_id,))
    con.execute(
        "INSERT INTO change_log (entity,entity_id,change_type,field,old_value,new_value,reason,actor) VALUES (?,?,?,?,?,?,?,?)",
        ("event", dup_id, "merge", "event_id", str(dup_id), str(target_id), "รวมงานซ้ำผ่านหน้า curator", actor),
    )
    _resolve(con, qid, actor, "merged")
    con.commit()


def keep(con, qid, event_id, actor="curator"):
    con.execute("UPDATE event SET status='confirmed', confidence='high', last_verified_at=datetime('now') WHERE id=?", (event_id,))
    con.execute(
        "INSERT INTO change_log (entity,entity_id,change_type,reason,actor) VALUES (?,?,?,?,?)",
        ("event", event_id, "verify", "curator ยืนยันว่าเป็นคนละงาน", actor),
    )
    _resolve(con, qid, actor, "distinct")
    con.commit()


def cancel(con, qid, event_id, actor="curator"):
    con.execute("UPDATE event SET status='cancelled', updated_at=datetime('now') WHERE id=?", (event_id,))
    con.execute(
        "INSERT INTO change_log (entity,entity_id,change_type,reason,actor) VALUES (?,?,?,?,?)",
        ("event", event_id, "cancel", "curator ยกเลิกงานนี้", actor),
    )
    _resolve(con, qid, actor, "cancelled")
    con.commit()
