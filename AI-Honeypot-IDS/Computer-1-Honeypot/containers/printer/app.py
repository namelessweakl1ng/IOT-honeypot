"""
Printer honeypot — app.py
-------------------------
Emulates an HP-style network printer with two surfaces:
  1. Web UI on :5000 (default creds admin/admin, /admin?file= path traversal)
  2. Raw JetDirect/PJL on :9100 (classic printer attack surface)
Vulnerabilities:
  * Default creds on web UI
  * /admin?file=<X> path traversal
  * PJL on :9100 accepts @PJL commands including filesystem reads
"""
from __future__ import annotations
import os, json, datetime, socket, threading
from typing import Any
from flask import Flask, request, jsonify, render_template_string

DEFAULT_USER = os.environ.get("DEFAULT_USER", "admin")
DEFAULT_PASS = os.environ.get("DEFAULT_PASS", "admin")
HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "printer"
CONTAINER_NAME = "hp-printer"
LISTEN_PORT = int(os.environ.get("PORT", "5000"))
PJL_PORT = 9100

app = Flask(__name__)

INDEX = """<!doctype html><html><head><title>HP Printer</title></head>
<body><h1>HP LaserJet Pro</h1>
<form method='POST' action='/login'>u:<input name='u'>p:<input name='p' type='password'><button>Login</button></form>
<a href='/admin?file=index.html'>Admin</a> | <a href='/status'>Status</a></body></html>"""


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


def emit_pjl_log(src_ip: str, src_port: int, payload: str) -> None:
    print(json.dumps({
        "@timestamp": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "container_name": CONTAINER_NAME,
        "container_service": SERVICE,
        "honeypot_host_ip": HOST_IP,
        "src_ip": src_ip, "src_port": src_port, "dst_port": PJL_PORT,
        "protocol": "PJL", "method": "RAW",
        "payload": payload[:500],
        "attack_type_hint": "printer_abuse",
        "response_code": 0,
    }, default=str), flush=True)


def classify(p: str, q: str, b: str) -> str:
    blob = f"{p}?{q} {b}".lower()
    for atk, kws in [
        ("path_traversal", ["../", "..\\", "/etc/passwd"]),
        ("command_injection", [";", "|", "$("]),
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


@app.route("/admin")
def admin():
    """VULNERABLE: path traversal."""
    f = request.args.get("file", "index.html")
    atk = classify(request.path, request.query_string.decode(), "")
    try:
        with open(f, "r", encoding="utf-8", errors="ignore") as fh:
            content = fh.read()[:500]
        code = 200
    except Exception as e:  # noqa: BLE001
        content = f"err: {e}"
        code = 404
    emit_log({"payload": f, "attack_type_hint": atk, "response_code": code, "file_content": content[:200]})
    return content, code


@app.route("/status")
def status():
    emit_log({"response_code": 200, "attack_type_hint": "recon"})
    return jsonify({"model": "HP LaserJet Pro", "toner": 73, "tray1": "A4", "ip": HOST_IP})


@app.route("/healthz")
def healthz():
    return "ok", 200


# ---------------------------------------------------------------------------
# Raw PJL listener on :9100 — runs in a background thread.
# ---------------------------------------------------------------------------
def pjl_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", PJL_PORT))
    srv.listen(50)
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_pjl, args=(conn, addr), daemon=True).start()


def handle_pjl(conn: socket.socket, addr):
    src_ip, src_port = addr[0], addr[1]
    buf = b""
    try:
        conn.settimeout(3)
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf += chunk
            if b"\n" in chunk:
                break
    except socket.timeout:
        pass
    finally:
        try:
            conn.sendall(b"\x1b%-12345X@PJL OK\n")
        except Exception:  # noqa: BLE001
            pass
        conn.close()
    emit_pjl_log(src_ip, src_port, buf.decode("utf-8", "ignore"))


# Start PJL listener before Flask
threading.Thread(target=pjl_server, daemon=True).start()

if __name__ == "__main__":
    print(f"[printer] web on :{LISTEN_PORT}, PJL on :{PJL_PORT}", flush=True)
    app.run(host="0.0.0.0", port=LISTEN_PORT, threaded=True)
