"""
Smart TV honeypot — app.py
--------------------------
Fake smart-TV control panel. Vulnerabilities:
  * /cast?url=<X> fetches arbitrary URLs (SSRF)
  * /app/install?pkg=<X> writes pkg name into a shell command (cmd injection)
  * Default creds: admin / 1234
Logs every interaction as JSON.
"""
from __future__ import annotations
import os, json, datetime, subprocess, urllib.request
from typing import Any
from flask import Flask, request, jsonify, render_template_string

DEVICE_MODEL = os.environ.get("DEVICE_MODEL", "TV-OLED-55")
DEFAULT_USER = os.environ.get("DEFAULT_USER", "admin")
DEFAULT_PASS = os.environ.get("DEFAULT_PASS", "1234")
HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "smarttv"
CONTAINER_NAME = "hp-smarttv"
LISTEN_PORT = int(os.environ.get("PORT", "5000"))

app = Flask(__name__)
APPS_INSTALLED = ["netflix", "youtube", "prime"]


def emit_log(event: dict[str, Any]) -> None:
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
        "attack_type_hint": "benign",
    }
    base.update(event)
    print(json.dumps(base, default=str), flush=True)


def classify(path: str, query: str, body: str) -> str:
    blob = f"{path}?{query} {body}".lower()
    rules = [
        ("ssrf", ["url=http", "url=ftp", "url=file", "url=gopher"]),
        ("command_injection", [";", "|", "$(", "`", "/bin/sh"]),
        ("sql_injection", ["'", "union select", " or 1=1"]),
        ("xss", ["<script", "onerror="]),
        ("brute_force", ["password=", "passwd="]),
    ]
    for atk, kws in rules:
        if any(k in blob for k in kws):
            return atk
    return "benign"


INDEX = """<!doctype html><html><head><title>{{model}}</title></head>
<body><h1>{{model}}</h1>
<p>Apps: {{apps}}</p>
<form method='POST' action='/login'>u:<input name='u'>p:<input name='p' type='password'><button>OK</button></form>
<a href='/cast?url=http://example.com'>Cast</a> |
<a href='/app/install?pkg=demo'>Install app</a>
</body></html>"""


@app.route("/")
def index():
    emit_log({"response_code": 200})
    return render_template_string(INDEX, model=DEVICE_MODEL, apps=",".join(APPS_INSTALLED))


@app.route("/login", methods=["GET", "POST"])
def login():
    u = request.values.get("u", "")
    p = request.values.get("p", "")
    atk = classify(request.path, request.query_string.decode(), f"u={u}&p={p}")
    ok = (u == DEFAULT_USER and p == DEFAULT_PASS)
    emit_log({"username": u, "password": p, "attack_type_hint": atk if not ok else "login_success",
              "auth_success": ok, "response_code": 200 if ok else 401})
    return ("OK" if ok else "Bad"), (200 if ok else 401)


@app.route("/cast")
def cast():
    """VULNERABLE: SSRF — server fetches attacker-supplied URL."""
    url = request.args.get("url", "")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        # Intentionally vulnerable: classic SSRF.
        with urllib.request.urlopen(url, timeout=3) as r:
            body = r.read(500)
        code = 200
    except Exception as e:  # noqa: BLE001
        body = f"err: {e}".encode()
        code = 502
    emit_log({"payload": url, "attack_type_hint": atk, "response_code": code,
              "ssrf_response": body[:200].decode("utf-8", "ignore")})
    return body, code


@app.route("/app/install")
def install():
    """VULNERABLE: cmd injection via pkg param."""
    pkg = request.args.get("pkg", "")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        out = subprocess.run(f"echo installing {pkg}", shell=True, capture_output=True,
                             text=True, timeout=3).stdout
        APPS_INSTALLED.append(pkg)
        code = 200
    except Exception as e:  # noqa: BLE001
        out = f"err: {e}"
        code = 400
    emit_log({"payload": pkg, "attack_type_hint": atk, "response_code": code, "exec_output": out[:200]})
    return jsonify({"installed": pkg, "output": out})


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    print(f"[smarttv] {DEVICE_MODEL} on 0.0.0.0:{LISTEN_PORT}", flush=True)
    app.run(host="0.0.0.0", port=LISTEN_PORT, threaded=True)
