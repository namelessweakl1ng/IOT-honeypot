#!/usr/bin/env bash
# =============================================================================
# Cross-cutting — lab_health.sh
# Verifies that all three lab machines are reachable, the honeypot ports are
# open from the attacker side, and Kibana is responding. Run from any
# machine that can reach 192.168.1.0/24.
# =============================================================================
set -uo pipefail
C1="${HONEYPOT_HOST:-192.168.1.10}"
C2="${ANALYSIS_HOST:-192.168.1.20}"
C3="${ATTACKER_HOST:-192.168.1.30}"

echo "================ LAB HEALTH ================"

echo "[1] Ping all three machines:"
for ip in "$C1" "$C2" "$C3"; do
  if ping -c 1 -W 2 "$ip" >/dev/null 2>&1; then
    echo "   [ OK ] $ip"
  else
    echo "   [FAIL] $ip"
  fi
done

echo ""
echo "[2] Honeypot ports reachable from this host:"
for p in 8080 8081 8082 8083 8084 8085 8086 8087 9100 2222 2121 2323; do
  if timeout 2 bash -c "echo > /dev/tcp/$C1/$p" 2>/dev/null; then
    echo "   [ OK ] $C1:$p"
  else
    echo "   [FAIL] $C1:$p"
  fi
done

echo ""
echo "[3] ELK ports on Computer 2:"
for p in 5044 9200 5601; do
  if timeout 2 bash -c "echo > /dev/tcp/$C2/$p" 2>/dev/null; then
    echo "   [ OK ] $C2:$p"
  else
    echo "   [FAIL] $C2:$p"
  fi
done

echo ""
echo "[4] Kibana HTTP health:"
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://$C2:5601/api/status" 2>/dev/null || echo "000")
echo "   HTTP $code"

echo ""
echo "[5] Elasticsearch event count:"
curl -s --max-time 3 "http://$C2:9200/honeypot-logs-*/_count" 2>/dev/null || echo "(unreachable)"

echo ""
echo "[6] Air-gap check (should FAIL):"
if curl -sI --max-time 3 https://example.com/ >/dev/null 2>&1; then
  echo "   [!!] Internet reachable — UNPLUG ROUTER WAN"
else
  echo "   [ OK ] No Internet (air-gap intact)"
fi

echo "============================================"
