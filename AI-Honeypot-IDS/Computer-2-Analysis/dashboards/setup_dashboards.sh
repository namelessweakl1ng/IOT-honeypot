#!/usr/bin/env bash
# =============================================================================
# Computer 2 — setup_dashboards.sh
# Creates the honeypot index pattern + visualizations + dashboard in Kibana
# via the Saved Objects API. Run after ELK is healthy.
# =============================================================================
set -euo pipefail

KIBANA="${KIBANA_URL:-http://127.0.0.1:5601}"
INDEX_PATTERN_ID="honeypot-logs"
TIMESTAMP_FIELD="@timestamp"

echo "[+] Creating index pattern ${INDEX_PATTERN_ID}..."
curl -fsS -X POST "${KIBANA}/api/index_patterns/index_pattern" \
  -H "kbn-xsrf: true" -H "Content-Type: application/json" \
  -d "{
    \"index_pattern\": {
      \"title\": \"honeypot-logs-*\",
      \"timeFieldName\": \"${TIMESTAMP_FIELD}\",
      \"id\": \"${INDEX_PATTERN_ID}\"
    }
  }" | head -c 200 ; echo

echo "[+] Setting default index pattern..."
curl -fsS -X POST "${KIBANA}/api/data_views/default" \
  -H "kbn-xsrf: true" -H "Content-Type: application/json" \
  -d "{\"data_view_id\": \"${INDEX_PATTERN_ID}\"}" ; echo

echo "[+] Creating visualizations + dashboard via bulk import..."
curl -fsS -X POST "${KIBANA}/api/saved_objects/_bulk_create?overwrite=true" \
  -H "kbn-xsrf: true" -H "Content-Type: application/x-ndjson" \
  --data-binary @dashboards/honeypot-dashboards.ndjson \
  | head -c 300 ; echo

echo "[+] Done. Open ${KIBANA}/app/dashboards to view."
