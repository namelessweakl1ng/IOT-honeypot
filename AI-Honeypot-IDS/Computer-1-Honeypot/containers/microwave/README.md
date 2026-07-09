# Smart Microwave honeypot
Port 8082 → 5000. REST API for a smart microwave. Vulnerabilities: no auth on
`/cook`, `program` param passed to `eval()` (Python code injection), arbitrary
timer values accepted.

## Endpoints
| Method | Path          | Notes                                  |
|--------|---------------|----------------------------------------|
| GET    | `/`           | device info                            |
| GET    | `/status`     | current state                          |
| GET/POST | `/cook`     | `program=` eval()'d — RCE              |
| POST   | `/door`       | open/close door                        |

## Sample attack
```
curl 'http://192.168.1.10:8082/cook?program=__import__("os").popen("id").read()'
```
