#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 08_dos_sim.sh
# Simple DoS simulation: a few hundred rapid requests against the HTTP
# container to generate a burst of events. This is NOT a real DoS — the goal
# is just to populate the timeline + heatmap visualizations with a visible
# spike. Run for ~10 seconds only.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
OUT="results/08_dos_sim"
mkdir -p results

N="${1:-300}"
echo "[+] Sending ${N} rapid requests to http://${HOST}:${HTTP_PORT:-8080}/ ..."
echo "(this is a controlled simulation, not a real DoS — limited to ${N} requests)"

ok=0; fail=0
for i in $(seq 1 "$N"); do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "http://${HOST}:${HTTP_PORT:-8080}/?n=${i}" 2>/dev/null || echo "000")
  if [ "$code" = "000" ] || [ "$code" = "503" ]; then
    fail=$((fail+1))
  else
    ok=$((ok+1))
  fi
done

echo "  ok=${ok}  fail=${fail}" | tee "${OUT}.txt"
echo "[+] Done. Burst visible in Kibana timeline."
