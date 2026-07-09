# CCTV Camera honeypot — README

## Purpose
Emulates an IP camera web panel (`admin/admin` default credentials, vulnerable
`/streams?id=` command-injection endpoint, and `/admin?file=` path traversal).
Logs every HTTP interaction as JSON to stdout.

## Build & run
```
cd Computer-1-Honeypot
docker compose build camera
docker compose up -d camera
```

## Ports
| Host port | Container port | Protocol | Purpose                |
|-----------|----------------|----------|------------------------|
| 8081      | 5000           | HTTP     | Web panel + REST API   |

## Endpoints
| Method | Path             | Behaviour                                  |
|--------|------------------|--------------------------------------------|
| GET    | `/`              | Login page                                 |
| GET/POST | `/login`       | Checks u/p against `admin/admin`           |
| GET    | `/streams?id=`   | Runs `echo` with shell — **cmd injection** |
| GET    | `/admin?file=`   | Reads any file — **path traversal**        |
| GET    | `/healthz`       | Health probe                               |

## Logs emitted
One JSON line per request with fields:
`@timestamp, container_name, container_service, src_ip, src_port, dst_port,
protocol, method, path, query, username, password, payload, user_agent,
attack_type_hint, response_code`.

## Viva questions (sample)
- Q: Why is `shell=True` dangerous here?
  A: It invokes a shell, so user input is interpreted as shell syntax, enabling
  `;`, `|`, `$()` command chaining — exactly the cmd-injection class.
- Q: How would you fix it?
  A: Use `subprocess.run(["echo", sid], shell=False)` and validate `sid` with
  a strict regex (`^\d+$`).
