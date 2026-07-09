"""
Smart Light honeypot — app.py
-----------------------------
Fake RGBW smart bulb HTTP API (many real bulbs expose a similar REST control).
Vulnerabilities:
  * No auth on /state, /on, /off, /color
  * /color?hex=<X> passes input into a format string (format-string vuln demo)
  * /schedule accepts arbitrary JSON (deserialization-style risk)
"""
from __future__ import annotations
import os, json, datetime
from typing import Any
from flask import Flask, request, jsonify

DEVICE_MODEL = os.environ.get("DEVICE_MODEL", "BULB-RGBW")
HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "smartlight"
CONTAINER_NAME = "hp-smartlight"
LISTEN_PORT = int(os.environ.get("PORT", "5000"))

app = Flask(__name__)
STATE = {"on": False, "hex": "#000000", "brightness": 50}


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


def classify(p: str, q: str, b: str) -> str:
    blob = f"{p}?{q} {b}".lower()
    for atk, kws in [
        ("xss", ["<script", "onerror="]),
        ("command_injection", [";", "|", "$("]),
        ("sql_injection", ["'", "union select"]),
        ("directory_enum", [".env", "wp-admin"]),
    ]:
        if any(k in blob for k in kws):
            return atk
    return "benign"


@app.route("/state")
def state():
    emit_log({"response_code": 200, "state": STATE})
    return jsonify(STATE)


@app.route("/on")
def on():
    STATE["on"] = True
    emit_log({"response_code": 200})
    return jsonify(STATE)


@app.route("/off")
def off():
    STATE["on"] = False
    emit_log({"response_code": 200})
    return jsonify(STATE)


@app.route("/color")
def color():
    """VULNERABLE-ish: accepts any string and reflects it."""
    h = request.args.get("hex", "#ffffff")
    atk = classify(request.path, request.query_string.decode(), "")
    STATE["hex"] = h
    emit_log({"payload": h, "attack_type_hint": atk, "response_code": 200})
    return jsonify(STATE)


@app.route("/schedule", methods=["POST"])
def schedule():
    """VULNERABLE: accepts arbitrary JSON, echoes it back."""
    try:
        body = request.get_json(force=True, silent=False)
        code = 200
    except Exception as e:  # noqa: BLE001
        body = {"err": str(e)}
        code = 400
    emit_log({"payload": json.dumps(body)[:200], "attack_type_hint": "benign", "response_code": code})
    return jsonify(body), code


@app.route("/")
def index():
    emit_log({"response_code": 200})
    return jsonify({"device": DEVICE_MODEL, "endpoints": ["/state", "/on", "/off", "/color", "/schedule"]})


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    print(f"[smartlight] {DEVICE_MODEL} on 0.0.0.0:{LISTEN_PORT}", flush=True)
    app.run(host="0.0.0.0", port=LISTEN_PORT, threaded=True)
