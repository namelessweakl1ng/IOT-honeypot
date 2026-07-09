# Computer 1 — Honeypot Server

> **Presenter notes for the Computer 1 team member.**
> This document is detailed enough to be printed and used as speaking notes
> during the viva and the final project demonstration.
>
> ⚠️ **EDUCATIONAL USE ONLY.** Run this honeypot only inside the air-gapped
> `192.168.1.0/24` lab. Never expose these containers to the Internet.

---

## 1. Role of Computer 1

Computer 1 is the **deception layer** of the project. It hosts 11 Docker
containers that emulate vulnerable IoT devices and common network services.
Every interaction — benign or malicious — is captured as a structured JSON
log line and forwarded in real time to Computer 2 (the SIEM).

The honeypot has **no production value**. By definition, any traffic it
receives is suspicious, which makes the resulting log data extremely clean for
training a machine-learning intrusion detector.

---

## 2. Hardware & OS

| Item         | Spec                                   |
|--------------|----------------------------------------|
| CPU          | 4 cores x86_64                         |
| RAM          | 8 GB                                   |
| Disk         | 40 GB SSD                              |
| NIC          | 1 GbE                                  |
| OS           | Ubuntu Server 22.04 LTS (minimal)      |
| IP (static)  | 192.168.1.10/24                        |
| Gateway      | 192.168.1.1                            |

Ubuntu Server is chosen over Desktop because there is no GUI requirement on
the honeypot — every administration task is performed over SSH.

---

## 3. Folder structure (every file explained)

```
Computer-1-Honeypot/
├── README.md                  ← this file (presenter notes)
├── docker-compose.yml         ← defines all 11 services + filebeat
├── .env.example               ← environment variables template
├── Makefile                   ← convenience targets (up/down/status/...)
├── containers/                ← one folder per emulated device
│   ├── camera/                ← CCTV web panel (port 8081)
│   │   ├── Dockerfile
│   │   ├── app.py             ← Flask app with cmd-injection + path traversal
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── microwave/             ← Smart Microwave REST API (8082, eval() RCE)
│   ├── smarttv/               ← Smart TV panel (8083, SSRF + cmd injection)
│   ├── smartlight/            ← Smart Light API (8084, no-auth)
│   ├── router/                ← Router login panel (8085, cmd injection)
│   ├── nas/                   ← NAS web UI (8086, path traversal)
│   ├── printer/               ← Printer web (8087) + raw PJL (9100)
│   ├── ssh/                   ← SSH honeypot (2222, paramiko)
│   ├── ftp/                   ← FTP honeypot (2121, pyftpdlib)
│   ├── http/                  ← Vulnerable web app (8080, SQLi/cmdi/XSS)
│   └── telnet/                ← Telnet honeypot (2323, raw socket)
├── configs/
│   ├── filebeat.yml           ← Filebeat config (autodiscover + logstash output)
│   └── filebeat-logging.conf  ← Filebeat internal logging config
├── scripts/
│   ├── start.sh               ← validates env, builds, starts, waits for health
│   ├── stop.sh                ← docker compose down
│   ├── status.sh              ← shows container + filebeat status
│   ├── healthcheck.sh         ← curls/probes every service
│   └── seed-traffic.sh        ← generates benign baseline traffic
└── logs/
    ├── README.md              ← explains logs are centralized, not local
    └── .gitkeep
```

---

## 4. The 11 containers (each one explained)

For each container we describe: what it emulates, the published port, the
intentional vulnerabilities, the logs it produces, and a sample attack.

### 4.1 CCTV Camera (`hp-camera`) — port 8081

- **Emulates:** IP camera web panel (`IP-CAM-1080P`).
- **Vulnerabilities:** default creds `admin/admin`; `/streams?id=` runs
  `subprocess.run(..., shell=True)` → command injection; `/admin?file=` reads
  arbitrary files → path traversal.
- **Logs:** every HTTP request as JSON with `username`, `password`, `payload`,
  `attack_type_hint`, `response_code`.
- **Sample attack:** `curl 'http://192.168.1.10:8081/streams?id=1;id'`

