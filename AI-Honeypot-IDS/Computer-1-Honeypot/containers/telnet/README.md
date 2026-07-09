# Telnet honeypot
Port 2323. Raw-socket Telnet server (pure stdlib). Banner: `BCM96338 ADSL
Router`. Fake BusyBox shell. Weak creds: `admin/admin`, `root/toor`,
`user/user`, `pi/raspberry`. Logs every login attempt and post-auth command.

## Sample attack
```
nc 192.168.1.10 2323
hydra -L users.txt -P pass.txt telnet://192.168.1.10:2323
```
