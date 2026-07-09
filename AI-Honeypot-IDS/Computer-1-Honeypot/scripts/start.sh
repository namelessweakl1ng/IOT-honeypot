#!/usr/bin/env bash
# =============================================================================
# Computer 1 — start.sh
# Validates environment, builds if needed, starts the honeypot, waits for
# health, prints status. Intended to be called via `make up` but can be run
# directly:  ./scripts/start.sh
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=============================================="
echo " AI-Honeypot-IDS — Computer 1 (Honeypot) start"
echo "=============================================="

# --- 1. Verify .env exists ---------------------------------------------------
if [ ! -f .env ]; then
  echo "[!] .env not found — copying from .env.example"
  cp .env.example .env
fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a

# --- 2. Sanity checks --------------------------------------------------------
command -v docker >/dev/null 2>&1 || { echo "[FATAL] docker not installed"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[FATAL] docker compose v2 not installed"; exit 1; }
docker info >/dev/null 2>&1 || { echo "[FATAL] docker daemon not running or no perms"; exit 1; }

echo "[+] LOGSTASH_HOST=${LOGSTASH_HOST:-192.168.1.20}:${LOGSTASH_PORT:-5044}"
echo "[+] HONEYPOT_HOST_IP=${HONEYPOT_HOST_IP:-192.168.1.10}"

# --- 3. Build (only if images missing) --------------------------------------
IMAGES_BUILT=$(docker images --filter "reference=computer-1-honeypot-*" -q | wc -l)
if [ "$IMAGES_BUILT" -lt 11 ]; then
  echo "[+] Building container images (first run takes a few minutes)..."
  docker compose build
fi

# --- 4. Bring up the stack ---------------------------------------------------
echo "[+] Starting containers..."
docker compose up -d

# --- 5. Wait for health ------------------------------------------------------
echo "[+] Waiting up to 60s for containers to become healthy..."
HEALTHY=0
for i in $(seq 1 12); do
  HEALTHY=$(docker compose ps --format json 2>/dev/null \
            | python3 -c 'import sys,json;print(sum(1 for l in sys.stdin if json.loads(l).get("Health")=="healthy"))' 2>/dev/null || echo 0)
  echo "    attempt ${i}/12 — healthy=${HEALTHY}/12"
  [ "$HEALTHY" -ge 11 ] && break
  sleep 5
done

# --- 6. Final status ---------------------------------------------------------
echo ""
echo "=============================================="
echo " Honeypot status"
echo "=============================================="
docker compose ps --format "table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "[+] Honeypot is up. Attacker should target: ${HONEYPOT_HOST_IP:-192.168.1.10}"
echo "[+] Filebeat is shipping logs to ${LOGSTASH_HOST:-192.168.1.20}:${LOGSTASH_PORT:-5044}"
echo "[+] Run 'make logs' to tail container logs."
