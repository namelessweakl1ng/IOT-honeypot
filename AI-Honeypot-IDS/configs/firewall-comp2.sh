#!/usr/bin/env bash
# UFW rules for Computer 2 (SIEM + ML)
# Run with: sudo bash firewall-comp2.sh
set -e
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow from 192.168.1.0/24 to any port 22 proto tcp           # SSH admin
ufw allow from 192.168.1.0/24 to any port 5601 proto tcp         # Kibana
ufw allow from 192.168.1.10 to any port 5044 proto tcp           # Filebeat ingest
ufw --force enable
ufw status verbose
