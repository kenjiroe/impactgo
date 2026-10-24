#!/usr/bin/env python3
"""หน้า curator แบบ localhost — ใช้ไลบรารีมาตรฐานเท่านั้น"""
import datetime as dt
import html
import os
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import build_site, curate, db  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = """
body{margin:0;background:#f6f6f3;color:#141414;font-family:"Sarabun","Noto Sans Thai","Thonburi",system-ui,sans-serif;line-height:1.5}
header{background:#141414;color:#fff;padding:16px 20px}
header h1{margin:0;font-size:18px} header p{margin:4px 0 0;color:#bbb;font-size:12px}
main{max-width:900px;margin:0 auto;padding:16px}
.card{background:#fff;border:1px solid #e3e3dd;border-radius:10px;padding:14px;margin-bottom:12px}
.card h2{margin:0 0 4px;font-size:15px}
.meta{font-size:12px;color:#666;margin-bottom:8px}
.tag{display:inline-block;font-size:11px;background:#eee;border-radius:6px;padding:1px 6px;margin-right:4px}
.opt{display:block;border:1px solid #e3e3dd;border-radius:8px;padding:8px 10px;margin:6px 0;font-size:13px}
.opt input{margin-right:6px}
button{font:inherit;font-size:12.5px;padding:6px 12px;border-radius:8px;border:1px solid #141414;background:#141414;color:#fff;cursor:pointer}
button.ghost{background:#fff;color:#141414}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.msg{background:#e8f3e2;border:1px solid #8fbf7a;border-radius:8px;padding:8px 12px;margin-bottom:12px;font-size:13px}
.empty{color:#666;font-size:14px;padding:20px;text-align:center}
form{display:inline}
"""


def page(body, msg=""):
    return f"""<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>ImpactGo — Curator</title>
<style>{CSS}</style></head><body>
<header><h1>ImpactGo · ตรวจงาน</h1><p>เฉพาะเครื่องนี้ (localhost) · การกระทำทุกอย่างถูกบันทึกใน change_log</p></header>
<main>{msg}{body}</main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        con = db.connect()
        try:
            q = curate.list_queue(con)
            parts = []
            if not q:
                parts.append('<div class="card empty">ไม่มีงานรอตรวจ 🎉</div>')
            for ev in q:
                sugs = curate.suggestions(con, ev)
                opts = "".join(
                    f'<label class="opt"><input type="radio" name="target" value="{s["id"]}" required>'
                    f'<b>{html.escape(s["title"])}</b> · {html.escape(s["venue"])} '
                    f'· sim {s["sim"]:.2f} <span class="tag">{html.escape(s["sources"] or "-")}</span></label>'
                    for s in sugs
                ) or '<div class="meta">ไม่พบงานวันเดียวกันให้เทียบ</div>'
                merge_form = f"""<form method="post" action="/action">
                    <input type="hidden" name="action" value="merge">
                    <input type="hidden" name="qid" value="{ev['qid']}">
                    <input type="hidden" name="eid" value="{ev['eid']}">
                    {opts}
                    <div class="row"><button type="submit">รวมเข้ากับงานที่เลือก</button></div>
                </form>""" if sugs else ""
                parts.append(f"""<div class="card">
                    <h2>{html.escape(ev['title'])}</h2>
                    <div class="meta">{html.escape(ev['start_date'])} → {html.escape(ev['end_date'])}
                      · {html.escape(ev['venue'])} <span class="tag">{html.escape(ev['sources'] or '-')}</span>
                      · เหตุผล: {html.escape(ev['reason'])}</div>
                    {merge_form}
                    <div class="row">
                      <form method="post" action="/action"><input type="hidden" name="action" value="keep">
                        <input type="hidden" name="qid" value="{ev['qid']}"><input type="hidden" name="eid" value="{ev['eid']}">
                        <button class="ghost" type="submit">เป็นคนละงาน (เก็บไว้)</button></form>
                      <form method="post" action="/action"><input type="hidden" name="action" value="cancel">
                        <input type="hidden" name="qid" value="{ev['qid']}"><input type="hidden" name="eid" value="{ev['eid']}">
                        <button class="ghost" type="submit">ยกเลิกงานนี้</button></form>
                    </div></div>""")
            msg = ""
            if "msg" in self.path:
                msg = '<div class="msg">บันทึกแล้ว · หน้าเว็บถูกสร้างใหม่</div>'
            self._send(200, page("".join(parts), msg))
        finally:
            con.close()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        form = urllib.parse.parse_qs(self.rfile.read(length).decode("utf-8"))
        action = (form.get("action") or [""])[0]
        qid = int((form.get("qid") or ["0"])[0])
        eid = int((form.get("eid") or ["0"])[0])
        target = (form.get("target") or [""])[0]
        con = db.connect()
        try:
            if action == "merge" and target:
                curate.merge(con, qid, eid, int(target))
            elif action == "keep":
                curate.keep(con, qid, eid)
            elif action == "cancel":
                curate.cancel(con, qid, eid)
            today = dt.datetime.now(ZoneInfo("Asia/Bangkok")).date()
            build_site.build(con, today, weeks=8)
        finally:
            con.close()
        self.send_response(303)
        self.send_header("Location", "/?msg=1")
        self.end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    print(f"curator: http://localhost:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
