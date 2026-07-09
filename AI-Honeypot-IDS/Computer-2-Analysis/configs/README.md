# Computer 2 — configs

ELK and ML configuration files live under `elk/` and `ml/` respectively. This
folder is reserved for cross-cutting configs (e.g. backup scripts, retention
policies).

## Files
- `elk-retention.sh` — ILM-like cleanup script: deletes honeypot-logs-* indices
  older than N days. Run via cron if you keep the lab up long-term.
