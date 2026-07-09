"""
=============================================================================
CCTV Camera honeypot — app.py
=============================================================================
Emulates an IP camera web panel with the classic 'admin/admin' default creds
and a hidden /streams endpoint that reflects any ?id= straight into a fake
RTSP URL (command-injection prone shell-out for demo).

EVERY HTTP interaction is logged as one JSON line to stdout with the canonical
honeypot schema (see docs/06_Logging.md). Filebeat picks up stdout and ships
to Computer 2.

VULNERABILITIES (intentional, for the lab):
  1.  Hardcoded default creds admin / admin  (login.html form, no rate limit)
  2.  /streams?id=<X> uses os.system to "probe" the stream → command injection
  3.  /admin/firmware path traversal via ?file=../../etc/passwd
  4.  No HTTPS, no CSRF token, verbose error messages

DO NOT EXPOSE TO THE INTERNET.
=============================================================================
"""
from __future__ import annotations
import os
import json
import time
import socket
import subprocess
import datetime
from typing import Any

from flask import Flask, request, jsonify, render_template_string, abort

# ---------------------------------------------------------------------------
# Configuration (all overridable via env)
# ---------------------------------------------------------------------------
DEVICE_MODEL = os.environ.get("DEVICE_MODEL", "IP-CAM-1080P")
DEFAULT_USER = os.environ.get("DEFAULT_USER", "admin")
DEFAULT_PASS = os.environ.get("DEFAULT_PASS", "admin")
HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "camera"
CONTAINER_NAME = "hp-camera"
LISTEN_PORT = int(os.environ.get("PORT", "5000"))

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Logging helper — emits ONE JSON line per interaction to stdout
# ---------------------------------------------------------------------------
def emit_log(event: dict[str, Any]) -> None:
    """Emit a structured JSON log line. Filebeat parses stdout JSON."""
    base = {
        "@timestamp": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "container_name": CONTAINER_NAME,
        "container_service": SERVICE,
        "device_model": DEVICE_MODEL,
        "honeypot_host_ip": HOST_IP,
        "src_ip": request.remote_addr or "0.0.0.0",
        "src_port": request.environ.get("REMOTE_PORT"),
        "dst_port": LISTEN_PORT,
        "protocol": "HTTP",
        "method": request.method,
        "path": request.path,
        "query": request.query_string.decode("utf-8", "ignore"),
        "user_agent": request.headers.get("User-Agent", ""),
        "host_header": request.host,
        "attack_type_hint": "benign",
    }
    base.update(event)
    print(json.dumps(base, default=str), flush=True)


def classify(path: str, query: str, body: str) -> str:
    """Cheap heuristic to hint at attack type — used for ML labeling later."""
    blob = f"{path}?{query} {body}".lower()
    rules = [
        ("sql_injection", ["'", " or 1=1", "union select", "sleep(", "--", "information_schema"]),
        ("command_injection", [";", "|", "&", "$(", "`", "/bin/sh", "cat /etc/passwd"]),
        ("path_traversal", ["../", "..\\", "/etc/passwd", "%2e%2e"]),
        ("xss", ["<script", "onerror=", "javascript:", "<img src=x"]),
        ("brute_force_login", ["password=", "passwd=", "login="]),
        ("directory_enum", [".git/", ".env", "wp-admin", "phpmyadmin", "admin.php"]),
    ]
    for atk, keywords in rules:
        if any(k in blob for k in keywords):
            return atk
    return "benign"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
INDEX_HTML = """
<!doctype html>
<html><head><title>{{model}} — CCTV Camera</title></head>
<body>
  <h1>{{model}}</h1>
  <p>Firmware v1.0 (build 2019-04)</p>
  <form method='POST' action='/login'>
    User: <input name='u'><br>
    Pass: <input name='p' type='password'><br>
    <button>Login</button>
  </form>
  <a href='/streams'>Live streams</a> |
  <a href='/admin'>Admin</a>
</body></html>
"""


@app.route("/")
def index():
    emit_log({"attack_type_hint": "benign", "response_code": 200})
    return render_template_string(INDEX_HTML, model=DEVICE_MODEL)


@app.route("/login", methods=["GET", "POST"])
def login():
    user = request.form.get("u", request.args.get("u", ""))
    pw = request.form.get("p", request.args.get("p", ""))
    atk = classify(request.path, request.query_string.decode(), f"u={user}&p={pw}")
    ok = (user == DEFAULT_USER and pw == DEFAULT_PASS)
    emit_log({
        "username": user,
        "password": pw,
        "attack_type_hint": atk if not ok else "login_success",
        "auth_success": ok,
        "response_code": 200 if ok else 401,
    })
    return ("Welcome admin" if ok else "Bad credentials"), (200 if ok else 401)


@app.route("/streams")
def streams():
    """VULNERABLE: command injection via the `id` param into os.system."""
    sid = request.args.get("id", "1")
    atk = classify(request.path, request.query_string.decode(), "")
    # Intentionally unsafe: this is what the honeypot is FOR.
    try:
        result = subprocess.run(
            f"echo 'probing stream {sid}'",
            shell=True, capture_output=True, text=True, timeout=3,
        )
        out = result.stdout
    except Exception as e:  # noqa: BLE001
        out = f"err: {e}"
    emit_log({
        "payload": sid,
        "attack_type_hint": atk,
        "response_code": 200,
        "exec_output": out[:200],
    })
    return jsonify({"stream_id": sid, "status": "live", "probe": out})


@app.route("/admin")
@app.route("/admin/firmware")
def admin():
    """VULNERABLE: path traversal via ?file=."""
    f = request.args.get("file", "index.html")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        # Intentionally vulnerable read.
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()[:500]
        code = 200
    except Exception as e:  # noqa: BLE001
        content = f"err: {e}"
        code = 404
    emit_log({
        "payload": f,
        "attack_type_hint": atk,
        "response_code": code,
    })
    return content, code


@app.route("/healthz")
def healthz():
    return "ok", 200


@app.errorhandler(404)
def not_found(e):
    emit_log({"attack_type_hint": "directory_enum", "response_code": 404})
    return "not found", 404


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 0.0.0.0 so the attacker can reach us through the published port
    print(f"[camera] {DEVICE_MODEL} listening on 0.0.0.0:{LISTEN_PORT}", flush=True)
    app.run(host="0.0.0.0", port=LISTEN_PORT, threaded=True)
