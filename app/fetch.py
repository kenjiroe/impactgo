"""HTTP fetch + snapshot ที่ตรวจย้อนได้ (ไม่ใช้ library ภายนอก)"""
import glob
import hashlib
import os
import subprocess
import time
import urllib.error
import urllib.request

UA = "ImpactGo/0.1 (personal project; contact: ken@localhost)"


def fetch(url: str, retries: int = 3, timeout: int = 25) -> tuple:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": UA, "Accept-Language": "th,en;q=0.8"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise last


def save_snapshot(data: bytes, root: str, name: str) -> tuple:
    """คืน (hash, path) และเขียนไฟล์เฉพาะเมื่อเนื้อหาเปลี่ยน"""
    h = hashlib.sha256(data).hexdigest()[:16]
    d = os.path.join(root, time.strftime("%Y-%m-%d"))
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{name}-{h}.html")
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(data)
    # เก็บย้อนหลังไม่เกิน 6 ไฟล์/หน้า/วัน (หน้าเว็บมี token ทำให้ hash เปลี่ยนทุกครั้ง)
    same = sorted(glob.glob(os.path.join(d, f"{name}-*.html")))
    for old in same[:-6]:
        try:
            os.remove(old)
        except OSError:
            pass
    return h, path


CURL_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")


def fetch_curl(url: str, timeout: int = 30) -> tuple:
    """บางโดเมนบล็อก urllib ที่ระดับ TLS — ใช้ curl ที่มากับ macOS แทน"""
    # หมายเหตุ: โดเมนนี้บล็อก UA บางแบบ (Mozilla/5.0 สั้น ๆ และ UA ของเรา) จึงใช้ค่า default ของ curl
    p = subprocess.run(
        ["curl", "-fsSL", "--compressed", "--max-time", str(timeout), url],
        capture_output=True,
    )
    if p.returncode != 0 or not p.stdout:
        raise RuntimeError(f"curl failed ({p.returncode}): {p.stderr[:120]!r}")
    return 200, p.stdout
