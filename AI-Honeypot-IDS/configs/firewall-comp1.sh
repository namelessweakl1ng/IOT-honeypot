#!/usr/bin/env bash
# UFW rules for Computer 1 (honeypot)
# Run with: sudo bash firewall-comp1.sh
set -e
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow from 192.168.1.0/24 to any port 22 proto tcp           # SSH admin
ufw allow from 192.168.1.0/24 to any port 8080:8087 proto tcp    # honeypot web
ufw allow from 192.168.1.0/24 to any port 9100 proto tcp         # printer raw
ufw allow from 192.168.1.0/24 to any port 2222 proto tcp         # ssh honeypot
ufw allow from 192.168.1.0/24 to any port 2121 proto tcp         # ftp honeypot
ufw allow from 192.168.1.0/24 to any port 2323 proto tcp         # telnet honeypot
ufw --force enable
ufw status verbose
