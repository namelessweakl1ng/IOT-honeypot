# Cross-cutting scripts

This folder holds automation scripts that span multiple computers or the
whole project. Per-computer scripts live under
`Computer-1-Honeypot/scripts/`, `Computer-2-Analysis/` (Makefile targets),
and `Computer-3-Attacker/scripts/`.

## Files
- `lab_health.sh` — pings all three machines, checks honeypot ports from
  the attacker side, checks Kibana reachability. Run from the operator's
  laptop before the demo.
- `full_demo.sh` — orchestrates the entire demo end-to-end across the three
  machines via SSH (assumes passwordless SSH configured).
- `reset_lab.sh` — stops all containers on Computer 1 and Computer 2,
  clears honeypot-logs-* indices, ready for a clean run.

## Usage
```bash
./lab_health.sh
./full_demo.sh
./reset_lab.sh
```
