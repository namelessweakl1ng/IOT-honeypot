#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 04_dirscan.sh
# Directory enumeration with gobuster + dirb against the HTTP and camera web
# roots. Uses scripts/wordlists/dirs.txt.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
WL="scripts/wordlists/dirs.txt"
OUT="results/04_dirscan"
mkdir -p results

echo "[+] gobuster on http://${HOST}:${HTTP_PORT:-8080}/ ..."
if command -v gobuster >/dev/null 2>&1; then
  gobuster mode=dir -u "http://${HOST}:${HTTP_PORT:-8080}" -w "$WL" \
    -t 20 -q -o "${OUT}_http.txt" 2>&1 | tee "${OUT}_http.log" || true
else
  echo "    (gobuster not installed — using curl loop)"
  while IFS= read -r line; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://${HOST}:${HTTP_PORT:-8080}/${line}")
    [ "$code" != "404" ] && echo "$code  /${line}" | tee -a "${OUT}_http.txt"
  done < "$WL"
fi

echo ""
echo "[+] gobuster on http://${HOST}:${CAMERA_PORT:-8081}/ ..."
if command -v gobuster >/dev/null 2>&1; then
  gobuster mode=dir -u "http://${HOST}:${CAMERA_PORT:-8081}" -w "$WL" \
    -t 20 -q -o "${OUT}_camera.txt" 2>&1 | tee "${OUT}_camera.log" || true
else
  while IFS= read -r line; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://${HOST}:${CAMERA_PORT:-8081}/${line}")
    [ "$code" != "404" ] && echo "$code  /${line}" | tee -a "${OUT}_camera.txt"
  done < "$WL"
fi

echo ""
echo "[+] dirb on http://${HOST}:${ROUTER_PORT:-8085}/ (if installed)..."
if command -v dirb >/dev/null 2>&1; then
  dirb "http://${HOST}:${ROUTER_PORT:-8085}" "$WL" -o "${OUT}_router.txt" 2>&1 | tee "${OUT}_router.log" || true
fi

echo "[+] Done."