### 4.2 Smart Microwave (`hp-microwave`) — port 8082

- **Emulates:** smart microwave REST API.
- **Vulnerabilities:** no auth; `/cook?program=` is passed to `eval()` →
  Python code injection.
- **Sample attack:**
  `curl 'http://192.168.1.10:8082/cook?program=__import__("os").popen("id").read()'`

### 4.3 Smart TV (`hp-smarttv`) — port 8083

- **Emulates:** smart TV control panel.
- **Vulnerabilities:** SSRF on `/cast?url=` (server fetches attacker URL);
  command injection on `/app/install?pkg=`; default creds `admin/1234`.

### 4.4 Smart Light (`hp-smartlight`) — port 8084

- **Emulates:** RGBW smart bulb REST API.
- **Vulnerabilities:** no auth on any endpoint; `/color?hex=` reflects input;
  `/schedule` accepts arbitrary JSON.

### 4.5 Router Login Panel (`hp-router`) — port 8085

- **Emulates:** ISP router admin panel (`AC1900`).
- **Vulnerabilities:** default creds `admin/password`; `/api/wps?pin=` and
  `/api/diag?host=` shell out → command injection; `/api/config` leaks SSID,
  firmware version, WPA mode (recon).

### 4.6 NAS Storage (`hp-nas`) — port 8086

- **Emulates:** NAS web UI (`DS-220`).
- **Vulnerabilities:** default creds `admin/admin123`; `/api/files?path=` →
  path traversal (reads `/etc/passwd`); `/api/snapshot?name=` → command
  injection; `/api/share` leaks share list.

### 4.7 Printer (`hp-printer`) — ports 8087 + 9100

- **Emulates:** HP LaserJet Pro with web UI and raw PJL.
- **Vulnerabilities:** default creds `admin/admin`; `/admin?file=` → path
  traversal; raw `@PJL` on port 9100 accepts filesystem-read commands (the
  classic printer abuse class).

### 4.8 SSH (`hp-ssh`) — port 2222

- **Emulates:** OpenSSH 8.2p1 on Ubuntu.
- **Vulnerabilities:** accepts ANY password for weak usernames
  (`admin, root, pi, user, ubuntu, test, guest, support, service, oracle`).
- **Post-auth:** fake BusyBox shell logs every command (no real exec).
- **Logs:** auth attempts, public-key attempts, exec requests, shell commands.

### 4.9 FTP (`hp-ftp`) — port 2121 (passive 30000-30010)

- **Emulates:** ProFTPD 1.3.5.
- **Vulnerabilities:** weak creds `admin/admin`, `ftp/ftp`, `root/toor`,
  anonymous access.
- **Logs:** connect, login success/failure, RETR, STOR, logout.

### 4.10 HTTP Vulnerable Web App (`hp-http`) — port 8080

The **primary attack target**. "ACME Shop" with a SQLite backend.
- **Vulnerabilities:**
  - SQLi on `/login` and `/product?id=` (string-built queries)
  - Reflected XSS on `/search?q=`
  - Command injection on `/api/ping?host=`
  - Arbitrary file upload on `/upload`
- **Seeded users:** `admin/s3cr3t`, `alice/alicepw`, `bob/bobpw`.

### 4.11 Telnet (`hp-telnet`) — port 2323

- **Emulates:** BCM96338 ADSL router with BusyBox shell.
- **Vulnerabilities:** weak creds `admin/admin`, `root/toor`, `user/user`,
  `pi/raspberry`.
- **Logs:** every login attempt and every post-auth command.

---

## 5. Logging architecture

### 5.1 Log schema (canonical JSON)

Every container emits ONE JSON line per interaction to stdout. Filebeat
parses that JSON and ships it to Logstash. The schema is:

