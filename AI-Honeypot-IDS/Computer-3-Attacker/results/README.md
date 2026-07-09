# Attack results

This folder holds the captured output of each attack script:

| File                       | Source script             | Contents                                   |
|----------------------------|---------------------------|--------------------------------------------|
| `01_portscan_*`            | 01_portscan.sh            | nmap + masscan output, banner grabs        |
| `02_bruteforce_*`          | 02_bruteforce.sh          | hydra output for SSH/FTP/Telnet/HTTP       |
| `03_webattacks.log`        | 03_webattacks.sh          | curl HTTP codes for every web attack       |
| `04_dirscan_*`             | 04_dirscan.sh             | gobuster/dirb directory listings           |
| `05_nikto_*`               | 05_nikto.sh               | nikto vulnerability scan reports           |
| `06_sqlmap/`               | 06_sqlmap.sh              | sqlmap dumps (users table)                 |
| `07_netcat_*`              | 07_netcat.sh              | banners, PJL abuse, revshell sim           |
| `08_dos_sim.txt`           | 08_dos_sim.sh             | request count summary                      |
| `09_custom_payloads.log`   | 09_custom_payloads.sh     | every delivered payload + HTTP code        |
| `10_credential_post_*`     | 10_credential_post.sh     | post-auth exfil/session captures           |

These are NOT committed by default (they contain lab IPs). They are
regenerated each time the demo is run.
