"""ดึงสรุปงานจากหน้างานจริง (og:description / meta description) ลง event.description

กติกากันโหลดหนักต้นทาง: รันละ cap หน้า เฉพาะงานที่ยังไม่มี description (NULL)
· ดึงสำเร็จแต่ไม่มี meta = เก็บ '' (ไม่ retry)
· เน็ต/HTTP พัง = คง NULL (รอบหน้าลองใหม่)
· โดเมน thaiticketmajor บังคับใช้ fetch_curl (บล็อก UA ธรรมดา)
"""
import html
import re

from . import fetch

OG_RE = re.compile(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
OG_RE_REV = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:description["\']', re.I)
DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
DESC_RE_REV = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', re.I)


def extract_description(doc):
    """og:description ตัวแรกก่อน (เป็นของเฉพาะงาน) — ไม่มีค่อยใช้ meta name=description"""
    for pat in (OG_RE, OG_RE_REV, DESC_RE, DESC_RE_REV):
        m = pat.search(doc)
        if m and m.group(1).strip():
            return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()[:400]
    return ""


def _get(url):
    if "thaiticketmajor" in url:
        status, data = fetch.fetch_curl(url)
    else:
        status, data = fetch.fetch(url)
    return data.decode("utf-8", "ignore")


def refresh(con, cap=8):
    rows = con.execute(
        """SELECT id, detail_url FROM event
           WHERE description IS NULL AND detail_url IS NOT NULL AND detail_url!=''
             AND status IN ('confirmed','tentative') AND end_date>=date('now')
           ORDER BY start_date LIMIT ?""",
        (cap,),
    ).fetchall()
    filled = 0
    for r in rows:
        try:
            txt = extract_description(_get(r["detail_url"]))
        except Exception:  # noqa: BLE001 — พังวันนี้ลองรอบหน้า (คง NULL)
            continue
        con.execute("UPDATE event SET description=? WHERE id=?", (txt, r["id"]))
        filled += 1
    con.commit()
    return filled
