#!/usr/bin/env bash
# Computer 1 — seed-traffic.sh
# Generates BENIGN baseline traffic so the ML dataset has a "normal" class.
# This is critical: without normal samples the classifier cannot distinguish
# attacks from benign activity.
#
# We use curl to hit each honeypot HTTP service with legitimate-looking
# requests (status checks, login page loads, light toggles) from the honeypot
# host itself. Source IP will appear as 172.20.0.1 (docker bridge gateway).
set -uo pipefail
cd "$(dirname "$0")/.."
HOST="${HONEYPOT_HOST_IP:-127.0.0.1}"
LOOPS="${1:-30}"
SLEEP="${2:-2}"

echo "[+] Generating ${LOOPS} rounds of benign traffic against ${HOST}..."
for i in $(seq 1 "$LOOPS"); do
  curl -s -o /dev/null "http://${HOST}:8081/"                     # camera page
  curl -s -o /dev/null "http://${HOST}:8082/status"               # microwave status
  curl -s -o /dev/null "http://${HOST}:8083/"                     # smarttv home
  curl -s -o /dev/null "http://${HOST}:8084/state"                # smartlight state
  curl -s -o /dev/null "http://${HOST}:8085/"                     # router login
  curl -s -o /dev/null "http://${HOST}:8086/"                     # nas home
  curl -s -o /dev/null "http://${HOST}:8087/"                     # printer web
  curl -s -o /dev/null "http://${HOST}:8080/"                     # http home
  curl -s -o /dev/null "http://${HOST}:8080/login?u=guest&p=guest" # benign login attempt
  echo "  round ${i}/${LOOPS} done"
  sleep "$SLEEP"
done
echo "[+] Benign seed traffic complete."
