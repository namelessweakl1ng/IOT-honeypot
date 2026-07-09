# SSH honeypot
Port 2222. Low-interaction paramiko-based SSH server. Banner mimics
`OpenSSH_8.2p1 Ubuntu`. Accepts any password for weak usernames
(`admin, root, pi, user, ubuntu, test, guest, support, service, oracle`) and
provides a fake shell that logs every command. Captures brute-force,
credential-stuffing, and post-auth command attempts.

## Sample attack (from Computer 3)
```
hydra -L users.txt -P pass.txt ssh://192.168.1.10:2222
sshpass -p anything ssh -p 2222 admin@192.168.1.10 'cat /etc/passwd'
```
