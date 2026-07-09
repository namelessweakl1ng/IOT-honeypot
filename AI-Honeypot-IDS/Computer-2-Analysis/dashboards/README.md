# Kibana Dashboards

This folder contains the dashboard definitions for the honeypot SIEM. There are
two ways to load them:

1. **Automated** (recommended): run `setup_dashboards.sh` from Computer 2 after
   ELK is up. It uses the Kibana Saved Objects API to create the index
   pattern, visualizations, and dashboard in one shot.
2. **Manual**: import `honeypot-dashboards.ndjson` from
   *Stack Management → Saved Objects → Import* in the Kibana UI.

## Dashboards included

| Dashboard            | Panels                                                            |
|----------------------|-------------------------------------------------------------------|
| Honeypot Overview    | Top attackers, top ports, most-attacked container, attack timeline|
| Attack Breakdown     | Attack class donut, protocol bar, geo map, brute-force timeline   |
| Per-Container Drill  | One table per container with last 100 events                      |

## Visualizations

1. **Top Attackers** — `terms` agg on `src_ip` (bar chart)
2. **Top Targeted Ports** — `terms` agg on `dst_port` (pie)
3. **Most Attacked Container** — `terms` agg on `container_name` (bar)
4. **Attack Timeline** — `date_histogram` on `@timestamp` (line)
5. **Attack Class Heatmap** — `terms` on `attack_class` × `date_histogram` (heatmap)
6. **Geo Map** — `geo` aggregation on `geo.location` (coordinate map)
7. **Protocol Distribution** — `terms` on `protocol` (donut)
8. **Attack Type Breakdown** — `terms` on `attack_type_hint` (bar)
9. **Brute-Force Timeline** — filter `attack_class:bruteforce`, `date_histogram`
10. **Auth Success vs Failure** — `terms` on `auth_success` (gauge)

Run `./setup_dashboards.sh` once ELK is healthy.
