#!/usr/bin/env python3
"""ImpactGo — ingest ปฏิทินอิมแพ็ค + คำนวณระดับ + สร้างเว็บ"""
import datetime as dt
import os
import sys
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import assets, build_site, db, fetch, holidays, normalize as N, parse_exhibition, parse_impact, parse_ttm, score, share_card  # noqa: E402

BASE = "https://www.impact.co.th/th/visitors/event-calendar"
TTM_URL = "https://m.thaiticketmajor.com/tag/Impact%20Arena"
SNAP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "snapshots")


def main():
    tz = ZoneInfo("Asia/Bangkok")
    today = dt.datetime.now(tz).date()
    con = db.connect()
    db.init_db(con)
    src = db.source_id(con, "impact")

    all_events, seen = [], set()
    for page, start in enumerate(range(0, 24 * 8, 24), 1):
        url = BASE if start == 0 else f"{BASE}?start={start}"
        try:
            status, data = fetch.fetch(url)
        except Exception as e:  # noqa: BLE001
            print(f"[warn] page {page} fetch failed: {e}")
            break
        digest, path = fetch.save_snapshot(data, SNAP, f"impact-p{page}")
        cur = con.execute(
            """INSERT OR IGNORE INTO raw_document (source_id,url,fetched_at,http_status,content_hash,storage_path,bytes)
               VALUES (?,?,?,?,?,?,?)""",
            (src, url, dt.datetime.now(tz).isoformat(timespec="seconds"), status, digest, path, len(data)),
        )
        new_doc = cur.rowcount > 0
        events = parse_impact.parse_page(data.decode("utf-8", "ignore"))
        fresh = [e for e in events if e["source_ref"] not in {x["source_ref"] for x in all_events}]
        print(f"[page {page}] {len(events)} cards, {len(fresh)} new")
        if new_doc:
            doc_id = con.execute(
                "SELECT id FROM raw_document WHERE source_id=? AND url=? AND content_hash=?",
                (src, url, digest),
            ).fetchone()["id"]
            for e in events:
                con.execute(
                    """INSERT INTO event_raw (raw_document_id,title_raw,date_text,venue_text,price_text,detail_url)
                       VALUES (?,?,?,?,?,?)""",
                    (doc_id, e["title"], e["date_text"], e["venue_text"],
                     "" if e["is_free"] is None else str(e["is_free"]), e["url"]),
                )
        if not events or not fresh:
            break
        all_events += fresh
        for e in fresh:
            eid = db.upsert_event(con, e, src, verified=dt.datetime.now(tz).isoformat(timespec="seconds"))
            seen.add(str(eid))
        con.commit()

    # ---- แหล่งที่ 2: ThaiTicketMajor ----
    ttm_src = db.source_id(con, "ttm")
    try:
        status, data = fetch.fetch_curl(TTM_URL)
        digest, path = fetch.save_snapshot(data, SNAP, "ttm-p1")
        con.execute(
            """INSERT OR IGNORE INTO raw_document (source_id,url,fetched_at,http_status,content_hash,storage_path,bytes)
               VALUES (?,?,?,?,?,?,?)""",
            (ttm_src, TTM_URL, dt.datetime.now(tz).isoformat(timespec="seconds"), status, digest, path, len(data)),
        )
        ttm_events = [e for e in parse_ttm.parse_page(data.decode("utf-8", "ignore")) if e["end"] >= today]
        added, merged = 0, 0
        for e in ttm_events:
            eid = db.find_by_source_ref(con, ttm_src, e["source_ref"])
            if eid:
                row = con.execute("SELECT title FROM event WHERE id=?", (eid,)).fetchone()
                if len(e["title"]) > len(row["title"]) + 2:
                    db.update_title(con, eid, e["title"])
                db.attach_source(con, eid, ttm_src, e["source_ref"], e["title"])
                continue
            eid = db.find_identity(con, db.identity_hash(e["title"], e["venue_code"], e["start"]))
            if eid:
                row = con.execute("SELECT title FROM event WHERE id=?", (eid,)).fetchone()
                if len(e["title"]) > len(row["title"]) + 2:
                    db.update_title(con, eid, e["title"])
                db.attach_source(con, eid, ttm_src, e["source_ref"], e["title"])
                continue
            cands = db.find_candidates(con, e["venue_code"], e["start"], e["end"])
            if len(cands) == 1:
                eid = cands[0]
                row = con.execute("SELECT title FROM event WHERE id=?", (eid,)).fetchone()
                if len(e["title"]) > len(row["title"]) + 2:
                    db.update_title(con, eid, e["title"])
                db.attach_source(con, eid, ttm_src, e["source_ref"], e["title"])
                merged += 1
            else:
                eid = db.upsert_event(con, e, ttm_src, verified=dt.datetime.now(tz).isoformat(timespec="seconds"))
                added += 1
            seen.add(str(eid))
        con.commit()
        print(f"[ttm] {len(ttm_events)} upcoming, merged={merged}, new={added}")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] ttm failed: {exc}")

    # ---- แหล่งที่ 3: ThailandExhibition (API) ----
    ex_src = db.source_id(con, "exhibition")
    try:
        ex_events = [e for e in parse_exhibition.fetch_events(since=today - dt.timedelta(days=1)) if e["end"] >= today]
        added, merged, queued = 0, 0, 0
        for e in ex_events:
            if db.find_by_source_ref(con, ex_src, e["source_ref"]):
                continue
            cands = db.find_candidates_by_dates(con, e["start"], e["end"])
            best, best_sim = None, 0.0
            for c in cands:
                sim = N.token_sim(e["title"], c["title"]) + (0.1 if c["venue_code"] == e["venue_code"] else 0)
                if sim > best_sim:
                    best, best_sim = c["id"], sim
            if best and best_sim >= 0.6:
                db.attach_source(con, best, ex_src, e["source_ref"], e["title"])
                merged += 1
            else:
                eid = db.upsert_event(con, e, ex_src, verified=dt.datetime.now(tz).isoformat(timespec="seconds"))
                added += 1
                if cands:
                    db.add_review(con, eid, "possible_duplicate", 2)
                    queued += 1
        con.commit()
        print(f"[exhibition] {len(ex_events)} upcoming, merged={merged}, new={added}, queued={queued}")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] exhibition failed: {exc}")

    if len(all_events) < 10:
        print("[abort] parsed too few events — keep previous data")
        return 1

    try:
        n_hol = holidays.refresh(con, today=today)
        if n_hol:
            print(f"[holidays] refreshed {n_hol}")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] holidays failed: {exc}")

    tentative = db.purge_missing(con, src, seen, today)
    score.recompute(con, today, 70)
    build_id = "%s-%d" % (dt.datetime.now().strftime("%Y%m%d-%H%M"), 0)
    try:
        assets.build(os.path.join(os.path.dirname(os.path.abspath(__file__)), "site"), build_id)
        print("[assets] icons + manifest + sw")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] assets failed: {exc}")
    try:
        cards = share_card.build_cards(con, today, weeks=8)
        print(f"[share] {len(cards)} cards")
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] share cards failed: {exc}")
    n = build_site.build(con, today, weeks=12)
    con.commit()

    lv = dict(con.execute("SELECT level, count(*) c FROM day_score WHERE date>=? GROUP BY level", (today.isoformat(),)).fetchall())
    print(f"[done] events={n} (new this run: {len(all_events)}) missing→tentative={tentative}")
    print(f"[done] levels: {dict(sorted(lv.items()))}")
    print(f"[done] site: {os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site', 'index.html')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
