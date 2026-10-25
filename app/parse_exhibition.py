"""adapter สำหรับ ThailandExhibition (Strapi API)"""
import datetime as dt
import json
import urllib.parse

from . import fetch, normalize as N

API = "https://api.thailandexhibition.com/api/trade-shows"


def _get(url):
    try:
        status, data = fetch.fetch(url, retries=2)
        return json.loads(data)
    except Exception:
        status, data = fetch.fetch_curl(url)
        return json.loads(data)


def _dates(at):
    ds = [d for d in (at.get("event_time") or []) if d]
    if not ds:
        return None
    ds = sorted(dt.date.fromisoformat(x[:10]) for x in ds)
    return ds[0], ds[-1]


def fetch_events(place="อิมแพ็ค", since: dt.date = None, max_pages=6):
    out = []
    page = 1
    while page <= max_pages:
        params = {
            "filters[place][$containsi]": place,
            "sort": "event_time_sort:asc",
            "pagination[page]": page,
        }
        if since:
            params["filters[event_time_sort][$gte]"] = since.isoformat()
        url = API + "?" + urllib.parse.urlencode(params)
        payload = _get(url)
        rows = payload.get("data") or []
        for r in rows:
            e = _map(r)
            if e:
                out.append(e)
        pg = (payload.get("meta") or {}).get("pagination") or {}
        if page >= int(pg.get("pageCount", 1)):
            break
        page += 1
    return out


def _map(row):
    at = row.get("attributes") or {}
    rng = _dates(at)
    if not rng:
        return None
    start, end = rng
    place = (at.get("place") or "").strip()
    title = (at.get("title") or "").strip()
    if not title:
        return None
    menu = (at.get("menu_of_event") or "").lower()
    tl = title.lower()
    if any(k in tl for k in ("concert", "tour", "fancon")) or "คอนเสิร์ต" in menu:
        cat = "concert"
    elif "trade" in menu:
        cat = "trade"
    else:
        cat = "public_fair"
    hall_from, hall_to = N.hall_range(place)
    return {
        "source_ref": "id:%s" % row.get("id"),
        "url": "",
        "title": title,
        "date_text": "%s → %s" % (start.isoformat(), end.isoformat()),
        "start": start,
        "end": end,
        "venue_text": place,
        "venue_code": N.venue_code(place),
        "hall_from": hall_from,
        "hall_to": hall_to,
        "category": cat,
        "audience": "public" if cat != "trade" else "trade_only",
        "is_free": None,
        "price_min": None,
        "price_max": None,
        "organizer": (at.get("organizer") or "").strip() or None,
        "status_raw": "postponed" if "เลื่อน" in title else "",
    }
