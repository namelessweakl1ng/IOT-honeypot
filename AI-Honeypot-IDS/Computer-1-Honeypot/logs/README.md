# Local log cache

This folder is a **local fallback** for honeypot logs. In normal operation
logs are NOT stored here — they are streamed straight to stdout, picked up by
the Docker `json-file` driver, and shipped by Filebeat to Computer 2.

Files you might find here (if the `seed-traffic.sh` or `healthcheck.sh`
scripts are configured to write locally):

* `honeypot-host.log` — host-level helper script logs (not container stdout).

> **Note:** Container stdout logs live under `/var/lib/docker/containers/`
> on the Docker host, NOT in this folder. Filebeat reads them from there.

## Log schema (canonical JSON)

Every log event produced by every container is a single JSON line with at
least these fields:

```json
{
  "@timestamp": "2024-05-01T12:34:56.789Z",
  "container_name": "hp-http",
  "container_service": "http",
  "src_ip": "192.168.1.30",
  "src_port": 54321,
  "dst_port": 8080,
  "protocol": "HTTP",
  "method": "GET",
  "path": "/login?u=admin&pw=' OR 1=1--",
  "payload": "u=admin&pw=' OR 1=1--",
  "username": "admin",
  "password": "' OR 1=1--",
  "user_agent": "sqlmap/1.7",
  "attack_type_hint": "sqli",
  "response_code": 200,
  "response_bytes": 1234
}
```

See `docs/06_Logging.md` for the full field dictionary and how each field is
populated.
