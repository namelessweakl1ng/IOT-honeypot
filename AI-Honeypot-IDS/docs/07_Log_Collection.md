# 07 — Log Collection

## 7.1 Pipeline overview

```
Container stdout (JSON)
   │
   ▼
Docker json-file driver
   │ /var/lib/docker/containers/<id>/<id>-json.log
   ▼
Filebeat (Computer 1)
   │ autodiscover + decode_json_fields + processors
   ▼
TCP 5044 → Logstash (Computer 2)
   │
   ▼
filter: flatten + coerce + geoip + attack_class
   │
   ▼
Elasticsearch index honeypot-logs-YYYY.MM.dd
```

## 7.2 Filebeat configuration walk-through

`Computer-1-Honeypot/configs/filebeat.yml`:

### 7.2.1 autodiscover
```yaml
filebeat.autodiscover:
  providers:
    - type: docker
      hints.enabled: true
      templates:
        - condition:
            contains:
              docker.container.labels.honeypot: "true"
          config:
            - type: container
              paths:
                - "/var/lib/docker/containers/${data.docker.container.id}/*-json.log"
```

Every container with Docker label `honeypot=true` (set in `docker-compose.yml`)
gets its `*-json.log` tailed automatically. No per-container config needed.

### 7.2.2 JSON decoding
```yaml
processors:
  - decode_json_fields:
      fields: ["message"]
      target: "honeypot"
      overwrite_keys: true
```

The container's stdout (already JSON) is parsed into a nested `honeypot`
object. Logstash later flattens this.

### 7.2.3 Enrichment
```yaml
processors:
  - add_fields:
      target: ""
      fields:
        lab_id: "ai-honeypot-ids"
        shipper: "filebeat-computer-1"
  - add_docker_metadata: ~
  - add_host_metadata: ~
```

### 7.2.4 Output
```yaml
output.logstash:
  hosts: ["${LOGSTASH_HOST}:${LOGSTASH_PORT}"]
  worker: 2
  loadbalance: true
  ttl: 30s
```

Persistent TCP connection to Logstash. Two workers for throughput. `ttl: 30s`
forces connection recycling so a dead Logstash is detected within 30 s.

### 7.2.5 In-memory queue
```yaml
queue.mem:
  events: 4096
  flush.min_events: 1024
  flush.timeout: 1s
```

Buffers up to 4096 events if Logstash is briefly unreachable.

## 7.3 Logstash pipeline walk-through

`Computer-2-Analysis/elk/logstash/conf.d/`:

### 10-honeypot-input.conf
```logstash
input {
  beats { port => 5044 }
}
```

Listens for Beats/Lumberjack v2 connections on TCP 5044.

### 20-honeypot-filter.conf
1. Flatten `honeypot.*` → top-level fields (Ruby filter).
2. Coerce types (`src_port`, `dst_port`, `response_code` → int).
3. Convert `auth_success` → boolean.
4. GeoIP enrichment on `src_ip`.
5. Derive `attack_class` from `attack_type_hint` (Ruby map).
6. Add `lab_id`.
7. Drop noisy Filebeat internal fields.

### 90-honeypot-output.conf
```logstash
output {
  if [container_name] {
    elasticsearch {
      hosts => ["http://elasticsearch:9200"]
      index => "honeypot-logs-%{+YYYY.MM.dd}"
    }
  }
}
```

One index per day. The `index-template-honeypot.json` defines strict mappings
applied automatically when the first event of a new day arrives.

## 7.4 Verifying the pipeline

### On Computer 1
```bash
# Filebeat is shipping?
docker logs hp-filebeat | grep -i "connected"
# Should show: "Connected to 192.168.1.20:5044"
```

### On Computer 2
```bash
# Logstash is receiving?
curl -s http://127.0.0.1:9600/_node/stats/pipelines | jq '.pipelines.main.events'
# Should show non-zero "in" and "out" counters.

# Elasticsearch is indexing?
curl -s "http://127.0.0.1:9200/honeypot-logs-*/_count"
# Should return {"count":N,...}
```

### In Kibana
- *Stack Management → Index Patterns* should show `honeypot-logs-*`.
- *Discover* should show events with the canonical schema.
- Filter `attack_class: bruteforce` to see only brute-force events.

## 7.5 Troubleshooting the pipeline

| Symptom                                  | Likely cause                          | Fix                                          |
|------------------------------------------|---------------------------------------|----------------------------------------------|
| Filebeat logs "no route to host"         | Wrong `LOGSTASH_HOST` / ufw blocking  | Verify `.env`, open TCP 5044 on Computer 2   |
| Logstash `_grokparsefailure`             | Schema mismatch                       | Check `20-honeypot-filter.conf`              |
| Kibana shows "no results"                | Wrong time filter or index pattern    | Set time filter to "Last 15 minutes"         |
| Events missing `attack_class`            | Logstash filter didn't match          | Verify `attack_type_hint` is set in container|
| Elasticsearch red cluster                | Disk >85% full                         | Delete old indices with `configs/elk-retention.sh` |

## 7.6 Performance

On the reference hardware the pipeline handles ~5000 events/sec sustained
without back-pressure. The lab generates ~2000 events in total — nowhere near
the limit.
