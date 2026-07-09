"""
FTP honeypot — app.py
---------------------
pyftpdlib-based FTP server with weak credentials and per-command logging.
Accepts anonymous + admin/admin, ftp/ftp, root/toor. Every FTP command (USER,
PASS, LIST, RETR, STOR, etc.) is logged as JSON.

The "filesystem" served is a fake read-only tree to keep things contained.
"""
from __future__ import annotations
import os, json, datetime
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

HOST_IP = os.environ.get("HONEYPOT_HOST_IP", "192.168.1.10")
SERVICE = "ftp"
CONTAINER_NAME = "hp-ftp"
LISTEN_PORT = int(os.environ.get("FTP_PORT", "2121"))
FAKE_HOME = "/tmp/ftproot"

# Build a fake FTP tree
os.makedirs(os.path.join(FAKE_HOME, "pub"), exist_ok=True)
os.makedirs(os.path.join(FAKE_HOME, "uploads"), exist_ok=True)
with open(os.path.join(FAKE_HOME, "pub", "readme.txt"), "w") as f:
    f.write("Welcome to the FTP server.\n")
with open(os.path.join(FAKE_HOME, "pub", "config.bak"), "w") as f:
    f.write("router_backup_2023.cfg\nWPA2_KEY=HomeNet2023\n")


def emit_log(event: dict) -> None:
    base = {
        "@timestamp": datetime.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "container_name": CONTAINER_NAME,
        "container_service": SERVICE,
        "honeypot_host_ip": HOST_IP,
        "dst_port": LISTEN_PORT,
        "protocol": "FTP",
    }
    base.update(event)
    print(json.dumps(base, default=str), flush=True)


class HoneypotHandler(FTPHandler):
    banner = "ProFTPD 1.3.5 Server ready."

    def on_connect(self):
        emit_log({"src_ip": self.remote_ip, "src_port": self.remote_port,
                  "attack_type_hint": "ftp_connect", "response_code": 220})

    def on_login(self, username):
        emit_log({"src_ip": self.remote_ip, "src_port": self.remote_port,
                  "username": username, "attack_type_hint": "ftp_login_success",
                  "auth_success": True, "response_code": 230})

    def on_login_failed(self, username, password):
        emit_log({"src_ip": self.remote_ip, "src_port": self.remote_port,
                  "username": username, "password": password,
                  "attack_type_hint": "ftp_brute_force",
                  "auth_success": False, "response_code": 530})

    def on_file_sent(self, file):
        emit_log({"src_ip": self.remote_ip, "src_port": self.remote_port,
                  "username": self.username, "path": file,
                  "attack_type_hint": "ftp_retr", "response_code": 226})

    def on_file_received(self, file):
        emit_log({"src_ip": self.remote_ip, "src_port": self.remote_port,
                  "username": self.username, "path": file,
                  "attack_type_hint": "ftp_stor", "response_code": 226})

    def on_logout(self, username):
        emit_log({"src_ip": self.remote_ip, "src_port": self.remote_port,
                  "username": username, "attack_type_hint": "ftp_logout", "response_code": 221})


def main():
    auth = DummyAuthorizer()
    # Intentionally weak credentials
    auth.add_user("admin", "admin", FAKE_HOME, perm="elr")
    auth.add_user("ftp", "ftp", FAKE_HOME, perm="elr")
    auth.add_user("root", "toor", FAKE_HOME, perm="elradfmw")
    auth.add_anonymous(FAKE_HOME, perm="elr")

    handler = HoneypotHandler
    handler.authorizer = auth
    handler.passive_ports = range(30000, 30011)

    server = FTPServer(("0.0.0.0", LISTEN_PORT), handler)
    server.max_cons = 50
    server.max_cons_per_ip = 10
    print(f"[ftp] honeypot listening on 0.0.0.0:{LISTEN_PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
