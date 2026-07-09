# 13 — Troubleshooting

Comprehensive issue-by-issue guide. Organized by component.

## 13.1 Computer 1 (Honeypot)

### 13.1.1 `make build` fails on a Dockerfile
**Cause:** pip can't reach PyPI (air-gap), or a base image pull failed.
**Fix:**
- Build with internet available first time; the images cache locally.
- Or pre-pull on a connected machine and `docker save | ssh ... docker load`.

### 13.1.2 Container shows `unhealthy`
**Cause:** app crashed or port already in use.
**Fix:**
```bash
docker logs <container-name>
ss -lntp | grep :<port>
```
Look for `Address already in use` (host port conflict) or Python tracebacks.

### 13.1.3 `make status` shows filebeat restarting
**Cause:** Logstash unreachable.
**Fix:**
- Verify `LOGSTASH_HOST` in `.env` (should be `192.168.1.20`).
- Verify Computer 2 ufw allows 5044 from Computer 1.
- `docker logs hp-filebeat | tail -20` — look for "no route to host" or
  "connection refused".

### 13.1.4 Port already in use on host
**Cause:** another service (e.g. nginx, apache) is bound to the same port.
**Fix:**
```bash
sudo ss -lntp | grep :8080
sudo systemctl stop apache2  # or whichever
```

### 13.1.5 `seed-traffic.sh` returns 000 codes
**Cause:** host firewall blocking localhost.
**Fix:** `sudo ufw status`; allow from 192.168.1.0/24.

## 13.2 Computer 2 (ELK + ML)

### 13.2.1 `make elk-up` exits but Elasticsearch is red
**Cause:** usually memory_lock or low vm.max_map_count.
**Fix:**
```bash
sudo sysctl -w vm.max_map_count=262144
echo 'vm.max_map_count=262144' | sudo tee -a /etc/sysctl.conf
docker compose -f elk/docker-compose-elk.yml down
docker compose -f elk/docker-compose-elk.yml up -d
```

### 13.2.2 Kibana shows "no indices"
**Cause:** index pattern not created.
**Fix:** `make dashboards` (runs `setup_dashboards.sh`).

### 13.2.3 `01_ingest.py` returns 0 events
**Cause:** no logs have arrived yet (attacks not run, or Filebeat not
shipping).
**Fix:**
```bash
# On Computer 2:
curl -s http://127.0.0.1:9200/_cat/indices/honeypot-logs-*?v
# On Computer 1:
docker logs hp-filebeat | tail -20
```

### 13.2.4 Logstash drops events
**Cause:** schema mismatch or Ruby filter error.
**Fix:**
```bash
docker logs elk-logstash 2>&1 | grep -i error | tail -20
```
Check `20-honeypot-filter.conf` for typos.

### 13.2.5 `03_train.py` OOM
**Cause:** dataset too large for in-memory SVM.
**Fix:**
- Subsample: `python src/01_ingest.py --days 1`.
- Reduce `n_estimators` in `config.py`.
- Skip SVM: comment out the `svm` entry in `config.MODELS`.
- Increase RAM (SVM is O(n²) in training-set size).

### 13.2.6 XGBoost import fails
**Cause:** missing build tools or incompatible wheel.
**Fix:**
```bash
sudo apt install -y build-essential python3.11-dev
pip install --no-cache-dir --no-binary :all: xgboost==2.0.3
```

### 13.2.7 `make evaluate` skips ROC
**Cause:** best model doesn't support `predict_proba`.
**Fix:** all our models set `probability=True` (SVM) or natively support
`predict_proba`. If you add a new model without it, the ROC step skips
gracefully (warning only).

### 13.2.8 Elasticsearch disk watermark hit (>85%)
**Cause:** too many indices.
**Fix:**
```bash
curl -X DELETE "http://127.0.0.1:9200/honeypot-logs-2024.04.*"
# or schedule configs/elk-retention.sh via cron
```

## 13.3 Computer 3 (Attacker)

### 13.3.1 hydra says "all children were disabled due to too many connection errors"
**Cause:** target throttling or wrong port.
**Fix:** for telnet use `-t 4` (already set in script 02). Verify
`HONEYPOT_HOST` and ports in `.env`.

### 13.3.2 `nmap` says "host seems down"
**Cause:** host firewall drops ICMP.
**Fix:** always use `-Pn` (we do).

### 13.3.3 `sqlmap` says "all tested parameters do not appear to be injectable"
**Cause:** the SQLite-backed `/product?id=` endpoint might have been
recently restarted and the seeded data is gone.
**Fix:** the http container reseeds its SQLite DB on every start, so this
shouldn't happen. If it does: `docker compose restart http` then re-run.

### 13.3.4 `gobuster` returns nothing
**Cause:** wordlist paths don't match the container's actual endpoints.
**Fix:** our `wordlists/dirs.txt` is pre-populated with the exact vulnerable
endpoints. Verify the file is present.

### 13.3.5 `nikto` returns "no web server found"
**Cause:** wrong port or service down.
**Fix:** `curl -I http://192.168.1.10:8080/` should return 200. If not,
check Computer 1.

## 13.4 Network

### 13.4.1 Can't ping between machines
**Cause:** ufw blocking ICMP or wrong subnet.
**Fix:** `sudo ufw status` on each; verify 192.168.1.0/24 is allowed.

### 13.4.2 Internet works on lab machines
**Cause:** router WAN is plugged in (air-gap broken).
**Fix:** **UNPLUG WAN IMMEDIATELY** before continuing. Re-verify with
`ping -c 1 8.8.8.8` (should fail).

## 13.5 General

### 13.5.1 "Permission denied" on scripts
**Fix:** `chmod +x scripts/*.sh`.

### 13.5.2 Disk full
**Fix:** `docker system prune -a` on Computer 1 and 2.

### 13.5.3 Lost SSH session to a lab machine
**Fix:** `ssh labuser@192.168.1.10` (or .20 / .30). If repeated, check the
machine's physical console.

## 13.6 Getting help

- Elastic docs: <https://www.elastic.co/guide/en/elasticsearch/reference/8.13/>
- Docker docs: <https://docs.docker.com/>
- scikit-learn docs: <https://scikit-learn.org/stable/>
- Project references: `docs/18_References.md`
