"""
Vulnerable HTTP web app honeypot — app.py
=========================================
The primary attack target. Implements a small "shop" with a SQLite backend.
Vulnerabilities (intentional, for the lab):
  1. SQL injection on /login, /product, /search (string-built queries)
  2. Command injection on /api/ping?host= (shell=True)
  3. Reflected XSS on /search?q=
  4. Insecure file upload on /upload (any file, any name)
  5. Verbose error messages (stack traces)
Every request logged as JSON.
"""
from __future__ import annotations
import os, json, datetime, sqlite3, subprocess, html
from typing import Any
from flask import Flask, request, jsonify, render_template_string, g

HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "http"
CONTAINER_NAME = "hp-http"
LISTEN_PORT = int(os.environ.get("PORT", "5000"))
DB = "/tmp/shop.db"

app = Flask(__name__)


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user TEXT, pass TEXT);
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL);
        INSERT OR IGNORE INTO users VALUES (1,'admin','s3cr3t'),(2,'alice','alicepw'),(3,'bob','bobpw');
        INSERT OR IGNORE INTO products VALUES (1,'Widget',9.99),(2,'Gadget',19.99),(3,'Gizmo',4.99);
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def emit_log(event: dict[str, Any]) -> None:
    base = {
        "@timestamp": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "container_name": CONTAINER_NAME,
        "container_service": SERVICE,
        "honeypot_host_ip": HOST_IP,
        "src_ip": request.remote_addr or "0.0.0.0",
        "src_port": request.environ.get("REMOTE_PORT"),
        "dst_port": LISTEN_PORT,
        "protocol": "HTTP",
        "method": request.method,
        "path": request.path,
        "query": request.query_string.decode("utf-8", "ignore"),
        "user_agent": request.headers.get("User-Agent", ""),
        "attack_type_hint": "benign",
    }
    base.update(event)
    print(json.dumps(base, default=str), flush=True)


def classify(p: str, q: str, b: str) -> str:
    blob = f"{p}?{q} {b}".lower()
    for atk, kws in [
        ("sql_injection", ["'", " or 1=1", "union select", "--", "sleep(", "information_schema", "0x", "benchmark("]),
        ("command_injection", [";", "|", "$(", "`", "/bin/sh", "&&", "||"]),
        ("xss", ["<script", "onerror=", "javascript:", "<img src=x", "<svg"]),
        ("path_traversal", ["../", "..\\", "/etc/passwd"]),
        ("brute_force", ["password=", "passwd="]),
        ("directory_enum", [".git/", ".env", "wp-admin", "phpmyadmin", "admin.php", "config.php"]),
    ]:
        if any(k in blob for k in kws):
            return atk
    return "benign"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
INDEX = """<!doctype html><html><head><title>Shop</title></head>
<body><h1>ACME Shop</h1>
<form method='POST' action='/login'>u:<input name='u'>p:<input name='p' type='password'><button>Login</button></form>
<form action='/search'><input name='q'><button>Search</button></form>
<a href='/product?id=1'>Product 1</a> |
<a href='/api/ping?host=127.0.0.1'>Ping</a> |
<form method='POST' action='/upload' enctype='multipart/form-data'>
  Upload: <input type='file' name='f'><button>Upload</button>
</form>
</body></html>"""


@app.route("/")
def index():
    emit_log({"response_code": 200})
    return render_template_string(INDEX)


@app.route("/login", methods=["GET", "POST"])
def login():
    u = request.values.get("u", "")
    p = request.values.get("p", "")
    atk = classify(request.path, request.query_string.decode(), f"u={u}&p={p}")
    ok = False
    try:
        # VULNERABLE: string-built SQL.
        q = f"SELECT * FROM users WHERE user='{u}' AND pass='{p}'"
        row = get_db().execute(q).fetchone()
        ok = row is not None
    except Exception as e:  # noqa: BLE001
        emit_log({"username": u, "password": p, "attack_type_hint": "sql_injection",
                  "response_code": 500, "db_error": str(e)[:200]})
        return f"DB error: {e}", 500
    emit_log({"username": u, "password": p, "attack_type_hint": atk if not ok else "login_success",
              "auth_success": ok, "response_code": 200 if ok else 401})
    return ("Welcome " + u if ok else "Bad credentials"), (200 if ok else 401)


@app.route("/product")
def product():
    pid = request.args.get("id", "1")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        # VULNERABLE: string-built SQL.
        q = f"SELECT * FROM products WHERE id={pid}"
        row = get_db().execute(q).fetchone()
        if row:
            code, body = 200, dict(row)
        else:
            code, body = 404, {"err": "not found"}
    except Exception as e:  # noqa: BLE001
        code, body = 500, {"err": str(e)}
        atk = "sql_injection"
    emit_log({"payload": pid, "attack_type_hint": atk, "response_code": code, "db_output": body})
    return jsonify(body), code


@app.route("/search")
def search():
    q = request.args.get("q", "")
    atk = classify(request.path, request.query_string.decode(), "")
    # VULNERABLE: reflected XSS (no escaping).
    body = f"<h2>Results for: {q}</h2><p>No products found.</p>"
    emit_log({"payload": q, "attack_type_hint": atk if atk != "benign" else "xss", "response_code": 200})
    return body, 200


@app.route("/api/ping")
def ping():
    """VULNERABLE: command injection via host."""
    host = request.args.get("host", "127.0.0.1")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        out = subprocess.run(f"ping -c 1 -W 1 {host}", shell=True, capture_output=True, text=True, timeout=3).stdout
        code = 200
    except Exception as e:  # noqa: BLE001
        out = f"err: {e}"
        code = 500
    emit_log({"payload": host, "attack_type_hint": atk, "response_code": code, "exec_output": out[:200]})
    return jsonify({"host": host, "output": out})


@app.route("/upload", methods=["POST"])
def upload():
    """VULNERABLE: stores any uploaded file under /tmp/uploads."""
    f = request.files.get("f")
    atk = "file_upload"
    if f is None:
        emit_log({"attack_type_hint": atk, "response_code": 400})
        return "no file", 400
    os.makedirs("/tmp/uploads", exist_ok=True)
    target = os.path.join("/tmp/uploads", os.path.basename(f.filename or "x"))
    f.save(target)
    emit_log({"payload": f.filename, "attack_type_hint": atk, "response_code": 200, "saved_to": target})
    return jsonify({"saved": target, "size": os.path.getsize(target)})


@app.route("/healthz")
def healthz():
    return "ok", 200


@app.errorhandler(404)
def nf(e):
    emit_log({"attack_type_hint": "directory_enum", "response_code": 404})
    return "not found", 404


# ---------------------------------------------------------------------------
init_db()
if __name__ == "__main__":
    print(f"[http] ACME Shop on 0.0.0.0:{LISTEN_PORT}", flush=True)
    app.run(host="0.0.0.0", port=LISTEN_PORT, threaded=True)
