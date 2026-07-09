# 04 — Docker

## 4.1 Why Docker?

| Benefit          | How we use it                                        |
|------------------|------------------------------------------------------|
| Isolation        | Each honeypot service runs in its own container      |
| Reproducibility  | Dockerfiles + compose let anyone rebuild the lab     |
| Fast spin-up     | 11 services start in <30 s                           |
| Per-container log| `json-file` driver captures stdout → Filebeat        |
| Network control  | Custom bridge `honeypot_net` with static IPs         |
| Easy teardown    | `docker compose down` resets the honeypot state      |

## 4.2 Installation (Ubuntu 22.04)

```bash
# Prereqs
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

# Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Repo
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list

# Install
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
  docker-buildx-plugin docker-compose-plugin

# Non-root access
sudo usermod -aG docker $USER
# log out, log back in, verify:
docker --version
docker compose version
docker run --rm hello-world
```

## 4.3 Docker networking

`docker-compose.yml` declares a custom bridge network `honeypot_net` with
subnet `172.20.0.0/16` and assigns each container a static IP (e.g.
`172.20.0.11` for the camera). This is **inside** the Docker host — the
attacker (192.168.1.30) reaches the honeypots via the host's published ports
(8081, 8082, …), not the Docker IPs directly.

```
Attacker (192.168.1.30)
   │  TCP → 192.168.1.10:8081
   ▼
Computer 1 host (192.168.1.10)
   │  iptables DNAT → 172.20.0.11:5000
   ▼
camera container (172.20.0.11:5000)
```

## 4.4 Docker logging driver

Each container uses the `json-file` driver with rotation:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

This prevents any single container's log from filling the disk. Filebeat
reads from `/var/lib/docker/containers/<id>/<id>-json.log`.

## 4.5 Health checks

Every container defines a `HEALTHCHECK`. The compose `start.sh` waits up to
60 s for all containers to become healthy before declaring success.

## 4.6 Resource limits (optional)

For labs with limited RAM, add to each service in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 256M
      cpus: "0.5"
```

We omit these by default because the lab has plenty of RAM, but they are
useful when running on a laptop.

## 4.7 Cleanup

```bash
# Stop and remove containers (keeps images)
docker compose down

# Stop + remove containers + volumes + dangling images
docker compose down -v
docker image prune -f

# Nuclear option (also removes all built images)
docker compose down -v --rmi local
```

## 4.8 Common Docker commands used in the project

| Command                                          | Purpose                       |
|--------------------------------------------------|-------------------------------|
| `docker compose build`                           | Build all images              |
| `docker compose up -d`                           | Start in background           |
| `docker compose ps`                              | Status table                  |
| `docker compose logs -f --tail=50`               | Tail all logs                 |
| `docker compose logs -f hp-http`                 | Tail one service              |
| `docker compose restart hp-camera`               | Restart one service           |
| `docker compose exec hp-http sh`                 | Shell into a container        |
| `docker stats`                                   | Live resource usage           |
| `docker system df`                               | Disk usage                    |