```json
{
  "@timestamp": "2024-05-01T12:34:56.789Z",
  "container_name": "hp-http",
  "container_service": "http",
  "device_model": "ACME Shop",
  "honeypot_host_ip": "192.168.1.10",
  "src_ip": "192.168.1.30",
  "src_port": 54321,
  "dst_port": 8080,
  "protocol": "HTTP",
  "method": "GET",
  "path": "/login",
  "query": "u=admin'--&p=x",
  "user_agent": "curl/7.81",
  "username": "admin'--",
  "password": "x",
  "payload": "u=admin'--&p=x",
  "attack_type_hint": "sql_injection",
  "response_code": 200,
  "auth_success": false
}
```

### 5.2 Log fields dictionary

| Field               | Type    | Meaning                                              |
|---------------------|---------|------------------------------------------------------|
| `@timestamp`        | string  | UTC ISO-8601 with milliseconds                       |
| `container_name`    | string  | Docker container name (e.g. `hp-http`)              |
| `container_service` | string  | Logical service label (e.g. `http`, `ssh`)          |
| `device_model`      | string  | Fake device model banner                             |
| `honeypot_host_ip`  | string  | IP of Computer 1                                     |
| `src_ip`            | string  | Attacker / client IP                                 |
| `src_port`          | int     | Client ephemeral port                                |
| `dst_port`          | int     | Honeypot port the request hit                        |
| `protocol`          | string  | `HTTP`, `SSH`, `FTP`, `Telnet`, `PJL`                |
| `method`            | string  | HTTP method or protocol command                      |
| `path`              | string  | URL path                                             |
| `query`             | string  | URL query string                                     |
| `username`          | string  | Submitted username (auth endpoints)                  |
| `password`          | string  | Submitted password (auth endpoints)                  |
| `payload`           | string  | The "interesting" input (cmd, SQL, file path, …)     |
| `user_agent`        | string  | HTTP User-Agent                                      |
| `attack_type_hint`  | string  | Heuristic label for ML (see 5.3)                     |
| `response_code`     | int     | HTTP status / protocol return code                   |
| `auth_success`      | bool    | Whether auth succeeded                               |

### 5.3 `attack_type_hint` values

| Value                | When emitted                                   |
|----------------------|------------------------------------------------|
| `benign`             | No suspicious pattern detected                 |
| `sql_injection`      | `'`, `OR 1=1`, `UNION SELECT`, `--`, `sleep(`…|
| `command_injection`  | `;`, `|`, `$(`, backtick, `/bin/sh`, `&&`      |
| `xss`                | `<script`, `onerror=`, `javascript:`           |
| `path_traversal`     | `../`, `..\\`, `/etc/passwd`, `%2e%2e`         |
| `brute_force_login`  | Login attempt with bad creds                   |
| `directory_enum`     | `.git/`, `.env`, `wp-admin`, `phpmyadmin`      |
| `login_success`      | Auth succeeded                                 |
| `ssh_brute_force`    | SSH auth failed                                |
| `ftp_brute_force`    | FTP auth failed                                |
| `telnet_brute_force` | Telnet auth failed                             |
| `ssh_command_exec`   | Post-auth shell command                        |
| `printer_abuse`      | Raw PJL payload                                |
| `recon`              | Info-leak endpoint hit                         |
| `file_upload`        | File upload received                           |

This `attack_type_hint` is the **label** used by the ML pipeline on Computer 2.
It is a heuristic, not a ground truth — during dataset creation we refine it
(see `docs/09_Dataset.md`).

---

## 6. Log flow from Computer 1 to Computer 2

```
┌─────────────────────────── Computer 1 ───────────────────────────┐
│  Container stdout (JSON line per interaction)                    │
│        │                                                          │
│        ▼                                                          │
│  Docker json-file driver (/var/lib/docker/containers/<id>/       │
│        <id>-json.log)                                            │
│        │                                                          │
│        ▼                                                          │
│  Filebeat container                                              │
│   ├─ autodiscover: attaches to any container with label          │
│   │  honeypot=true                                               │
│   ├─ decode_json_fields: parses "message" JSON into honeypot.*   │
│   └─ output.logstash: TCP 192.168.1.20:5044                      │
└──────────────────────────┬─────────────────────────────────────────┘
                           │ TCP 5044 (Beats/Lumberjack v2)
                           ▼
┌─────────────────────────── Computer 2 ───────────────────────────┐
│  Logstash                                                        │
│   ├─ beats input on :5044                                        │
│   ├─ json filter (already JSON, just normalize)                  │
│   ├─ geoip filter (enrich src_ip → country, city)                │
│   └─ elasticsearch output → index honeypot-logs-YYYY.MM.dd       │
└──────────────────────────────────────────────────────────────────┘
```

