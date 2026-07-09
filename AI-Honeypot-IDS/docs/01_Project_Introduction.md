# 01 — Project Introduction

## 1.1 Motivation

Modern enterprise networks are under constant attack. Intrusion Detection
Systems (IDS) are the primary line of defense, but they rely on signatures
that lag behind new attack techniques. **Deception technology** — honeypots
— flips the asymmetry: instead of waiting for an attack to hit a real asset,
we deploy fake assets that have no production value. Any interaction with
them is, by definition, suspicious. This produces extremely clean labeled
data, ideal for training machine-learning intrusion detectors.

## 1.2 Problem statement

> Can logs collected from a Docker-based IoT honeypot be transformed into a
> labeled dataset capable of training a multi-class intrusion-detection
> classifier with high accuracy?

## 1.3 Hypothesis

We hypothesize that:

1. A honeypot of 11 Docker containers emulating IoT devices and common
   services can be operated safely inside an air-gapped lab.
2. Every interaction can be captured as a structured JSON log with a
   per-event heuristic attack-type hint.
3. Forwarding those logs to a centralized ELK Stack enables real-time
   visualization and dataset extraction.
4. The resulting dataset, after feature engineering, can train at least one
   classifier to >0.95 macro-F1 across 11 attack classes.

## 1.4 Scope

This project delivers:

- A working Docker honeypot (Computer 1).
- A working ELK-based SIEM (Computer 2).
- A working Python ML training pipeline (Computer 2).
- A working attacker machine with 10 labeled attack scripts (Computer 3).
- Complete documentation: 18 markdown files, 3 per-computer READMEs, and a
  master README.

## 1.5 Out of scope

- Live deployment of the trained model (see `14_Future_Work.md`).
- Internet-facing honeypot operation.
- Hardware IoT firmware emulation (we emulate behavior, not real firmware).
- Adversarial robustness testing of the classifier.

## 1.6 Ethical framework

This project is conducted under the following constraints:

1. **Air-gapped lab:** The `192.168.1.0/24` network has no Internet uplink
   during the demo.
2. **Self-owned assets:** All attack targets are honeypots we own and
   operate.
3. **No third-party harm:** No traffic leaves the lab; no real user data is
   processed.
4. **Educational purpose:** The goal is to learn and demonstrate defensive
   cybersecurity techniques, not offensive capability.

## 1.7 Expected outcomes

| Outcome                                  | Success criterion                       |
|------------------------------------------|-----------------------------------------|
| 11 honeypot containers running           | `make health` returns all OK            |
| Logs flowing to ELK                      | Kibana shows non-zero events            |
| 10+ attack classes represented           | `attack_class` distribution has ≥8 classes |
| ML dataset of ≥10k events                | `data/raw.parquet` row count            |
| Best model F1 macro ≥0.95                | `reports/summary.json`                  |
| Saved deployable model artifact          | `trained_models/best_model_*.joblib`    |

## 1.8 Project team roles

| Member                  | Owns                                        |
|-------------------------|---------------------------------------------|
| Computer 1 presenter    | Honeypot containers, Docker, Filebeat       |
| Computer 2 presenter    | ELK Stack, ML pipeline, dashboards          |
| Computer 3 presenter    | Attack scripts, dataset generation          |
| Project lead            | Master README, integration, docs            |
