"""
SSH honeypot — app.py
---------------------
A minimal SSH server (paramiko-based) that:
  * Presents a banner that looks like OpenSSH on Ubuntu
  * Accepts ANY password for known weak usernames (admin, root, pi, user, etc.)
  * Logs every auth attempt with username, password, client IP/port, key type
  * Provides a fake interactive shell that logs every command (no real exec)

This is intentionally a low-interaction honeypot — enough to capture brute
force and credential-stuffing, not enough to give a real shell.

DO NOT EXPOSE TO THE INTERNET.
"""
from __future__ import annotations
import os, json, datetime, socket, threading, logging
import paramiko

HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "ssh"
CONTAINER_NAME = "hp-ssh"
LISTEN_PORT = int(os.environ.get("SSH_PORT", "2222"))

# Suppress paramiko's noisy internal logging
logging.getLogger("paramiko").setLevel(logging.WARNING)

# Weak credentials that the honeypot will "accept" (it logs success but never
# gives a real shell).
WEAK_USERS = {"admin", "root", "pi", "user", "ubuntu", "test", "guest", "support", "service", "oracle"}
WEAK_PASS_ANY = True  # accept ANY password for a weak username (for the demo)

HOST_KEY = paramiko.RSAKey.generate(2048)


def emit_log(event: dict) -> None:
    base = {
        "@timestamp": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "container_name": CONTAINER_NAME,
        "container_service": SERVICE,
        "honeypot_host_ip": HOST_IP,
        "dst_port": LISTEN_PORT,
        "protocol": "SSH",
    }
    base.update(event)
    print(json.dumps(base, default=str), flush=True)


class HoneypotServer(paramiko.ServerInterface):
    def __init__(self, client_addr):
        self.client_ip, self.client_port = client_addr
        self.authenticated = False
        self.username = None

    def check_auth_password(self, username, password):
        ok = WEAK_PASS_ANY and username in WEAK_USERS
        self.username = username
        emit_log({
            "src_ip": self.client_ip, "src_port": self.client_port,
            "username": username, "password": password,
            "auth_success": ok,
            "attack_type_hint": "login_success" if ok else "ssh_brute_force",
            "response_code": 0 if ok else 1,
        })
        if ok:
            self.authenticated = True
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        emit_log({
            "src_ip": self.client_ip, "src_port": self.client_port,
            "username": username, "key_type": key.get_name(),
            "key_fingerprint": key.get_fingerprint().hex(),
            "auth_success": False,
            "attack_type_hint": "ssh_key_attempt",
            "response_code": 1,
        })
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        cmd = command.decode("utf-8", "ignore")
        emit_log({
            "src_ip": self.client_ip, "src_port": self.client_port,
            "username": self.username, "payload": cmd,
            "attack_type_hint": "ssh_command_injection",
            "response_code": 0,
        })
        # Reject exec so attackers fall back to shell, which we log per command.
        return False


def handle_client(conn: socket.socket, addr):
    try:
        transport = paramiko.Transport(conn)
        transport.local_version = "SSH-2.0-OpenSSH_8.2p1 Ubuntu-4ubuntu0.5"
        transport.add_server_key(HOST_KEY)
        server = HoneypotServer(addr)
        transport.start_server(server=server)
        chan = transport.accept(20)
        if chan is None:
            return
        chan.send(b"Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0 x86_64)\r\n")
        chan.send(b"Last login: never\r\n")
        chan.send(b"$ ")
        buf = b""
        while True:
            data = chan.recv(1024)
            if not data:
                break
            buf += data
            if b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                cmd = line.decode("utf-8", "ignore").strip()
                emit_log({
                    "src_ip": addr[0], "src_port": addr[1],
                    "username": server.username, "payload": cmd,
                    "attack_type_hint": "ssh_command_exec",
                    "response_code": 0,
                })
                chan.send(f"command not found: {cmd}\r\n$ ".encode())
        chan.close()
    except Exception as e:  # noqa: BLE001
        emit_log({"src_ip": addr[0], "src_port": addr[1], "attack_type_hint": "ssh_protocol_error",
                  "error": str(e)[:200]})
    finally:
        try:
            transport.close()  # type: ignore[name-defined]
        except Exception:  # noqa: BLE001
            pass


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", LISTEN_PORT))
    srv.listen(100)
    print(f"[ssh] honeypot listening on 0.0.0.0:{LISTEN_PORT}", flush=True)
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()


if __name__ == "__main__":
    main()
