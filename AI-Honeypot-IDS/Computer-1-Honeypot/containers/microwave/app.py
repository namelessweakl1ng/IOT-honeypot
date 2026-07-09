"""
Smart Microwave honeypot — app.py
---------------------------------
Fake REST API for a smart microwave. Vulnerabilities:
  * No authentication on /cook (anyone can start the microwave)
  * /cook?program=<X> reflects the program name into an eval() — RCE
  * /timer accepts arbitrary negative numbers (DoS / overflow)
Logs every request as JSON.
"""
from __future__ import annotations
import os, json, datetime
from typing import Any
from flask import Flask, request, jsonify

DEVICE_MODEL = os.environ.get("DEVICE_MODEL", "MW-X200")
HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "microwave"
CONTAINER_NAME = "hp-microwave"
LISTEN_PORT = int(os.environ.get("PORT", "5000"))

app = Flask(__name__)
STATE = {"power": 800, "timer": 0, "running": False, "door_closed": True}


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
        ("command_injection", ["__import__", "os.system", "eval", "exec", "subprocess"]),
        ("sql_injection", ["'", " or 1=1", "union select", "--"]),
        ("xss", ["<script", "onerror="]),
        ("brute_force", ["password=", "passwd="]),
    ]
    for atk, kws in rules:
        if any(k in blob for k in kws):
            return atk
    return "benign"


@app.route("/status")
def status():
    emit_log({"response_code": 200, "state": STATE})
    return jsonify(STATE)


@app.route("/cook", methods=["GET", "POST"])
def cook():
    """VULNERABLE: program param is eval()'d — Python code injection."""
    program = request.values.get("program", "popcorn")
    timer = request.values.get("timer", "60")
    atk = classify(request.path, request.query_string.decode(), f"program={program}&timer={timer}")
    out = ""
    try:
        # Intentionally vulnerable — NEVER do this in real code.
        out = str(eval(program))  # noqa: S307
        STATE["running"] = True
        STATE["timer"] = int(timer)
        code = 200
    except Exception as e:  # noqa: BLE001
        out = f"err: {e}"
        code = 400
    emit_log({
        "payload": program,
        "attack_type_hint": atk,
        "response_code": code,
        "eval_output": out[:200],
    })
    return jsonify({"started": True, "program": program, "timer": timer, "result": out})


@app.route("/door", methods=["POST"])
def door():
    STATE["door_closed"] = request.values.get("closed", "true") == "true"
    emit_log({"response_code": 200, "door_closed": STATE["door_closed"]})
    return jsonify(STATE)


@app.route("/")
def index():
    emit_log({"response_code": 200})
    return jsonify({"device": DEVICE_MODEL, "endpoints": ["/status", "/cook", "/door"]})


@app.route("/healthz")
def healthz():
    return "ok", 200


if __name__ == "__main__":
    print(f"[microwave] {DEVICE_MODEL} on 0.0.0.0:{LISTEN_PORT}", flush=True)
    app.run(host="0.0.0.0", port=LISTEN_PORT, threaded=True)
