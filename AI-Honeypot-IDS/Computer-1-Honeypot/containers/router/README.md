# Router Login Panel honeypot
Port 8085 → 5000. Fake ISP router admin panel. Default creds `admin/password`.
Vulnerable endpoints: `/api/wps?pin=` (cmd injection), `/api/diag?host=` (cmd
injection via ping), `/api/config` (recon leak). Brute-force-friendly (no rate
limit).
