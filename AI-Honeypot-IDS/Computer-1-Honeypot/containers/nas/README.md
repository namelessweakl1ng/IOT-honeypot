# NAS Storage honeypot
Port 8086 → 5000. Default creds `admin/admin123`. Vulnerabilities:
`/api/files?path=` (path traversal), `/api/snapshot?name=` (cmd injection),
`/api/share` (info disclosure).
