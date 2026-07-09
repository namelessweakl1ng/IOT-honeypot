# 12 — Demonstration Guide

This is the **minute-by-minute demo script** for the final project
presentation. Total runtime: ~45 minutes (30 demo + 15 Q&A).

## 12.1 Pre-demo checklist (T-15 min)

Run through this BEFORE the committee arrives:

- [ ] Router WAN cable physically unplugged.
- [ ] All three machines powered on, logged in, `ip a` shows correct IPs.
- [ ] Computer 1: `make status` shows 11 healthy containers.
- [ ] Computer 2: `make elk-status` shows 3 healthy ELK containers.
- [ ] Computer 2: Kibana loads at `http://192.168.1.20:5601`.
- [ ] Computer 2: Dashboards panel visible.
- [ ] Computer 3: `cat .env` shows `HONEYPOT_HOST=192.168.1.10`.
- [ ] Operator laptop has a browser tab open to Kibana.
- [ ] Projector / screen mirror ready on each machine.

## 12.2 Demo timeline

| T   | Step | Presenter        | Action                                                                 |
|-----|------|------------------|------------------------------------------------------------------------|
| 0:00| 1    | Lead             | Introduce project; show master README; explain 3-computer architecture |
| 2:00| 2    | Computer 1       | Show `ip a`, `make status`, walk through one container's app.py        |
| 5:00| 3    | Computer 1       | `make health` — all green; explain Filebeat shipping                   |
| 7:00| 4    | Computer 2       | `make elk-status`; open Kibana; show empty Discover view               |
| 9:00| 5    | Computer 2       | `make dashboards` (or confirm pre-loaded); show dashboard panels       |
|11:00| 6    | Computer 1       | `make seed` — generate benign traffic; show events appearing in Kibana |
|14:00| 7    | Computer 3       | `ip a`; show `ls scripts/`; explain each attack class briefly          |
|17:00| 8    | Computer 3       | `./scripts/run_all_attacks.sh` — narrate as each phase runs            |
|25:00| 9    | Computer 2       | Switch to Kibana; walk through every dashboard panel live              |
|30:00| 10   | Computer 2       | `make ingest` → `make stats` — show dataset class distribution         |
|32:00| 11   | Computer 2       | `make train` — narrate CV metrics printing; show best model            |
|35:00| 12   | Computer 2       | `make evaluate` — show confusion matrix + ROC PNGs                     |
|37:00| 13   | Computer 2       | `ls trained_models/` — show the four handover artifacts                |
|38:00| 14   | Lead             | Explain future deployment paths (SIEM/firewall/EDR/cloud); reiterate   |
|     |      |                  | that the model is NOT deployed in this project                         |
|40:00| 15   | All              | Q&A                                                                    |

## 12.3 Screenshot markers

Every `[Take Screenshot Here]` in the per-computer READMEs corresponds to a
slide in the final report. Minimum screenshots to capture:

1. Computer 1 `ip a` + container status table.
2. Computer 1 sample JSON log line (`docker logs hp-http | head -1`).
3. Computer 2 ELK status table.
4. Computer 2 Kibana Overview dashboard (full screen).
5. Computer 2 Kibana Discover view filtered to `attack_class: bruteforce`.
6. Computer 2 Kibana timeline showing the DoS burst spike.
7. Computer 3 `ip a` + attack scripts listing.
8. Computer 3 nmap `-A` output.
9. Computer 3 hydra cracked credentials.
10. Computer 3 sqlmap dumping users table.
11. Computer 3 PJL abuse response.
12. Computer 2 dataset class distribution (`make stats`).
13. Computer 2 CV metrics table.
14. Computer 2 confusion matrix PNG (best model).
15. Computer 2 ROC curve PNG (best model).
16. Computer 2 `trained_models/` directory listing.

Save all screenshots to `screenshots/` with descriptive filenames
(`01_comp1_status.png`, etc.).

## 12.4 Demo fallbacks

If something breaks mid-demo:

| Failure                          | Fallback                                           |
|----------------------------------|----------------------------------------------------|
| Container unhealthy              | `docker compose restart <name>`; skip if persistent|
| No logs in Kibana                | Check `docker logs hp-filebeat`; show saved        |
|                                  | screenshot of a previous successful run            |
| ML pipeline OOM                  | Subsample the dataset: `python src/01_ingest.py --days 1` |
| Projector fails                  | Read from the per-computer README aloud             |
| Committee asks to re-run attack  | Run `scripts/09_custom_payloads.sh` (fastest, ~30s)|

## 12.5 Post-demo

- Capture any screenshots missed.
- `cd Computer-2-Analysis && make all-models` to regenerate final reports.
- Copy `reports/` and `datasets/honeypot_dataset.csv` into the project
  handover folder.
- Archive `trained_models/` into a zip for the committee.
