"""parser สำหรับหน้า IMPACT event calendar (Joomla + Event Booking)"""
import html as htmlmod
import re

from . import normalize as N


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = htmlmod.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def parse_page(doc: str):
    """คืน list ของ dict (ยังไม่แตะ DB)"""
    out = []
    chunks = re.split(r'<div class="eb-category-', doc)[1:]
    for ch in chunks:
        head = ch[:2500]
        mcat = re.match(r"(\d+)", ch)
        mid = re.search(r"eb-event-(\d+)", head)
        if not (mcat and mid):
            continue
        href = re.search(r'class="eb-event-title"\s+href="([^"]+)"', head)
        title = re.search(r'class="eb-event-title"[^>]*>(.*?)</a>', head, re.S)
        date = re.search(r'class="eb-event-date-time">(.*?)</div>', head, re.S)
        venue = re.search(r'class="eb-event-location">(.*?)</div>', head, re.S)
        price = re.search(r'class="eb-individual-price">(.*?)</span>', head, re.S)
        status = re.search(r"status-(\w+)", head)

        if not (title and date):
            continue
        parsed = N.parse_date_text(_clean(date.group(1)))
        if not parsed:
            continue
        start, end = parsed
        venue_text = _clean(venue.group(1)) if venue else ""
        p_free, p_min, p_max = N.price_info(_clean(price.group(1)) if price else "")
        cat_id = int(mcat.group(1))
        category = N.CATEGORY_MAP.get(cat_id, "unknown")
        out.append({
            "source_ref": str(mid.group(1)),
            "url": ("https://www.impact.co.th" + href.group(1)) if href else "",
            "title": _clean(title.group(1)),
            "date_text": _clean(date.group(1)),
            "start": start,
            "end": end,
            "venue_text": venue_text,
            "venue_code": N.venue_code(venue_text),
            "hall_from": N.hall_range(venue_text)[0],
            "hall_to": N.hall_range(venue_text)[1],
            "category": category,
            "audience": N.AUDIENCE_BY_CATEGORY.get(category, "unknown"),
            "is_free": p_free,
            "price_min": p_min,
            "price_max": p_max,
            "status_raw": status.group(1) if status else "",
        })
    return out
