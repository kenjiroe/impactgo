"""แปลงข้อความไทย → วันที่ / สถานที่ / ประเภท / ผู้ชม"""
import datetime as dt
import re

TH_MONTHS = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4, "พฤษภาคม": 5,
    "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8, "กันยายน": 9, "ตุลาคม": 10,
    "พฤศจิกายน": 11, "ธันวาคม": 12,
    "ม.ค.": 1, "ก.พ.": 2, "มี.ค.": 3, "เม.ย.": 4, "พ.ค.": 5, "มิ.ย.": 6,
    "ก.ค.": 7, "ส.ค.": 8, "ก.ย.": 9, "ต.ค.": 10, "พ.ย.": 11, "ธ.ค.": 12,
}

VENUE_MAP = [
    ("อิมแพ็ค อารีน่า", "ARENA"),
    ("อิมแพ็ค ชาเลนเจอร์", "CHALLENGER"),
    ("ศูนย์แสดงสินค้า อิมแพ็ค", "EXHIBITION"),
    ("เอ็กซิบิชั่น ฮอลล์", "EXHIBITION"),
    ("อิมแพ็ค เมืองทองธานี", "EXHIBITION"),
    ("IMPACT Exhibition", "EXHIBITION"),
    ("IMPACT Muang Thong Thani", "EXHIBITION"),
    ("Exhibition Hall", "EXHIBITION"),
    ("อิมแพ็ค ฟอรั่ม", "FORUM"),
    ("ธันเดอร์โดม", "THUNDER"),
    ("ริมทะเลสาบ", "LAKESIDE"),
    ("สปีด พาร์ค", "SPEEDPARK"),
    ("พอร์ทอล", "PORTAL"),
]

CATEGORY_MAP = {
    1: "concert", 2: "congress", 3: "exam", 4: "public_fair", 5: "trade",
    6: "sport", 7: "family", 8: "congress", 9: "special",
}

AUDIENCE_BY_CATEGORY = {
    "concert": "public", "public_fair": "public", "family": "public",
    "sport": "public", "special": "public", "trade": "trade_only",
    "congress": "mixed", "exam": "mixed", "unknown": "unknown",
}


def parse_date_text(text: str):
    """รองรับ 3 รูปแบบ: 23-25 ต.ค. 69 / 23 ต.ค. - 1 พ.ย. 69 / 31 ต.ค. 69"""
    s = re.sub(r"\s+", " ", (text or "")).strip()
    s = s.replace("–", "-").replace("—", "-")
    # แปลง พ.ศ. → ค.ศ. ทุกจุดในข้อความ (เช่น "16 ม.ค. 2570 - 17 ม.ค. 2570")
    s = re.sub(r"\b(2[4-9]\d{2})\b", lambda m: str(int(m.group(1)) - 543), s)

    # "16 ม.ค. 2027 - 17 ม.ค. 2027" (มีปีทั้งสองข้าง)
    m = re.match(r"(\d{1,2})\s+(\S+)\s+(\d{4})\s*-\s*(\d{1,2})\s+(\S+)\s+(\d{4})$", s)
    if m:
        mo1, mo2 = TH_MONTHS.get(m[2]), TH_MONTHS.get(m[5])
        if mo1 and mo2:
            return dt.date(int(m[3]), mo1, int(m[1])), dt.date(int(m[6]), mo2, int(m[4]))

    m = re.match(r"(\d{1,2})\s+(\S+)\s*-\s*(\d{1,2})\s+(\S+)\s+(\d{4})$", s)
    if m:
        d1, mo1, d2, mo2, y = int(m[1]), TH_MONTHS.get(m[2]), int(m[3]), TH_MONTHS.get(m[4]), int(m[5])
        if mo1 and mo2:
            return dt.date(y, mo1, d1), dt.date(y, mo2, d2)

    m = re.match(r"(\d{1,2})-(\d{1,2})\s+(\S+)\s+(\d{4})$", s)
    if m:
        mo = TH_MONTHS.get(m[3])
        if mo:
            y = int(m[4])
            return dt.date(y, mo, int(m[1])), dt.date(y, mo, int(m[2]))

    m = re.match(r"(\d{1,2})\s+(\S+)\s+(\d{4})$", s)
    if m:
        mo = TH_MONTHS.get(m[2])
        if mo:
            d = dt.date(int(m[3]), mo, int(m[1]))
            return d, d
    return None


def venue_code(text: str) -> str:
    t = (text or "").strip()
    for needle, code in VENUE_MAP:
        if needle in t:
            return code
    return "OTHER"


def hall_range(text: str):
    m = re.search(r"(?:Hall|ฮอลล์)\s*(\d{1,2})(?:\s*[-–]\s*(\d{1,2}))?", text or "")
    if not m:
        return None, None
    a = int(m.group(1))
    b = int(m.group(2)) if m.group(2) else a
    return a, b


def price_info(text: str):
    t = (text or "").strip()
    if not t:
        return None, None, None
    if "ฟรี" in t:
        return 1, 0, 0
    nums = [int(x.replace(",", "")) for x in re.findall(r"([\d,]{3,})", t)]
    nums = [n for n in nums if 100 <= n <= 200000]
    if nums:
        return 0, min(nums), max(nums)
    return None, None, None


def fix_category(category: str, venue_code: str) -> str:
    """กฎเสริมหมวดงาน: อารีน่าแทบจัดเฉพาะการแสดง — งานที่อารีน่าแต่แท็กแฟร์/ไม่ระบุ = คอนเสิร์ต
    (เคสจริง: Maroon 5 Asia 2027 จาก API exhibition ถูกแท็ก public_fair)"""
    if venue_code == "ARENA" and category in ("public_fair", "unknown"):
        return "concert"
    return category


def normalize_title(t: str) -> str:
    s = (t or "").lower()
    s = re.sub(r"[\u200b-\u200f]", "", s)
    s = re.sub(r"[\(\)\[\]\"'“”‘’]", " ", s)
    s = re.sub(r"\b(20\d{2}|256\d|257\d)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def token_sim(a: str, b: str) -> float:
    """Jaccard ของคำ (ตัดปี/เครื่องหมาย) — ใช้จับคู่งานข้ามแหล่ง"""
    def toks(s):
        s = normalize_title(s)
        s = re.sub(r"[^\w\u0E00-\u0E7F&]+", " ", s)
        return {t for t in s.split() if len(t) >= 2 and not t.isdigit()}
    ta, tb = toks(a), toks(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)
