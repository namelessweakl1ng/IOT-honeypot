# 08 — ELK Stack

## 8.1 Why ELK?

ELK (Elasticsearch + Logstash + Kibana) is the most widely-deployed SIEM
stack in industry. Choosing it for the lab means the skills demonstrated
transfer directly to a real SOC.

| Component       | Role in this project                              |
|-----------------|---------------------------------------------------|
| Elasticsearch   | Storage + search engine for all honeypot events   |
| Logstash        | Ingest from Filebeat, parse, enrich, index        |
| Kibana          | Visualization + dashboards + Discover view        |

## 8.2 Versions

All three components are pinned to `8.13.4` for compatibility.

## 8.3 Compose file

`Computer-2-Analysis/elk/docker-compose-elk.yml` defines four services:

| Service        | Image                                                          | Ports        |
|----------------|----------------------------------------------------------------|--------------|
| elasticsearch  | docker.elastic.co/elasticsearch/elasticsearch:8.13.4           | 9200         |
| logstash       | docker.elastic.co/logstash/logstash:8.13.4                     | 5044, 9600   |
| kibana         | docker.elastic.co/kibana/kibana:8.13.4                         | 5601         |
| setup           | elasticsearch:8.13.4 (one-shot, loads index template)         | —            |

## 8.4 Elasticsearch configuration

`elasticsearch/elasticsearch.yml`:
- `discovery.type: single-node` — no clustering.
- `xpack.security.enabled: false` — air-gapped lab.
- `bootstrap.memory_lock: true` — prevents heap swapping.
- Heap: 1 GB via `ES_JAVA_OPTS=-Xms1g -Xmx1g`.

`elasticsearch/index-template-honeypot.json`:
- Matches `honeypot-logs-*`.
- 1 shard, 0 replicas (single-node).
- Strict mappings for every honeypot field.
- `geo.location` as `geo_point` for the map visualization.

## 8.5 Logstash configuration

Three config files in `logstash/conf.d/`:

### 10-honeypot-input.conf
Beats input on port 5044.

### 20-honeypot-filter.conf
The heart of the enrichment pipeline:
1. Flatten nested JSON from Filebeat.
2. Coerce types.
3. GeoIP enrichment.
4. Derive `attack_class` from `attack_type_hint` (the ML target).
5. Drop noisy fields.

### 90-honeypot-output.conf
Daily-rolling index in Elasticsearch.

## 8.6 Kibana configuration

`kibana/kibana.yml`:
- Bind to 0.0.0.0:5601.
- No TLS (lab).
- Default app: dashboards.
- Telemetry off.

## 8.7 Dashboards

Loaded via `dashboards/setup_dashboards.sh`. The "Honeypot Overview" dashboard
contains 7 panels:

1. **Top Attackers** — bar chart, terms on `src_ip`.
2. **Top Targeted Ports** — donut, terms on `dst_port`.
3. **Most Attacked Container** — bar, terms on `container_name`.
4. **Attack Timeline** — stacked line, date_histogram on `@timestamp`.
5. **Attack Class Breakdown** — donut, terms on `attack_class`.
6. **Protocol Distribution** — donut, terms on `protocol`.
7. **Attacker Geo Map** — coordinate map, geohash_grid on `geo.location`.

## 8.8 Operating ELK

### Start
```bash
cd Computer-2-Analysis
make elk-up
```

### Stop
```bash
make elk-down
```

### Status
```bash
make elk-status
```

### Tail logs
```bash
make elk-logs
```

### Load dashboards
```bash
make dashboards
```

### Open Kibana
```bash
make kibana
# or browse to http://192.168.1.20:5601
```

## 8.9 Index management

Daily indices `honeypot-logs-YYYY.MM.dd` grow indefinitely. In a long-running
lab, schedule `configs/elk-retention.sh` via cron to delete indices older
than 30 days:

```bash
# crontab -e
0 3 * * * /home/labuser/AI-Honeypot-IDS/Computer-2-Analysis/configs/elk-retention.sh 30
```

For a one-off cleanup:
```bash
curl -X DELETE "http://127.0.0.1:9200/honeypot-logs-2024.04.*"
```

## 8.10 Security considerations (lab vs production)

| Setting                  | Lab             | Production                       |
|--------------------------|-----------------|----------------------------------|
| `xpack.security`         | disabled        | enabled                          |
| TLS (transport)          | off             | on (mutual auth)                 |
| TLS (HTTP)               | off             | on                               |
| Authentication           | none            | RBAC + API keys                  |
| Network exposure         | 192.168.1.0/24  | VPN-only / private subnet        |
| Audit logging            | off             | on                               |
| Backups                  | none            | snapshots to S3/NFS daily        |

The lab config is documented as **insecure** in every relevant file. Anyone
reusing this code in production must apply the production column.

## 8.11 Resource sizing

| Component     | Lab RAM | Lab CPU | Production RAM | Production CPU |
|---------------|---------|---------|----------------|----------------|
| Elasticsearch | 1 GB    | 1 core  | 8–32 GB        | 4–8 cores      |
| Logstash      | 512 MB  | 1 core  | 2–4 GB         | 2–4 cores      |
| Kibana        | 1 GB    | 1 core  | 2 GB           | 2 cores        |
