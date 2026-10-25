"""สร้างไอคอน + manifest + service worker (PWA-lite)"""
import json
import os
import subprocess

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ICON_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;box-sizing:border-box}
body{width:%(s)dpx;height:%(s)dpx;background:#141414;display:flex;align-items:center;justify-content:center}
.cal{width:66%%;height:66%%;background:#fff;border-radius:20%%;position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;padding-top:12%%}
.bar{position:absolute;top:16%%;left:9%%;right:9%%;height:15%%;background:#141414;border-radius:6px}
.d{font-family:'Thonburi',sans-serif;font-weight:800;color:#141414;font-size:%(d)dpx;line-height:1;margin-top:6%%}
.t{font-family:'Thonburi',sans-serif;color:#6b6b6b;font-size:%(t)dpx;margin-top:%(m)dpx}
</style></head><body><div class="cal"><div class="bar"></div><div class="d">25</div></div></body></html>"""


def _icon(size, path):
    html = ICON_HTML % {"s": size, "d": int(size * 0.30), "t": int(size * 0.095), "m": int(size * 0.015)}
    tmp = "/tmp/icon-%d.html" % size
    open(tmp, "w", encoding="utf-8").write(html)
    if os.path.exists(CHROME):
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--user-data-dir=/tmp/igicon", "--screenshot=" + path,
                        "--window-size=%d,%d" % (size, size), "--virtual-time-budget=1500",
                        "file://" + tmp], capture_output=True)


def build(site_dir, build_id):
    os.makedirs(site_dir, exist_ok=True)
    for s, n in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")):
        _icon(s, os.path.join(site_dir, n))

    manifest = {
        "name": "ปฏิทินงาน เมืองทองธานี",
        "short_name": "ImpactGo",
        "description": "งานล่วงหน้า 8 สัปดาห์ + ระดับคนแน่น",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
        "background_color": "#f6f6f3",
        "theme_color": "#141414",
        "lang": "th",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    with open(os.path.join(site_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    sw = """const V='%s';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==V).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  e.respondWith(fetch(e.request).then(r=>{const c=r.clone();caches.open(V).then(x=>x.put(e.request,c));return r})
    .catch(()=>caches.match(e.request).then(r=>r||caches.match('./'))));
});
""" % build_id
    with open(os.path.join(site_dir, "sw.js"), "w", encoding="utf-8") as f:
        f.write(sw)
