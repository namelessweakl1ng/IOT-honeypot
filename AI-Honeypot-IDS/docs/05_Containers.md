# 05 — Containers

This document explains each of the 11 honeypot containers in detail. For the
full per-container README, see `Computer-1-Honeypot/containers/<name>/README.md`.

## 5.1 Container summary table

| # | Service    | Container      | Host port | Ctr port | Vuln class(es)              | Base image        |
|---|------------|----------------|-----------|----------|-----------------------------|-------------------|
| 1 | camera     | hp-camera      | 8081      | 5000     | cmdi, traversal, weak creds | python:3.11-slim  |
| 2 | microwave  | hp-microwave   | 8082      | 5000     | eval() RCE, no auth         | python:3.11-slim  |
| 3 | smarttv    | hp-smarttv     | 8083      | 5000     | SSRF, cmdi, weak creds      | python:3.11-slim  |
| 4 | smartlight | hp-smartlight  | 8084      | 5000     | no-auth, JSON abuse         | python:3.11-slim  |
| 5 | router     | hp-router      | 8085      | 5000     | cmdi, recon, weak creds     | python:3.11-slim  |
| 6 | nas        | hp-nas         | 8086      | 5000     | traversal, cmdi, weak creds | python:3.11-slim  |
| 7 | printer    | hp-printer     | 8087+9100 | 5000+9100| traversal, PJL abuse        | python:3.11-slim  |
| 8 | ssh        | hp-ssh         | 2222      | 2222     | weak creds, fake shell      | python:3.11-slim  |
| 9 | ftp        | hp-ftp         | 2121      | 2121     | weak creds, anon            | python:3.11-slim  |
|10 | http       | hp-http        | 8080      | 5000     | SQLi, cmdi, XSS, upload     | python:3.11-slim  |
|11 | telnet     | hp-telnet      | 2323      | 2323     | weak creds, fake shell      | python:3.11-slim  |

## 5.2 Common patterns

Every container follows the same structural pattern:

```
containers/<name>/
├── Dockerfile      ← python:3.11-slim, non-root user, healthcheck
├── app.py          ← the vulnerable service
├── requirements.txt← Flask/paramiko/pyftpdlib as needed
└── README.md       ← vuln summary + sample attacks
```

Every `app.py` defines an `emit_log()` function that prints one canonical
JSON line per interaction (see `06_Logging.md` for the schema).

## 5.3 Per-container vulnerability catalog

### camera (port 8081)
- Default creds `admin/admin` on `/login`.
- `/streams?id=<X>` → `subprocess.run(f"echo {sid}", shell=True)` → cmdi.
- `/admin?file=<X>` → `open(file)` → path traversal.

### microwave (port 8082)
- No auth on any endpoint.
- `/cook?program=<X>` → `eval(program)` → Python RCE.

### smarttv (port 8083)
- Default creds `admin/1234`.
- `/cast?url=<X>` → `urllib.request.urlopen(url)` → SSRF.
- `/app/install?pkg=<X>` → `subprocess.run(..., shell=True)` → cmdi.

### smartlight (port 8084)
- No auth.
- `/color?hex=<X>` reflects input.
- `/schedule` accepts arbitrary JSON.

### router (port 8085)
- Default creds `admin/password`.
- `/api/wps?pin=<X>` and `/api/diag?host=<X>` shell out → cmdi.
- `/api/config` leaks SSID/firmware → recon.

### nas (port 8086)
- Default creds `admin/admin123`.
- `/api/files?path=<X>` → `open(path)` → traversal.
- `/api/snapshot?name=<X>` → cmdi.
- `/api/share` → recon.

### printer (port 8087 + 9100)
- Default creds `admin/admin`.
- `/admin?file=<X>` → traversal.
- Raw `@PJL` on :9100 → printer abuse.

### ssh (port 2222)
- Banner `SSH-2.0-OpenSSH_8.2p1 Ubuntu`.
- Accepts any password for weak usernames.
- Fake BusyBox shell logs every command.

### ftp (port 2121)
- Banner `ProFTPD 1.3.5`.
- Weak creds `admin/admin`, `ftp/ftp`, `root/toor`.
- Anonymous access.

### http (port 8080)
- "ACME Shop" with SQLite.
- SQLi on `/login`, `/product?id=`.
- Reflected XSS on `/search?q=`.
- Cmdi on `/api/ping?host=`.
- Arbitrary file upload on `/upload`.

### telnet (port 2323)
- Banner `BCM96338 ADSL Router`.
- Weak creds `admin/admin`, `root/toor`, `user/user`, `pi/raspberry`.
- Fake BusyBox shell.

## 5.4 Build order

Compose builds each container independently (no cross-container build deps).
First build takes ~2–3 minutes (downloading python:3.11-slim + pip installs).
Subsequent rebuilds use the layer cache and complete in seconds.

## 5.5 Container isolation

- Each container runs as non-root user `appuser`.
- No container mounts host directories (except Filebeat, which mounts
  `/var/lib/docker/containers` read-only).
- No container has `--privileged`.
- No container uses `network_mode: host`.
- The `honeypot_net` bridge isolates container-to-container traffic from the
  host network.

## 5.6 Adding a 12th container

To add a new honeypot (e.g. a fake RTSP server):

1. `mkdir Computer-1-Honeypot/containers/rtsp`
2. Create `Dockerfile`, `app.py`, `requirements.txt`, `README.md` (copy
   `camera/` as a template).
3. Add a service block to `docker-compose.yml` with the next free IP
   (`172.20.0.22`) and host port (`8088`).
4. Add a healthcheck row to `scripts/healthcheck.sh`.
5. `make build && make up`.

The Logstash pipeline + ML feature engineering pick up new containers
automatically (the `container_service` field is just a categorical feature).
