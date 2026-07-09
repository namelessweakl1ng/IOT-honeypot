#!/usr/bin/env bash
# =============================================================================
# Cross-cutting — reset_lab.sh
# Stops all containers on Computer 1 and Computer 2, clears honeypot-logs-*
# indices, ready for a clean run. Run from any machine with SSH access.
# =============================================================================
set -euo pipefail
C1="${HONEYPOT_HOST:-192.168.1.10}"
C2="${ANALYSIS_HOST:-192.168.1.20}"
SSH_USER="${SSH_USER:-labuser}"
PROJ="/home/$SSH_USER/AI-Honeypot-IDS"

echo "[1/3] Stopping honeypot on Computer 1..."
ssh "$SSH_USER@$C1" "cd $PROJ/Computer-1-Honeypot && make down" || true

echo "[2/3] Stopping ELK on Computer 2..."
ssh "$SSH_USER@$C2" "cd $PROJ/Computer-2-Analysis && make elk-down" || true

echo "[3/3] Clearing honeypot-logs-* indices on Computer 2..."
ssh "$SSH_USER@$C2" "curl -fsS -X DELETE 'http://127.0.0.1:9200/honeypot-logs-*' || echo '(elasticsearch already down)'"

echo "[+] Lab reset. Run full_demo.sh to start fresh."
