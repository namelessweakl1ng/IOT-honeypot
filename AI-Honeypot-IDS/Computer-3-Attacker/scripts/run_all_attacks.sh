#!/usr/bin/env bash
# =============================================================================
# Computer 3 — run_all_attacks.sh
# Convenience runner: executes the full attack suite in order against the
# honeypot host. Each sub-script writes its results to results/.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"

echo "============================================================"
echo " AI-Honeypot-IDS — Computer 3 full attack suite"
echo " Target: ${HOST}"
echo "============================================================"

SCRIPTS=(
  "01_portscan.sh"
  "02_bruteforce.sh"
  "03_webattacks.sh"
  "04_dirscan.sh"
  "05_nikto.sh"
  "06_sqlmap.sh"
  "07_netcat.sh"
  "08_dos_sim.sh 200"
  "09_custom_payloads.sh"
  "10_credential_post.sh"
)

for s in "${SCRIPTS[@]}"; do
  echo ""
  echo "########## RUNNING: scripts/$s ##########"
  bash "scripts/$s" || echo "[!] $s failed (continuing)"
done

echo ""
echo "============================================================"
echo " All attacks complete. Check Kibana on Computer 2:"
echo "   http://${ANALYSIS_HOST:-192.168.1.20}:5601"
echo " Results saved under Computer-3-Attacker/results/"
echo "============================================================"
