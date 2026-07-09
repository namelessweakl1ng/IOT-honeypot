"""
Router Login Panel honeypot — app.py
------------------------------------
Fake ISP router admin panel. Vulnerabilities:
  * Default creds admin / password
  * /api/wps?pin=<X> reflects pin into a shell command (cmd injection)
  * /api/diag?host=<X> pings user-supplied host (cmd injection)
  * No CSRF, no rate limit — perfect for brute-force demos
"""
from __future__ import annotations
import os, json, datetime, subprocess
from typing import Any
from flask import Flask, request, jsonify, render_template_string

DEFAULT_USER = os.environ.get("DEFAULT_USER", "admin")
DEFAULT_PASS = os.environ.get("DEFAULT_PASS", "password")
HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "router"
CONTAINER_NAME = "hp-router"
LISTEN_PORT = int(os.environ.get("PORT", "5000"))

app = Flask(__name__)
SESSIONS: dict[str, str] = {}

INDEX = """<!doctype html><html><head><title>Router Admin</title></head>
<body><h1>AC1900 Router</h1>
<form method='POST' action='/login'>u:<input name='u'>p:<input name='p' type='password'><button>Login</button></form>
<p>Default credentials: admin / password</p></body></html>"""


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
        ("command_injection", [";", "|", "$(", "`", "/bin/sh", "&&"]),
        ("sql_injection", ["'", "union select", " or 1=1"]),
        ("xss", ["<script", "onerror="]),
        ("brute_force", ["password=", "passwd="]),
        ("directory_enum", [".env", "wp-admin", "/admin/"]),
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
    return ("Welcome admin" if ok else "Bad credentials"), (200 if ok else 401)


@app.route("/api/wps")
def wps():
    """VULNERABLE: cmd injection via pin."""
    pin = request.args.get("pin", "00000000")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        out = subprocess.run(f"wps_pin {pin}", shell=True, capture_output=True, text=True, timeout=3).stdout
        code = 200
    except Exception as e:  # noqa: BLE001
        out = f"err: {e}"
        code = 400
    emit_log({"payload": pin, "attack_type_hint": atk, "response_code": code, "exec_output": out[:200]})
    return jsonify({"pin": pin, "output": out})


@app.route("/api/diag")
def diag():
    """VULNERABLE: cmd injection via host."""
    host = request.args.get("host", "127.0.0.1")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        out = subprocess.run(f"ping -c 1 {host}", shell=True, capture_output=True, text=True, timeout=3).stdout
        code = 200
    except Exception as e:  # noqa: BLE001
        out = f"err: {e}"
        code = 400
    emit_log({"payload": host, "attack_type_hint": atk, "response_code": code, "exec_output": out[:200]})
    return jsonify({"host": host, "output": out})


@app.route("/api/config")
def config():
    """Leaks 'config' — useful for attackers doing recon."""
    emit_log({"response_code": 200, "attack_type_hint": "recon"})
    return jsonify({"ssid": "HomeNet", "wpa2": "psk", "dhcp": True, "fw": "1.0.3"})


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    print(f"[router] panel on 0.0.0.0:{LISTEN_PORT}", flush=True)
    app.run(host="0.0.0.0", port=LISTEN_PORT, threaded=True)
