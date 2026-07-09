# 02 — Hardware

## 2.1 Bill of materials

| # | Item                                | Qty | Notes                                  |
|---|-------------------------------------|-----|----------------------------------------|
| 1 | Desktop PC (Computer 1)             | 1   | 4-core CPU, 8 GB RAM, 40 GB SSD        |
| 2 | Desktop PC (Computer 2)             | 1   | 8-core CPU, 16 GB RAM, 256 GB SSD      |
| 3 | Laptop / mini PC (Computer 3)       | 1   | Kali Linux, 4 GB RAM, 40 GB SSD        |
| 4 | 4-port gigabit router               | 1   | Any home router; managed switch OK     |
| 5 | Cat6 Ethernet cables                | 3   | One per computer                       |
| 6 | USB stick (for OS install)          | 1   | 8 GB+                                  |
| 7 | Monitor + keyboard (setup only)     | 1   | Each machine imaged headless after     |

## 2.2 Per-machine specs justification

### Computer 1 — Honeypot (8 GB RAM)
- 11 Docker containers each running a Python web server.
- Filebeat sidecar.
- Docker daemon overhead.
- 8 GB is comfortable; 4 GB would be tight.

### Computer 2 — Analysis (16 GB RAM, 8-core)
- Elasticsearch heap: 1 GB.
- Logstash heap: 512 MB.
- Kibana: ~1 GB.
- ML training: scikit-learn + XGBoost + LightGBM can each use multiple
  cores; 8 cores + 16 GB runs the full pipeline in 2–4 minutes on a 50k-row
  dataset.
- 32 GB is recommended if you intend to scale to a larger honeypot.

### Computer 3 — Attacker (4 GB RAM, 4-core)
- Kali runs tools that are mostly single-threaded and short-lived. 4 GB is
  plenty. Could even run on a Raspberry Pi 4.

## 2.3 BIOS / UEFI settings

On every machine:
- Disable Secure Boot (Kali install + unsigned kernel modules).
- Enable VT-x / AMD-V (Docker on Computer 1 & 2).
- Disable Wake-on-LAN (not needed; lab is powered on demand).
- Set power profile to "performance" (avoid CPU throttling during ML).

## 2.4 Cabling

```
[Cable 1] Computer 1 NIC ── Router LAN port 1
[Cable 2] Computer 2 NIC ── Router LAN port 2
[Cable 3] Computer 3 NIC ── Router LAN port 3
```

The router's WAN port is intentionally left **unplugged** during the demo.

## 2.5 Power

Each machine on its own UPS or on a single lab power strip with surge
protection. Total power draw: ~150 W (Computer 1) + ~200 W (Computer 2) +
~50 W (Computer 3) = ~400 W peak.

## 2.6 Imaging

Each machine is imaged from a bootable USB created with `dd` or Rufus:

```bash
# Example: write Ubuntu Server 22.04 ISO to /dev/sdX
sudo dd if=ubuntu-22.04-live-server-amd64.iso of=/dev/sdX bs=4M status=progress && sync
```

Kali ISO: <https://www.kali.org/get-kali/>
Ubuntu Server: <https://ubuntu.com/download/server>