### 6.1 Filebeat config walk-through (`configs/filebeat.yml`)

| Section                | Purpose                                               |
|------------------------|-------------------------------------------------------|
| `filebeat.autodiscover`| Listens to Docker events, picks up honeypot containers by label |
| `templates[0].config`  | Reads each container's `*-json.log`, decodes JSON     |
| `processors`           | Adds `lab_id`, `shipper`, host metadata               |
| `output.logstash`      | Persistent TCP to `192.168.1.20:5044` (worker=2, loadbalanced) |
| `queue.mem`            | 4096-event in-memory buffer for resilience            |
| `logging`              | Filebeat's own logs to `/var/log/filebeat/`           |

The `LOGSTASH_HOST` / `LOGSTASH_PORT` environment variables are read from
`.env` (defaults `192.168.1.20` / `5044`).

---

## 7. Installation (step by step)

```bash
# 1. Install Docker + Compose v2 (see docs/04_Docker.md for full commands)
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# log out, log back in

# 2. Clone / copy the project
git clone <repo> AI-Honeypot-IDS
cd AI-Honeypot-IDS/Computer-1-Honeypot

# 3. Configure environment
cp .env.example .env
nano .env   # verify LOGSTASH_HOST=192.168.1.20

# 4. Build and start
make build
make up

# 5. Verify
make status
make health
```

`make up` runs `scripts/start.sh`, which:
1. Verifies Docker is installed and running.
2. Loads `.env`.
3. Builds images that are missing.
4. `docker compose up -d`.
5. Polls container health for up to 60 s.
6. Prints a status table.

---

## 8. Health checks

Every container defines a `HEALTHCHECK`:
- HTTP containers: `curl -fsS http://localhost:<port>/` (or `/status`, `/state`).
- TCP containers (SSH/FTP/Telnet): Python one-liner opens a socket.

`make health` runs `scripts/healthcheck.sh`, which probes every service from
the host. This is useful right before the demo to confirm all 11 surfaces are
reachable.

---

## 9. Benign traffic seeding

Real ML datasets need a **normal** class. `scripts/seed-traffic.sh` issues
legitimate-looking requests to every HTTP service from the honeypot host
itself (source IP `172.20.0.1`, the Docker bridge gateway). Run it for a few
minutes before capturing the dataset:

```bash
make seed    # 30 rounds × ~9 requests = ~270 benign events
```

These events are labeled `attack_type_hint=benign` and become the negative
class in the ML dataset.

---

## 10. Demo procedure (Computer 1 presenter)

> Speak slowly. Every step below is also a screenshot opportunity.

1. **"This is Computer 1, the honeypot server, at 192.168.1.10."**
   - `[Take Screenshot Here]` `ip a` shows the static IP.

2. **"We run 11 Docker containers that emulate IoT devices and servers."**
   - `make status` — show the table.
   - `[Take Screenshot Here]` Container status table.

3. **"Each container is intentionally vulnerable."**
   - Open one container's `app.py` on screen and walk through the
     vulnerability (e.g. the `subprocess.run(..., shell=True)` in `camera`).

4. **"Every interaction is logged as JSON and shipped live to Computer 2."**
   - `docker logs hp-http | tail -5` — show JSON log lines.
   - `[Take Screenshot Here]` Sample JSON log line.

5. **"Filebeat handles the shipping."**
   - `docker logs hp-filebeat | tail -10` — show "connected to logstash"
     messages.

6. **"We seed benign traffic so the ML model has a normal class."**
   - `make seed` (run a couple of rounds live).

7. **"All healthy — handing over to Computer 2."**
   - `make health` final check.

---

