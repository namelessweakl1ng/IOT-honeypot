#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 01_portscan.sh
# Runs nmap + masscan against the honeypot host. Captures a normal service
# scan plus an aggressive (-A) scan for banner grabbing.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
OUT="results/01_portscan"
mkdir -p results

echo "[+] nmap default TCP scan against ${HOST}..."
nmap -Pn -n -sS -p- --min-rate 2000 -oN "${OUT}_nmap_tcp.txt" "${HOST}" 2>&1 | tee "${OUT}_nmap_tcp.log"

echo ""
echo "[+] nmap service + version + OS detection (-A) on discovered open ports..."
nmap -Pn -n -A --version-intensity 5 -oN "${OUT}_nmap_A.txt" "${HOST}" 2>&1 | tee "${OUT}_nmap_A.log"

echo ""
echo "[+] masscan top 1000 ports (if installed)..."
if command -v masscan >/dev/null 2>&1; then
  sudo masscan "${HOST}" -p1-65535 --rate=2000 -oJ "${OUT}_masscan.json" 2>&1 | tee "${OUT}_masscan.log" || true
else
  echo "    (masscan not installed — skipping)"
fi

echo "[+] Banner grab with netcat on a few key ports..."
for p in 2222 2121 2323 9100 8080; do
  echo "--- port ${p} ---"
  timeout 2 bash -c "exec 3<>/dev/tcp/${HOST}/${p}; head -c 80 <&3" 2>/dev/null || echo "(no banner / closed)"
done

echo "[+] Done. Results in results/${OUT}_*"
