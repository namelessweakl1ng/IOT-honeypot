# 03 — Network Setup

## 3.1 IP plan

| Host        | IP            | MAC (example)     | Role           |
|-------------|---------------|-------------------|----------------|
| Router      | 192.168.1.1   | 00:1A:2B:3C:4D:5E | Gateway, DHCP  |
| Computer 1  | 192.168.1.10  | 00:1A:2B:3C:4D:01 | Honeypot       |
| Computer 2  | 192.168.1.20  | 00:1A:2B:3C:4D:02 | SIEM + ML      |
| Computer 3  | 192.168.1.30  | 00:1A:2B:3C:4D:03 | Attacker       |

Subnet: `192.168.1.0/24`. Netmask: `255.255.255.0`.

## 3.2 Router configuration

1. **WAN:** unplug the cable. The router must have NO upstream Internet.
2. **LAN IP:** set to `192.168.1.1`.
3. **DHCP server:** disable, OR reserve the three IPs above by MAC so they
   never change. We recommend static IPs on each host for stability.
4. **Wi-Fi:** disable (we are Ethernet-only for the demo).
5. **Firewall:** leave at defaults. The lab is air-gapped; the router's
   stateful firewall is sufficient.

## 3.3 Static IP assignment

### Ubuntu (Computer 1 & 2) — netplan

`/etc/netplan/01-lab.yaml`:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: no
      addresses:
        - 192.168.1.10/24   # 192.168.1.20 on Computer 2
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8]   # only used during install; remove after
```

Apply:

```bash
sudo netplan apply
ip a
```

### Kali (Computer 3)

Edit `/etc/network/interfaces`:

```
auto eth0
iface eth0 inet static
  address 192.168.1.30/24
  gateway 192.168.1.1
```

```bash
sudo systemctl restart networking
ip a
```

## 3.4 Hosts file

On every machine, add to `/etc/hosts`:

```
192.168.1.10   honeypot
192.168.1.20   siem
192.168.1.20   kibana
192.168.1.30   attacker
```

This lets us use `honeypot`, `siem`, `kibana`, `attacker` as hostnames in
scripts.

## 3.5 Firewall rules

### Computer 1 (ufw)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 8080:8087 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 9100 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 2222 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 2121 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 2323 proto tcp
sudo ufw enable
```

### Computer 2 (ufw)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.1.0/24 to any port 22 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 5601 proto tcp   # Kibana
sudo ufw allow from 192.168.1.10 to any port 5044 proto tcp     # Filebeat ingest
sudo ufw enable
```

### Computer 3

No inbound firewall restrictions (it is the attacker). Outbound unrestricted
within the lab.

## 3.6 Connectivity test

From each machine, ping the other two:

```bash
ping -c 3 192.168.1.10
ping -c 3 192.168.1.20
ping -c 3 192.168.1.30
```

Expected: 0% packet loss, <1 ms RTT.

## 3.7 Bandwidth & latency expectations

All three machines are on the same gigabit broadcast domain:
- Round-trip latency: < 1 ms.
- Throughput: ~940 Mbps (gigabit line rate).
- This is plenty for honeypot log shipping (Filebeat events are tiny).

## 3.8 Air-gap verification

Before every demo, verify the air-gap:

```bash
# On every machine:
ping -c 1 -W 2 8.8.8.8   # should fail with "Network is unreachable"
ping -c 1 -W 2 1.1.1.1   # should fail
curl -sI --max-time 3 https://example.com/   # should fail
```

If any of these succeeds, the router WAN is plugged in — UNPLUG IT before
running the honeypot.
