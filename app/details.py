"""ดึงเนื้อหางานจากหน้างานจริง ลง event.description (สรุป og/meta) + event.description_full (กล่อง .eb-description)

กติกากันโหลดหนักต้นทาง: รันละ cap หน้า เฉพาะงานที่ยังมี field ว่าง (NULL)
· ดึงสำเร็จแต่ไม่เจอเนื้อหา = เก็บ '' (ไม่ retry)
· เน็ต/HTTP พัง = คง NULL (รอบหน้าลองใหม่)
· โดเมน thaiticketmajor บังคับใช้ fetch_curl (บล็อก UA ธรรมดา)
· ข้อความล้วน (ตัด script/style/img) — ไม่เอารูป/สื่อจากต้นทาง ตามกติกา deploy/README

รูปแบบเนื้อเต็ม: ย่อหน้าคั่นด้วย \n · บล็อก "ติดต่อผู้จัด" แยกออกด้วย split_contact()
เพื่อให้หน้าเว็บเรนเดอร์ tel/website/facebook/email เป็นลิงก์ได้ (contact_html)
"""
import html
import re
from html.parser import HTMLParser

from . import fetch

OG_RE = re.compile(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
OG_RE_REV = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:description["\']', re.I)
DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
DESC_RE_REV = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', re.I)

MAX_FULL = 2000
CONTACT_MARK = "ติดต่อผู้จัด"
SKIP_TAGS = ("script", "style", "img", "noscript")
SKIP_CLASSES = ("eb-save-to-calendar-buttons",)  # ปุ่มแชร์ของ Joomla อยู่ในกล่อง — ตัดทิ้ง
BREAK_TAGS = {"p", "div", "li", "tr", "br", "dt", "dd", "section", "article", "table", "ul", "ol",
              "h1", "h2", "h3", "h4", "h5", "h6"}
JUNK_LINES = {"tweet", "back", "print", "google calendar", "yahoo calendar", "save ical",
              "save to google calendar", "add to calendar"}


class _BoxText(HTMLParser):
    """เก็บข้อความภายใน div ที่ class ตรงเป้า (ตามความลึกจริงของ DOM) — ปิดท้าย tag บล็อก = ขึ้นบรรทัด

    เก็บข้อความดิบ (ไม่ strip) เพื่อรักษาช่องว่างขอบเขต tag เช่น <strong>Tel.</strong>02 422 9999
    """

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
        if self.target_depth is not None and not self.done and self.skip_depth is None \
                and any(sc in cls for sc in SKIP_CLASSES):
            self.skip_depth = len(self.stack)
        self.stack.append(tag)
        if self.target_depth is not None and not self.done and tag in SKIP_TAGS:
            self.skip_depth = self.skip_depth or len(self.stack)

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        if self.target_depth is not None and not self.done and len(self.stack) == self.target_depth:
            self.done = True
            self.chunks.append("\n")
            return
        if self.target_depth is not None and not self.done and tag in BREAK_TAGS:
            self.chunks.append("\n")
        if self.skip_depth is not None and len(self.stack) < self.skip_depth:
            self.skip_depth = None

    def handle_data(self, data):
        if (self.target_depth is not None and not self.done and self.skip_depth is None and data.strip()):
            self.chunks.append(data)


def extract_box(doc, target_class):
    """ข้อความในกล่อง — ย่อหน้าคั่น \n, ช่องว่างยุบทีละบรรทัด, กรองบรรทัดขยะปุ่มแชร์, cap MAX_FULL"""
    p = _BoxText(target_class)
    try:
        p.feed(doc)
    except Exception:  # noqa: BLE001 — HTML เพี้ยนบางส่วนยังเอาข้อความที่ได้กลับมาใช้ได้
        pass
    lines = []
    for ln in "".join(p.chunks).split("\n"):
        ln = re.sub(r"\s+", " ", ln).strip()
        if ln and ln.lower() not in JUNK_LINES and not ln.lower().startswith("save "):
            lines.append(ln)
    return "\n".join(lines)[:MAX_FULL]


CONTACT_MARKS = ("ติดต่อผู้จัดงาน", "ติดต่อผู้จัด")


def split_contact(full):
    """แยกบล็อก 'ติดต่อผู้จัด' ออกจากเนื้อหา — คืน (body, contact)

    marker ถูกตัดทิ้ง (หน้าเว็บเรนเดอร์หัวข้อ "ติดต่อผู้จัดงาน" ให้แล้ว)
    ข้อความต่อท้าย marker ในบรรทัดเดียวกัน (ชื่อบริษัทที่ติดกันใน HTML ต้นทาง) จะคงไว้
    """
    i = -1
    mark = ""
    for m in CONTACT_MARKS:
        i = full.find(m)
        if i >= 0:
            mark = m
            break
    if i < 0:
        return full, ""
    return full[:i].strip(), full[i + len(mark):].lstrip(" :：\n").strip()


def extract_description(doc):
    """og:description ตัวแรกก่อน (เป็นของเฉพาะงาน) — ไม่มีค่อยใช้ meta name=description"""
    for pat in (OG_RE, OG_RE_REV, DESC_RE, DESC_RE_REV):
        m = pat.search(doc)
        if m and m.group(1).strip():
            return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()[:400]
    return ""


def contact_html(contact):
    """บล็อกติดต่อ → HTML: เบอร์โทร tel:+66 · เว็บ https · Facebook · อีเมล mailto"""
    out = []
    for raw in contact.split("\n"):
        ln = raw.strip()
        if not ln or ln in CONTACT_MARKS:
            continue  # label หัวบล็อกซ้ำกับที่เรนเดอร์อยู่แล้ว
        m = re.match(r"^(Tel\.?|โทร\.?)\s*(.+)$", ln, re.I)
        if m:
            main = re.split(r"(?:Ext\.?|ต่อ)", m.group(2), flags=re.I)[0]
            digits = "".join(c for c in main if c.isdigit())
            if digits.startswith("0") and len(digits) >= 9:
                href = "tel:+66" + digits[1:]
            elif len(digits) >= 10:  # เบอร์ต่างประเทศที่พ่วงรหัสประเทศมาแล้ว
                href = "tel:+" + digits
            else:
                href = "tel:" + digits
            out.append('<div>%s <a href="%s">%s</a></div>' % (esc(m.group(1)), esc(href), esc(m.group(2))))
            continue
        m = re.search(r"(?:Website|เว็บไซต์)\s*:?\s*(\S+|)", ln, re.I)
        m = m if m and m.group(1) else re.search(r"(www\.[^\s]+|https?://\S+)", ln)
        if m and m.group(1):
            href = m.group(1)
            if href.startswith("www."):
                href = "https://" + href
            out.append('<div><a href="%s" target="_blank" rel="noopener">%s</a></div>' % (esc(href), esc(m.group(1))))
            continue
        m = re.match(r"^(Facebook|FB)\s*:?\s*(\S+)$", ln, re.I)
        if m:
            out.append('<div>%s <a href="https://facebook.com/%s" target="_blank" rel="noopener">%s</a></div>'
                       % (esc(m.group(1)), esc(m.group(2).lstrip("@")), esc(m.group(2))))
            continue
        m = re.search(r"[\w.+-]+@[\w.-]+\.\w+", ln)
        if m:
            out.append('<div>%s <a href="mailto:%s">%s</a></div>' % (esc(ln[:m.start()]).strip(), esc(m.group(0)), esc(m.group(0))))
            continue
        out.append("<div>%s</div>" % esc(ln))
    return "".join(out)


def esc(s):
    return html.escape(s or "", quote=True)


def _get(url):
    if "thaiticketmajor" in url:
        status, data = fetch.fetch_curl(url)
    else:
        status, data = fetch.fetch(url)
    return data.decode("utf-8", "ignore")


def refresh(con, cap=8):
    rows = con.execute(
        """SELECT id, detail_url, description FROM event
           WHERE (description IS NULL OR description_full IS NULL OR contact IS NULL)
             AND detail_url IS NOT NULL AND detail_url!=''
             AND status IN ('confirmed','tentative') AND end_date>=date('now')
             AND (description_full IS NULL OR description_full!='')
           ORDER BY start_date LIMIT ?""",
        (cap,),
    ).fetchall()
    filled = 0
    for r in rows:
        try:
            doc = _get(r["detail_url"])
            short = extract_description(doc)
            full = extract_box(doc, "eb-description")
            _, contact = split_contact(full)
        except Exception:  # noqa: BLE001 — พังวันนี้ลองรอบหน้า (คง NULL)
            continue
        # ถ้ากล่องเนื้อหาไม่ต่างจากสรุป (ยาวกว่าไม่ถึง 60 ตัวอักษร) ถือว่าไม่มีของขยาย
        flat = full.replace("\n", " ")
        if flat and r["description"] and len(flat) <= len(r["description"]) + 60:
            full = ""
        # คงสรุปเดิมไว้ถ้าหน้านี้ไม่มี meta ('' = ดึงแล้วไม่มีของ — ไม่ต้อง retry)
        new_desc = short if short else (r["description"] if r["description"] is not None else "")
        con.execute(
            "UPDATE event SET description=?, description_full=?, contact=? WHERE id=?",
            (new_desc, full, contact, r["id"]),
        )
        filled += 1
    con.commit()
    return filled
