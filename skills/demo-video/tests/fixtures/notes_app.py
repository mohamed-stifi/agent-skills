"""A tiny notes app for demo-video's tests: a web page, a JSON API and an audit log. Python stdlib only.

    python notes_app.py PORT [DB]      # serves http://127.0.0.1:PORT

  GET  /                 the page: a form to add a note, the list of notes
  GET  /api/notes        [{"id", "text", "created"}]
  POST /api/notes        {"text": "..."} -> 201 the note | 422 {"error": "..."} when text is empty
  GET  /api/audit        [{"at", "event", "note_id"}]: every change, newest last
"""

import json
import sqlite3
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
DB = sys.argv[2] if len(sys.argv) > 2 else ":memory:"
db = sqlite3.connect(DB, check_same_thread=False)
db.executescript("""create table if not exists notes (id integer primary key, text text, created text);
                    create table if not exists audit (at text, event text, note_id integer);""")

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Notes</title><style>
body{font:20px -apple-system,system-ui,sans-serif;background:#f6f7fb;margin:0;color:#1d2330}
header{background:#3b5bdb;color:#fff;padding:22px 48px;font-size:28px;font-weight:600}
main{max-width:900px;margin:40px auto;padding:0 24px}
form{display:flex;gap:12px;margin-bottom:28px}
input{flex:1;font-size:22px;padding:14px 16px;border:2px solid #ccd3e0;border-radius:10px}
button{font-size:22px;padding:14px 26px;border:0;border-radius:10px;background:#e8590c;color:#fff;cursor:pointer}
li{background:#fff;border-radius:10px;padding:16px 20px;margin:10px 0;list-style:none;box-shadow:0 1px 3px #0002}
ul{padding:0} .err{color:#c92a2a;margin:-12px 0 20px} small{color:#7a8396;margin-left:12px}
</style></head><body><header>Notes</header><main>
<form id="f"><input id="text" placeholder="Write a note" autocomplete="off"><button id="save">Save</button></form>
<div class="err" id="err"></div><ul id="list"></ul></main><script>
async function load(){const r=await fetch('/api/notes');const n=await r.json();
 document.getElementById('list').innerHTML=n.map(x=>`<li>${x.text}<small>#${x.id}</small></li>`).join('')}
document.getElementById('f').onsubmit=async e=>{e.preventDefault();const t=document.getElementById('text');
 const r=await fetch('/api/notes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t.value})});
 const b=await r.json();document.getElementById('err').textContent=r.ok?'':b.error;if(r.ok){t.value='';load()}};
load();</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            return self.send(200, PAGE, "text/html; charset=utf-8")
        if self.path == "/api/notes":
            rows = db.execute("select id, text, created from notes order by id").fetchall()
            return self.send(200, [{"id": i, "text": t, "created": c} for i, t, c in rows])
        if self.path == "/api/audit":
            rows = db.execute("select at, event, note_id from audit").fetchall()
            return self.send(200, [{"at": a, "event": e, "note_id": n} for a, e, n in rows])
        self.send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/notes":
            return self.send(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except json.JSONDecodeError:
            return self.send(400, {"error": "body is not JSON"})
        text = (body.get("text") or "").strip()
        if not text:
            return self.send(422, {"error": "text is required"})
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        cur = db.execute("insert into notes (text, created) values (?, ?)", (text, now))
        db.execute("insert into audit values (?, 'note.created', ?)", (now, cur.lastrowid))
        db.commit()
        self.send(201, {"id": cur.lastrowid, "text": text, "created": now})


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
