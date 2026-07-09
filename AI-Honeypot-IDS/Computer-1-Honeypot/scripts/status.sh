#!/usr/bin/env bash
# Computer 1 — status.sh : show container health + filebeat shipping stats
set -euo pipefail
cd "$(dirname "$0")/.."

echo "================ HONEYPOT CONTAINER STATUS ================"
docker compose ps --format "table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "================ FILEBEAT SHIPPER STATUS ================"
FB=$(docker ps --filter "name=hp-filebeat" --format '{{.Names}}')
if [ -z "$FB" ]; then
  echo "[!] filebeat container not running"
else
  echo "[+] filebeat container: $FB"
  echo "[+] Recent filebeat log lines:"
  docker logs --tail 15 hp-filebeat 2>&1 | sed 's/^/    /'
fi
echo ""

echo "================ LOG VOLUMES ================"
docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Active}}\t{{.Size}}\t{{.Reclaimable}}"