## 11. Troubleshooting (Computer 1 specific)

| Symptom                                  | Fix                                                         |
|------------------------------------------|-------------------------------------------------------------|
| `make build` fails on a Dockerfile       | `docker compose build <service>` to see the full log        |
| Container `unhealthy`                    | `docker logs <name>`; check the app's stdout                |
| `make status` shows filebeat restarting  | Logstash unreachable — verify `LOGSTASH_HOST`, Comp 2 ufw   |
| Port already in use on host              | `sudo ss -lntp | grep :8081`; stop the conflicting service  |
| `seed-traffic.sh` returns 000 codes      | Host firewall blocking — `sudo ufw status`                  |

Full troubleshooting guide: `docs/13_Troubleshooting.md`.

---

## 12. Viva questions (Computer 1 presenter)

**Q1.** Why use Docker for the honeypot instead of VMs?
**A1.** Docker gives us process-level isolation with millisecond spin-up,
per-container stdout logging that Filebeat can autodiscover, and a tiny
resource footprint so we can run 11 services on a single 8 GB machine. VMs
would give stronger isolation but are far heavier and harder to log centrally
without an agent per VM.

**Q2.** How does Filebeat know which containers to ship logs from?
**A2.** Each honeypot container has the Docker label `honeypot=true` set in
`docker-compose.yml`. Filebeat's `autodiscover` provider subscribes to the
Docker event stream, and the template condition matches on that label. The
container's `*-json.log` file is then tailed and parsed.

**Q3.** Why is `shell=True` dangerous in `subprocess.run`?
**A3.** It invokes `/bin/sh -c <string>`, so user-controlled input is
interpreted as shell syntax. An attacker can chain commands with `;`, `|`,
`&&`, or use command substitution `$(...)`. The camera's `/streams?id=`
endpoint demonstrates this exactly.

**Q4.** How would you fix the command-injection vulnerabilities?
**A4.** Pass a list of arguments (`subprocess.run(["echo", sid],
shell=False)`), validate input against a strict whitelist regex, and never
reflect user input into a shell string. The same applies to SQL: use
parameterized queries, not string formatting.

**Q5.** What stops an attacker from escaping the container?
**A5.** Containers run as non-root (`appuser`), the kernel namespace isolates
PID/net/mount/IPC/UTS, seccomp restricts syscalls, capabilities are dropped
to Docker defaults, and the lab network is air-gapped. For a stronger
guarantee we would add a read-only rootfs, AppArmor/SELinux profile, and
Falco for runtime detection. None of these are needed for the lab demo.

**Q6.** Why does the SSH honeypot accept any password?
**A6.** To capture as many brute-force attempts as possible. Real attackers
try huge wordlists; accepting any password for weak usernames lets us observe
post-auth behavior (commands, file transfers) which is the most valuable data
for ML training.

**Q7.** How are the logs labeled for ML?
**A7.** Each container's `classify()` heuristic emits an `attack_type_hint`.
This is a *weak* label. In `Computer-2-Analysis/ml/src/02_features.py` we
refine these labels using payload signatures and a manual review pass to
produce the final `label` column in the dataset.

**Q8.** Why not just use a real honeypot like Cowrie?
**A8.** Cowrie is excellent and we reference it in `docs/18_References.md`.
We built our own to keep the codebase self-contained, to control the exact
log schema, and because building the honeypot is itself a learning objective
of the project. The architecture would let us swap in Cowrie for the SSH/FTP
containers without changing anything else.

---

## 13. Ethical & safety statement

This honeypot is operated exclusively inside an air-gapped `192.168.1.0/24`
laboratory. The router's WAN port is physically unplugged during the demo.
No logs leave the lab except via the operator's manually inspected export to
the report. The containers contain no real user data and no real services;
compromising them provides no leverage against any production system.

**Before each demo the operator confirms:**
1. Router WAN cable is unplugged.
2. All three machines are on `192.168.1.0/24` only.
3. No ports 8080-8087, 9100, 2222, 2121, 2323 are reachable outside the lab.

---

**End of Computer 1 README.**
