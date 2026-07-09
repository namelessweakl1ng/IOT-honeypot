# FTP honeypot
Port 2121 (passive 30000-30010). pyftpdlib-based. Banner mimics
`ProFTPD 1.3.5`. Weak credentials:
| user | pass  | perms       |
|------|-------|-------------|
| admin| admin | elr         |
| ftp  | ftp   | elr         |
| root | toor  | elradfmw    |
| anonymous | (any) | elr    |

Logs every connect, login success/failure, RETR, STOR, logout.

## Sample attack
```
hydra -L users.txt -P pass.txt ftp://192.168.1.10:2121
curl ftp://admin:admin@192.168.1.10:2121/pub/config.bak
```
