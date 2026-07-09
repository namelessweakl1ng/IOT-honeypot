"""
Telnet honeypot — app.py
------------------------
A minimal raw-socket Telnet server that:
  * Sends a "login:" / "Password:" prompt
  * Accepts admin/admin, root/toor, user/user (logs success)
  * Logs every other attempt as brute force
  * Provides a fake BusyBox shell that logs every command

Pure stdlib — no external deps.
"""
from __future__ import annotations
import os, json, datetime, socket, threading

HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "telnet"
CONTAINER_NAME = "hp-telnet"
LISTEN_PORT = int(os.environ.get("TELNET_PORT", "2323"))

WEAK_CREDS = {("admin", "admin"), ("root", "toor"), ("user", "user"), ("pi", "raspberry")}


def emit_log(event: dict) -> None:
    base = {
        "@timestamp": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "container_name": CONTAINER_NAME,
        "container_service": SERVICE,
        "honeypot_host_ip": HOST_IP,
        "dst_port": LISTEN_PORT,
        "protocol": "Telnet",
    }
    base.update(event)
    print(json.dumps(base, default=str), flush=True)


def recvline(conn: socket.socket, timeout=30) -> str:
    conn.settimeout(timeout)
    buf = b""
    while True:
        try:
            ch = conn.recv(1)
        except socket.timeout:
            return buf.decode("utf-8", "ignore").strip("\r\n")
        if not ch:
            break
        if ch in (b"\n", b"\r"):
            if ch == b"\r":
                try:
                    n = conn.recv(1)
                    if n != b"\n":
                        buf += n
                except Exception:  # noqa: BLE001
                    pass
            break
        buf += ch
    return buf.decode("utf-8", "ignore").strip()


def handle(conn: socket.socket, addr):
    src_ip, src_port = addr
    emit_log({"src_ip": src_ip, "src_port": src_port, "attack_type_hint": "telnet_connect", "response_code": 0})
    try:
        conn.sendall(b"\r\nBCM96338 ADSL Router\r\nlogin: ")
        user = recvline(conn)
        conn.sendall(b"Password: ")
        # Echo off simulation
        pw = recvline(conn)
        ok = (user, pw) in WEAK_CREDS
        emit_log({"src_ip": src_ip, "src_port": src_port, "username": user, "password": pw,
                  "auth_success": ok,
                  "attack_type_hint": "login_success" if ok else "telnet_brute_force",
                  "response_code": 0 if ok else 1})
        if not ok:
            conn.sendall(b"Login incorrect\r\nlogin: ")
            conn.close()
            return
        conn.sendall(b"\r\nBusyBox v1.20.2 () built-in shell (ash)\r\nEnter 'help' for help.\r\n\r\n# ")
        while True:
            cmd = recvline(conn, timeout=60)
            if not cmd:
                break
            emit_log({"src_ip": src_ip, "src_port": src_port, "username": user,
                      "payload": cmd, "attack_type_hint": "telnet_command_exec",
                      "response_code": 0})
            if cmd in ("exit", "quit", "logout"):
                conn.sendall(b"goodbye\r\n")
                break
            conn.sendall(f"sh: {cmd}: not found\r\n# ".encode())
    except Exception as e:  # noqa: BLE001
        emit_log({"src_ip": src_ip, "src_port": src_port, "attack_type_hint": "telnet_error",
                  "error": str(e)[:200]})
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", LISTEN_PORT))
    srv.listen(100)
    print(f"[telnet] honeypot listening on 0.0.0.0:{LISTEN_PORT}", flush=True)
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
