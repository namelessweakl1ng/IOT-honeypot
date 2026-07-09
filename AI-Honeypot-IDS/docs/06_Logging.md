# 06 — Logging

## 6.1 Log philosophy

Every interaction with every honeypot container produces exactly one
structured log line. The line is a JSON object with a fixed schema. This
makes parsing trivial (no regex), enables reliable downstream aggregation,
and gives the ML pipeline clean features.

## 6.2 Canonical log schema

```json
{
  "@timestamp": "2024-05-01T12:34:56.789Z",
  "container_name": "hp-http",
  "container_service": "http",
  "device_model": "ACME Shop",
  "honeypot_host_ip": "192.168.1.10",
  "src_ip": "192.168.1.30",
  "src_port": 54321,
  "dst_port": 8080,
  "protocol": "HTTP",
  "method": "GET",
  "path": "/product",
  "query": "id=1 UNION SELECT user,pass,1 FROM users",
  "username": "",
  "password": "",
  "payload": "1 UNION SELECT user,pass,1 FROM users",
  "user_agent": "curl/7.81.0",
  "attack_type_hint": "sql_injection",
  "response_code": 200,
  "auth_success": false,
  "lab_id": "ai-honeypot-ids",
  "shipper": "filebeat-computer-1",
  "source_host": "computer-1-honeypot"
}
```

After Logstash enrichment, two more fields are added:

```json
{
  "attack_class": "sqli",
  "geo": {
    "country_name": "United States",
    "region_name": "California",
    "city_name": "San Jose",
    "location": { "lat": 37.25, "lon": -121.9 }
  }
}
```

(In the lab, `src_ip` is `192.168.1.30` so GeoIP returns no data — this is
expected. GeoIP is configured for future Internet-facing deployments.)

## 6.3 Field dictionary

| Field               | Type    | Source                  | Meaning                                              |
|---------------------|---------|-------------------------|------------------------------------------------------|
| `@timestamp`        | date    | container app.py        | UTC ISO-8601 ms-precision                            |
| `container_name`    | keyword | Docker label            | e.g. `hp-http`                                       |
| `container_service` | keyword | Docker label            | e.g. `http`                                          |
| `device_model`      | keyword | env var                 | fake device banner                                   |
| `honeypot_host_ip`  | ip      | env var                 | Computer 1's IP                                      |
| `src_ip`            | ip      | socket peer             | attacker / client IP                                 |
| `src_port`          | int     | socket peer             | client ephemeral port                                |
| `dst_port`          | int     | container env           | honeypot port the request hit                        |
| `protocol`          | keyword | app.py                  | `HTTP`, `SSH`, `FTP`, `Telnet`, `PJL`                |
| `method`            | keyword | app.py                  | HTTP method or protocol command                      |
| `path`              | keyword | HTTP request            | URL path                                             |
| `query`             | text    | HTTP request            | URL query string                                     |
| `username`          | keyword | auth form / protocol    | submitted username                                   |
| `password`          | keyword | auth form / protocol    | submitted password                                   |
| `payload`           | text    | app.py (per-endpoint)   | the "interesting" input (cmd, SQL, path, …)          |
| `user_agent`        | keyword | HTTP header             | client UA                                            |
| `attack_type_hint`  | keyword | app.py classify()       | per-container heuristic (weak label)                 |
| `attack_class`      | keyword | Logstash filter         | coarse 11-class ML target (strong label)             |
| `response_code`     | int     | app.py                  | HTTP status / protocol return code                   |
| `auth_success`      | bool    | app.py                  | whether auth succeeded                               |
| `geo.*`             | —       | Logstash geoip filter   | country/region/city/geo_point                        |
| `lab_id`            | keyword | Filebeat processor      | always `ai-honeypot-ids`                             |
| `shipper`           | keyword | Filebeat processor      | `filebeat-computer-1`                                |

## 6.4 How a log line is produced

Take the SQLi example: an attacker runs

```
curl 'http://192.168.1.10:8080/product?id=1 UNION SELECT user,pass,1 FROM users'
```

Inside the `http` container:

1. Flask receives the request and routes it to `product()`.
2. `product()` reads `id` from `request.args`.
3. `classify("/product", "id=1 UNION ...", "")` scans the payload for SQL
   keywords and returns `"sql_injection"`.
4. The query is built and executed (`SELECT * FROM products WHERE id=1
   UNION SELECT user,pass,1 FROM users`) — the SQLite engine returns rows
   from the `users` table.
5. `emit_log({"payload": id, "attack_type_hint": atk, "response_code": 200,
   "db_output": body})` prints one JSON line to stdout.

The Docker `json-file` driver appends that line to
`/var/lib/docker/containers/<id>/<id>-json.log`. Filebeat tails the file,
decodes the JSON, and ships it to Logstash. Logstash adds `attack_class`
and `geo`, then indexes into Elasticsearch.

End-to-end latency from request to Kibana visibility: <2 seconds.

## 6.5 `attack_type_hint` → `attack_class` mapping

Defined in `Computer-2-Analysis/elk/logstash/conf.d/20-honeypot-filter.conf`:

| `attack_type_hint`     | `attack_class` |
|------------------------|----------------|
| benign                 | benign         |
| login_success          | benign         |
| ftp_login_success      | benign         |
| recon                  | recon          |
| directory_enum         | recon          |
| ftp_connect            | recon          |
| telnet_connect         | recon          |
| telnet_error           | recon          |
| ssh_protocol_error     | recon          |
| sql_injection          | sqli           |
| command_injection      | cmdi           |
| ssh_command_injection  | cmdi           |
| ssh_command_exec       | cmdi           |
| telnet_command_exec    | cmdi           |
| xss                    | xss            |
| path_traversal         | traversal      |
| brute_force_login      | bruteforce     |
| ssh_brute_force        | bruteforce     |
| ftp_brute_force        | bruteforce     |
| telnet_brute_force     | bruteforce     |
| ssh_key_attempt        | bruteforce     |
| ftp_retr               | exfil          |
| ftp_stor               | implant        |
| file_upload            | implant        |
| ssrf                   | ssrf           |
| printer_abuse          | abuse          |

## 6.6 Log volume estimates

For the lab demo (10 attack scripts + 30 rounds of benign seed traffic):

| Phase              | Events   | Notes                              |
|--------------------|----------|------------------------------------|
| Benign seed        | ~270     | 30 rounds × 9 endpoints            |
| Port scan (nmap)   | ~200     | one per probed port                |
| Brute force        | ~540     | 20 users × 27 passwords × ~1 svc   |
| Web attacks        | ~30      | 1 per curl in script 03            |
| Dir scan           | ~120     | 60 paths × 2 web roots             |
| Nikto              | ~500     | nikto sends ~500 requests/scan     |
| sqlmap             | ~100     | detection + dump probes            |
| Netcat / PJL       | ~10      | banner + PJL + revshell sim        |
| DoS sim            | ~200     | 200 rapid requests                 |
| Custom payloads    | ~25      | 1 per deliver()                    |
| Post-auth exfil    | ~10      | SSH + FTP + Telnet                 |
| **Total**          | **~2005**| Enough for a meaningful ML dataset |

For a more substantial dataset, run the attack suite 5–10 times and the seed
traffic for 10+ minutes.
