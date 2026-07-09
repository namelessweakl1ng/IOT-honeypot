#!/usr/bin/env bash
# Computer 2 — elk-retention.sh
# Deletes honeypot-logs-* indices older than N days (default 30).
# Run from cron: 0 3 * * * /path/to/Computer-2-Analysis/configs/elk-retention.sh 30
set -euo pipefail
DAYS="${1:-30}"
ES="${ES_HOST:-http://127.0.0.1:9200}"
echo "[retention] deleting honeypot-logs-* indices older than ${DAYS} days"
curl -fsS -X DELETE "${ES}/honeypot-logs-*?expand_wildcards=open&ignore_unavailable=true" \
  -H "Content-Type: application/json" \
  -d "{\"query\":{\"range\":{\"@timestamp\":{\"lt\":\"now-${DAYS}d/d\"}}}}" \
  | head -c 200; echo
echo "[retention] done."
