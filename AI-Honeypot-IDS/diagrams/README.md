# Diagrams

This folder contains the project's architecture and network diagrams in
multiple formats.

## Files
- `01_network_topology.txt` — ASCII art network topology
- `02_architecture.mmd` — Mermaid architecture diagram (render in any Mermaid viewer, GitHub, or Kibana)
- `03_log_flow.mmd` — Mermaid data/log flow diagram
- `04_ml_pipeline.mmd` — Mermaid ML training pipeline diagram
- `05_attack_to_class.mmd` — Mermaid mapping of attack scripts → attack_class

## Rendering Mermaid
- GitHub renders `.mmd` inside ```` ```mermaid ```` blocks in Markdown.
- Or paste into https://mermaid.live/
- Or install the Mermaid CLI: `npm i -g @mermaid-js/mermaid-cli` then
  `mmdc -i 02_architecture.mmd -o 02_architecture.png`
