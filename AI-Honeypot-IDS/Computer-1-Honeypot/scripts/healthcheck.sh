#!/usr/bin/env bash
# Computer 1 — healthcheck.sh : curl every honeypot HTTP service + tcp-probe
# the SSH/FTP/Telnet ports. Exits non-zero if any service is unreachable.
set -uo pipefail
cd "$(dirname "$0")/.."

HOST="${HONEYPOT_HOST_IP:-127.0.0.1}"
FAIL=0

check_http() {
  local name="$1" port="$2" path="${3:-/}"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 "http://${HOST}:${port}${path}" 2>/dev/null || echo "000")
  if [ "$code" = "000" ]; then
    printf "  [FAIL] %-10s :%s%s  unreachable\n" "$name" "$port" "$path"
    FAIL=$((FAIL+1))
  else
    printf "  [ OK ] %-10s :%s%s  HTTP %s\n" "$name" "$port" "$path" "$code"
  fi
}

check_tcp() {
  local name="$1" port="$2"
  if timeout 2 bash -c "echo > /dev/tcp/${HOST}/${port}" 2>/dev/null; then
    printf "  [ OK ] %-10s :%s  TCP open\n" "$name" "$port"
  else
    printf "  [FAIL] %-10s :%s  TCP closed\n" "$name" "$port"
    FAIL=$((FAIL+1))
  fi
}

echo "================ HEALTH CHECKS (host=${HOST}) ================"
check_http  camera     8081  /
check_http  microwave  8082  /status
check_http  smarttv    8083  /
check_http  smartlight 8084  /state
check_http  router     8085  /
check_http  nas        8086  /
check_http  printer    8087  /
check_http  http       8080  /
check_tcp   printer    9100
check_tcp   ssh        2222
check_tcp   ftp        2121
check_tcp   telnet     2323
echo "============================================================="

if [ "$FAIL" -gt 0 ]; then
  echo "[!] ${FAIL} service(s) unreachable. Run 'docker compose ps' to investigate."
  exit 1
fi
echo "[+] All honeypot services reachable."
