#!/usr/bin/env bash
# =============================================================================
# Cross-cutting — full_demo.sh
# Orchestrates the full demo end-to-end across the three machines via SSH.
# Assumes passwordless SSH is configured to labuser@<each-machine>.
#
# This is a convenience wrapper. The committee demo is normally run
# interactively per the script in docs/12_Demonstration.md. This script
# exists so the operator can sanity-check the full pipeline before the demo.
# =============================================================================
set -euo pipefail
C1="${HONEYPOT_HOST:-192.168.1.10}"
C2="${ANALYSIS_HOST:-192.168.1.20}"
C3="${ATTACKER_HOST:-192.168.1.30}"
SSH_USER="${SSH_USER:-labuser}"
PROJ="/home/$SSH_USER/AI-Honeypot-IDS"

echo "============================================================"
echo " Full demo orchestration"
echo "   C1 honeypot : $C1"
echo "   C2 analysis : $C2"
echo "   C3 attacker : $C3"
echo "============================================================"

echo ""
echo "[1/6] Verifying lab health..."
bash "$(dirname "$0")/lab_health.sh"

echo ""
echo "[2/6] Starting honeypot on Computer 1..."
ssh "$SSH_USER@$C1" "cd $PROJ/Computer-1-Honeypot && make up && make health"

echo ""
echo "[3/6] Starting ELK on Computer 2..."
ssh "$SSH_USER@$C2" "cd $PROJ/Computer-2-Analysis && make elk-up && make dashboards"

echo ""
echo "[4/6] Seeding benign traffic from Computer 1..."
ssh "$SSH_USER@$C1" "cd $PROJ/Computer-1-Honeypot && make seed"

echo ""
echo "[5/6] Running attack suite from Computer 3..."
ssh "$SSH_USER@$C3" "cd $PROJ/Computer-3-Attacker && ./scripts/run_all_attacks.sh"

echo ""
echo "[6/6] Running ML pipeline on Computer 2..."
ssh "$SSH_USER@$C2" "cd $PROJ/Computer-2-Analysis && source ~/.venvs/honeypot-ml/bin/activate && make all-models"

echo ""
echo "============================================================"
echo " Demo complete."
echo "   Kibana:  http://$C2:5601"
echo "   Models:  $PROJ/trained_models/"
echo "   Reports: $PROJ/Computer-2-Analysis/ml/reports/"
echo "============================================================"
