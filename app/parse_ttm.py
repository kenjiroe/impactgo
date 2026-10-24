"""parser สำหรับ ThaiTicketMajor (หน้า tag สถานที่)"""
import html as htmlmod
import re

from . import normalize as N


def _clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", htmlmod.unescape(s)).strip()


def parse_page(doc: str):
    out = []
    for it in re.split(r'<div class="event-item">', doc)[1:]:
        t = re.search(r'class="title"\s+href="([^"]+)"[^>]*>(.*?)</a>', it, re.S)
        d = re.search(r'class="datetime">(.*?)</span>', it, re.S)
        v = re.search(r'class="venue"[^>]*>(.*?)</a>', it, re.S)
        if not (t and d and v):
            continue
        parsed = N.parse_date_text(_clean(d.group(1)))
        if not parsed:
            continue
        start, end = parsed
        venue_text = _clean(v.group(1))
        if ("อิมแพ็ค" not in venue_text) and ("เมืองทอง" not in venue_text):
            continue
        href = t.group(1)
        url = href if href.startswith("http") else "https://m.thaiticketmajor.com" + href
        title = _clean(t.group(2))
        cat = "concert" if any(k in title.lower() for k in ("concert", "tour", "fancon", "world tour")) else "special"
        out.append({
            "source_ref": url,
            "url": url,
            "title": title,
            "date_text": _clean(d.group(1)),
            "start": start,
            "end": end,
            "venue_text": venue_text,
            "venue_code": N.venue_code(venue_text),
            "hall_from": N.hall_range(venue_text)[0],
            "hall_to": N.hall_range(venue_text)[1],
            "category": cat,
            "audience": "public",
            "is_free": 0,
            "price_min": None,
            "price_max": None,
            "status_raw": "",
        })
    return out
