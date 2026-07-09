#!/usr/bin/env bash
# Computer 1 — stop.sh : clean shutdown of honeypot containers + filebeat
set -euo pipefail
cd "$(dirname "$0")/.."
echo "[+] Stopping honeypot..."
docker compose down
echo "[+] Done. Containers removed (images preserved)."
