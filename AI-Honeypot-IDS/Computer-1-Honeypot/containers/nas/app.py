"""
NAS Storage honeypot — app.py
-----------------------------
Fake NAS web UI. Vulnerabilities:
  * Default creds admin / admin123
  * /api/files?path=<X> path traversal — reads any host file
  * /api/share exposes a fake file listing (info disclosure)
  * /api/snapshot?name=<X> reflects into a shell (cmd injection)
"""
from __future__ import annotations
import os, json, datetime, subprocess
from typing import Any
from flask import Flask, request, jsonify, render_template_string

DEFAULT_USER = os.environ.get("DEFAULT_USER", "admin")
DEFAULT_PASS = os.environ.get("DEFAULT_PASS", "admin123")
HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "nas"
CONTAINER_NAME = "hp-nas"
LISTEN_PORT = int(os.environ.get("PORT", "5000"))

app = Flask(__name__)
FAKE_FILES = ["/docs", "/photos", "/backups", "/music", "/public"]

INDEX = """<!doctype html><html><head><title>NAS</title></head>
<body><h1>NAS Storage DS-220</h1>
<form method='POST' action='/login'>u:<input name='u'>p:<input name='p' type='password'><button>Login</button></form>
<a href='/api/share'>Shares</a> | <a href='/api/files?path=/docs'>Files</a></body></html>"""


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
        ("path_traversal", ["../", "..\\", "/etc/passwd", "%2e%2e"]),
        ("command_injection", [";", "|", "$(", "`"]),
        ("sql_injection", ["'", "union select"]),
        ("brute_force", ["password=", "passwd="]),
    ]:
        if any(k in blob for k in kws):
            return atk
    return "benign"


@app.route("/")
def index():
    emit_log({"response_code": 200})
    return render_template_string(INDEX)


@app.route("/login", methods=["GET", "POST"])
def login():
    u = request.values.get("u", "")
    p = request.values.get("p", "")
    atk = classify(request.path, request.query_string.decode(), f"u={u}&p={p}")
    ok = (u == DEFAULT_USER and p == DEFAULT_PASS)
    emit_log({"username": u, "password": p, "attack_type_hint": atk if not ok else "login_success",
              "auth_success": ok, "response_code": 200 if ok else 401})
    return ("OK" if ok else "Bad"), (200 if ok else 401)


@app.route("/api/files")
def files():
    """VULNERABLE: path traversal via ?path=."""
    path = request.args.get("path", "/docs")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        # Intentionally vulnerable — no normalization.
        if path.startswith("/"):
            target = path
        else:
            target = os.path.join("/app", path)
        with open(target, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()[:500]
        code = 200
    except Exception as e:  # noqa: BLE001
        content = f"err: {e}"
        code = 404
    emit_log({"payload": path, "attack_type_hint": atk, "response_code": code, "file_content": content[:200]})
    return content, code


@app.route("/api/share")
def share():
    emit_log({"response_code": 200, "attack_type_hint": "recon"})
    return jsonify({"shares": FAKE_FILES})


@app.route("/api/snapshot")
def snapshot():
    """VULNERABLE: cmd injection via name."""
    name = request.args.get("name", "snap1")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        out = subprocess.run(f"echo snapshot {name}", shell=True, capture_output=True, text=True, timeout=3).stdout
        code = 200
    except Exception as e:  # noqa: BLE001
        out = f"err: {e}"
        code = 400
    emit_log({"payload": name, "attack_type_hint": atk, "response_code": code, "exec_output": out[:200]})
    return jsonify({"snapshot": name, "output": out})


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    print(f"[nas] DS-220 on 0.0.0.0:{LISTEN_PORT}", flush=True)
    app.run(host="0.0.0.0", port=LISTEN_PORT, threaded=True)
