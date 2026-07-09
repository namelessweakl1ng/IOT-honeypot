#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 05_nikto.sh
# Runs nikto against the HTTP vulnerable web app for vulnerability scanning.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
OUT="results/05_nikto"
mkdir -p results

echo "[+] nikto against http://${HOST}:${HTTP_PORT:-8080}/ ..."
if command -v nikto >/dev/null 2>&1; then
  nikto -h "http://${HOST}:${HTTP_PORT:-8080}" -Tuning 1,2,8,9 -o "${OUT}_http.txt" 2>&1 | tee "${OUT}_http.log" || true
else
  echo "    (nikto not installed — run: sudo apt install nikto)"
fi

echo ""
echo "[+] nikto against http://${HOST}:${CAMERA_PORT:-8081}/ ..."
if command -v nikto >/dev/null 2>&1; then
  nikto -h "http://${HOST}:${CAMERA_PORT:-8081}" -o "${OUT}_camera.txt" 2>&1 | tee "${OUT}_camera.log" || true
fi

echo "[+] Done."
