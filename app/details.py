"""ดึงเนื้อหางานจากหน้างานจริง ลง event.description (สรุป og/meta) + event.description_full (กล่อง .eb-description)

กติกากันโหลดหนักต้นทาง: รันละ cap หน้า เฉพาะงานที่ยังมี field ว่าง (NULL)
· ดึงสำเร็จแต่ไม่เจอเนื้อหา = เก็บ '' (ไม่ retry)
· เน็ต/HTTP พัง = คง NULL (รอบหน้าลองใหม่)
· โดเมน thaiticketmajor บังคับใช้ fetch_curl (บล็อก UA ธรรมดา)
· ข้อความล้วน (ตัด script/style/img) — ไม่เอารูป/สื่อจากต้นทาง ตามกติกา deploy/README
"""
import html
import re
from html.parser import HTMLParser

from . import fetch

OG_RE = re.compile(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
OG_RE_REV = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:description["\']', re.I)
DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
DESC_RE_REV = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', re.I)

MAX_FULL = 1600
SKIP_TAGS = ("script", "style", "img", "noscript")


class _BoxText(HTMLParser):
    """เก็บข้อความภายใน div ที่ class ตรงเป้า (ตามความลึกจริงของ DOM)"""

    def __init__(self, target_class):
        super().__init__(convert_charrefs=True)
        self.target_class = target_class
        self.stack = []
        self.target_depth = None
        self.skip_depth = None
        self.done = False
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        cls = ""
        for k, v in attrs:
            if k == "class":
                cls = v or ""
                break
        if self.target_depth is None and not self.done and self.target_class in cls.split():
            self.target_depth = len(self.stack)
        self.stack.append(tag)
        if self.target_depth is not None and not self.done and tag in SKIP_TAGS:
            self.skip_depth = len(self.stack)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        if self.target_depth is not None and not self.done and len(self.stack) == self.target_depth:
            self.done = True
        if self.skip_depth is not None and len(self.stack) < self.skip_depth:
            self.skip_depth = None

    def handle_data(self, data):
        if (self.target_depth is not None and not self.done and self.skip_depth is None and data.strip()):
            self.chunks.append(data.strip())


def extract_box(doc, target_class):
    p = _BoxText(target_class)
    try:
        p.feed(doc)
    except Exception:  # noqa: BLE001 — HTML เพี้ยนบางส่วนยังเอาข้อความที่ได้กลับมาใช้ได้
        pass
    return re.sub(r"\s+", " ", " ".join(p.chunks)).strip()[:MAX_FULL]


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
        """SELECT id, detail_url, description FROM event
           WHERE (description IS NULL OR description_full IS NULL)
             AND detail_url IS NOT NULL AND detail_url!=''
             AND status IN ('confirmed','tentative') AND end_date>=date('now')
           ORDER BY start_date LIMIT ?""",
        (cap,),
    ).fetchall()
    filled = 0
    for r in rows:
        try:
            doc = _get(r["detail_url"])
            short = extract_description(doc)
            full = extract_box(doc, "eb-description")
        except Exception:  # noqa: BLE001 — พังวันนี้ลองรอบหน้า (คง NULL)
            continue
        # ถ้ากล่องเนื้อหาไม่ต่างจากสรุป (ยาวกว่าไม่ถึง 60 ตัวอักษร) ถือว่าไม่มีของขยาย
        if full and r["description"] and len(full) <= len(r["description"]) + 60:
            full = ""
        # คงสรุปเดิมไว้ถ้าหน้านี้ไม่มี meta ('' = ดึงแล้วไม่มีของ — ไม่ต้อง retry)
        new_desc = short if short else (r["description"] if r["description"] is not None else "")
        con.execute(
            "UPDATE event SET description=?, description_full=? WHERE id=?",
            (new_desc, full, r["id"]),
        )
        filled += 1
    con.commit()
    return filled
