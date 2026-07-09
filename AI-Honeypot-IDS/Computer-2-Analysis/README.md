# Computer 2 — SIEM, Log Collector & ML Training

> **Presenter notes for the Computer 2 team member.**
> Print this document and use it as speaking notes for the viva and demo.

---

## 1. Role of Computer 2

Computer 2 is the **brain** of the project. It does four things:

1. **Receives** logs from Computer 1's Filebeat (Logstash on TCP 5044).
2. **Stores & visualizes** them (Elasticsearch + Kibana dashboards).
3. **Transforms** them into a labeled ML dataset (Python pipeline).
4. **Trains and evaluates** six classifiers, saving the best as a deployable
   artifact.

> ⚠️ The trained model is **NOT** wired into live detection in this project.
> It is saved as a joblib artifact that can later be deployed in a SIEM,
> firewall, EDR, or cloud security product. This is documented in
> `docs/14_Future_Work.md` and in the README inside `trained_models/`.

---

## 2. Hardware & OS

| Item         | Spec                                       |
|--------------|--------------------------------------------|
| CPU          | 8 cores x86_64 (ML training is CPU-bound)  |
| RAM          | 16 GB minimum (32 GB recommended)          |
| Disk         | 256 GB SSD (Elasticsearch is disk-hungry)  |
| NIC          | 1 GbE                                      |
| OS           | Ubuntu Server 22.04 LTS                    |
| IP (static)  | 192.168.1.20/24                            |
| Gateway      | 192.168.1.1                                |

---

## 3. Folder structure

```
Computer-2-Analysis/
├── README.md                          ← this file
├── Makefile                           ← elk-up/down, ingest/train/evaluate targets
├── elk/
│   ├── docker-compose-elk.yml         ← 3 services + setup container
│   ├── elasticsearch/
│   │   ├── elasticsearch.yml          ← single-node, security disabled (lab)
│   │   └── index-template-honeypot.json ← field mappings + ILM
│   ├── logstash/
│   │   ├── logstash.yml               ← host/port, logging
│   │   ├── pipelines.yml              ← declares the honeypot pipeline
│   │   ├── conf.d/
│   │   │   ├── 10-honeypot-input.conf   ← beats input on :5044
│   │   │   ├── 20-honeypot-filter.conf  ← json flatten, geoip, attack_class
│   │   │   └── 90-honeypot-output.conf  ← daily index honeypot-logs-YYYY.MM.dd
│   │   └── patterns/honeypot.grok     ← reserved grok patterns
│   └── kibana/
│       └── kibana.yml                 ← 0.0.0.0:5601, default app dashboards
├── dashboards/
│   ├── README.md
│   ├── setup_dashboards.sh           ← creates index pattern + viz via API
│   └── honeypot-dashboards.ndjson    ← bulk-import saved objects
├── ml/
│   ├── README.md
│   ├── requirements.txt
│   ├── src/
│   │   ├── config.py                 ← paths, labels, model specs
│   │   ├── 01_ingest.py              ← ES → raw.parquet
│   │   ├── 02_features.py            ← features → features.parquet + scaler
│   │   ├── 03_train.py               ← CV + train 6 models
│   │   ├── 04_evaluate.py            ← confusion matrix, ROC, comparison
│   │   └── 05_dataset_stats.py       ← EDA → reports/dataset_stats.md
│   ├── data/                         ← raw.parquet, features.parquet
│   ├── models/                       ← *.joblib + scaler + feature_columns
│   ├── reports/                      ← metrics + plots
│   └── notebooks/                    ← optional EDA notebooks
└── configs/
    ├── README.md
    └── elk-retention.sh              ← delete old indices (cron)
```

---

## 4. ELK Stack — component by component

### 4.1 Elasticsearch
- **Image:** `docker.elastic.co/elasticsearch/elasticsearch:8.13.4`
- **Mode:** single-node, security **disabled** (air-gapped lab only).
- **Heap:** 1 GB (`ES_JAVA_OPTS=-Xms1g -Xmx1g`).
- **Index pattern:** `honeypot-logs-YYYY.MM.dd` (one index per day).
- **Index template** (`index-template-honeypot.json`): strict mappings for
  every honeypot field, including `geo.location` as `geo_point`.
- **Port:** 9200 (REST API — used by the ML ingest script too).
- **Healthcheck:** `curl http://localhost:9200/_cluster/health`.

### 4.2 Logstash
- **Image:** `docker.elastic.co/logstash/logstash:8.13.4`
- **Input:** `beats { port => 5044 }` — receives from Computer 1's Filebeat.
- **Filter pipeline** (`conf.d/20-honeypot-filter.conf`):
  1. Flatten the `honeypot.*` object that Filebeat's `decode_json_fields`
     produced into top-level fields.
  2. Coerce types (`src_port`, `dst_port`, `response_code` → integer,
     `auth_success` → boolean).
  3. **GeoIP enrichment** on `src_ip` (bundled MaxMind DB).
  4. Derive `attack_class` from `attack_type_hint` via a Ruby map (the
     canonical 11-class taxonomy used for ML).
  5. Drop noisy Filebeat internal fields.
- **Output:** daily index in Elasticsearch.
- **Ports:** 5044 (ingest), 9600 (monitoring API).

### 4.3 Kibana
- **Image:** `docker.elastic.co/kibana/kibana:8.13.4`
- **Port:** 5601 (HTTP — no TLS in lab).
- **Default app:** dashboards.
- **Index pattern:** `honeypot-logs-*` with `@timestamp` time field
  (created automatically by `setup_dashboards.sh`).

---

## 5. Dashboards

Loaded via `dashboards/setup_dashboards.sh` (or manual NDJSON import). The
"Honeypot Overview" dashboard contains 7 panels:

| # | Panel                  | Aggregation                                         |
|---|------------------------|-----------------------------------------------------|
| 1 | Top Attackers          | `terms` on `src_ip`, bar chart                      |
| 2 | Top Targeted Ports     | `terms` on `dst_port`, donut                        |
| 3 | Most Attacked Container| `terms` on `container_name`, bar                    |
| 4 | Attack Timeline        | `date_histogram` on `@timestamp`, stacked line      |
| 5 | Attack Class Breakdown | `terms` on `attack_class`, donut                    |
| 6 | Protocol Distribution  | `terms` on `protocol`, donut                        |
| 7 | Attacker Geo Map       | `geohash_grid` on `geo.location`, coordinate map    |

> `[Take Screenshot Here]` — Kibana Overview dashboard, full screen, last-24h
> time filter, after a few minutes of attacks.

---

## 6. Machine-learning pipeline

### 6.1 Stage 1 — ingest (`01_ingest.py`)

- Scrolls the `honeypot-logs-*` indices with the Elasticsearch Python client.
- Flattens nested `geo` object.
- Writes `data/raw.parquet`.
- Also writes a friendly CSV export to `../../datasets/honeypot_dataset.csv`
  for sharing with evaluators.

### 6.2 Stage 2 — features (`02_features.py`)

For each event we build:

**Numeric features (20):**
- `src_port`, `dst_port`, `response_code`
- `payload_len`, `path_len`, `query_len`, `username_len`, `password_len`, `ua_len`
- `hour_of_day`, `day_of_week`, `is_weekend`
- `auth_attempt`, `auth_success_int`
- `special_chars_payload`, `digit_ratio_payload`, `uppercase_ratio_payload`
- `has_sql_keywords`, `has_cmd_keywords`, `has_xss_keywords`, `has_traversal_keywords`

**Categorical features (4, one-hot encoded):**
- `container_service`, `protocol`, `method`, `geo_country`

**Label:**
- `attack_class` (11 classes; see `config.LABELS`).

Numeric features are scaled with `StandardScaler` (also saved for inference).
The scaler + one-hot column list are persisted so the model can be deployed
without re-fitting.

### 6.3 Stage 3 — train (`03_train.py`)

- Stratified 80/20 train/test split.
- 5-fold stratified cross-validation on the train set.
- Trains six models in parallel where supported:
  - Logistic Regression (baseline)
  - Decision Tree
  - Random Forest
  - SVM (RBF, probability=True)
  - XGBoost
  - LightGBM
- Saves each model to `models/<name>.joblib`.
- Saves consolidated CV metrics to `reports/cv_metrics.json`.
- Writes the best model name to `reports/best_model.txt` (by test F1 macro).

### 6.4 Stage 4 — evaluate (`04_evaluate.py`)

For every model:
- Computes test accuracy, macro precision/recall/F1, weighted F1.
- Saves a confusion matrix PNG.
- Saves a per-class classification report (JSON).

For the best model only:
- Plots an OvR micro-averaged ROC curve (requires `predict_proba`).

Then:
- Writes `reports/summary.json` and `reports/model_comparison.csv`.
- Copies the best model + scaler + feature_columns + labels into the
  project-root `trained_models/` folder for handover.

> `[Take Screenshot Here]` — `model_comparison.csv` printed in the terminal.
> `[Take Screenshot Here]` — confusion matrix PNG of the best model.
> `[Take Screenshot Here]` — ROC curve PNG of the best model.

---

## 7. Label taxonomy

The ML target is `attack_class`, an 11-class taxonomy derived from
`attack_type_hint` in Logstash:

| `attack_class` | Meaning                                   | Example sources                 |
|-----------------|-------------------------------------------|---------------------------------|
| `benign`        | No suspicious pattern                     | Seed traffic, successful logins |
| `recon`         | Reconnaissance                            | `/api/config`, dirb hits, nmap  |
| `sqli`          | SQL injection                             | `/login?u=' OR 1=1--`           |
| `cmdi`          | Command injection                         | `/streams?id=1;id`              |
| `xss`           | Cross-site scripting                      | `/search?q=<script>`            |
| `traversal`     | Path traversal                            | `/admin?file=../../etc/passwd`  |
| `bruteforce`    | Brute-force auth attempts                 | hydra runs                      |
| `exfil`         | Data exfiltration                         | FTP RETR                        |
| `implant`       | Implantation / upload                     | FTP STOR, file upload           |
| `ssrf`          | Server-side request forgery               | `/cast?url=http://attacker/`    |
| `abuse`         | Protocol abuse (e.g. printer PJL)         | Raw PJL payloads                |

---

## 8. Why the model is NOT deployed in this project

This is a **research deliverable**, not a production system. The academic
objective is to prove that Docker-honeypot logs can be turned into a labeled
dataset capable of training a high-accuracy multi-class classifier.

The trained artifacts (`best_model_*.joblib`, `scaler.joblib`,
`feature_columns.json`, `labels.json`) are **deployment-ready**. The
`trained_models/README.md` documents exactly how a downstream system would
load and use them. Section 12 below lists the candidate deployment targets.

---

## 9. Installation (end-to-end)

```bash
# 1. Install Docker + Compose v2 (see docs/04_Docker.md)
# 2. Install Python 3.11 + venv
sudo apt install -y python3.11 python3.11-venv python3.11-dev build-essential
python3.11 -m venv ~/.venvs/honeypot-ml
source ~/.venvs/honeypot-ml/bin/activate
pip install --upgrade pip
pip install -r Computer-2-Analysis/ml/requirements.txt

# 3. Start ELK
cd Computer-2-Analysis
make elk-up
# wait ~60s for Elasticsearch

# 4. Load dashboards
make dashboards

# 5. After attacks have been run from Computer 3, run the ML pipeline:
make all-models
```

---

## 10. Demo procedure (Computer 2 presenter)

1. **"This is Computer 2, the SIEM and ML training machine, at 192.168.1.20."**
   - `ip a` shows static IP.
   - `[Take Screenshot Here]`

2. **"ELK is up."**
   - `make elk-status` shows three healthy containers.
   - `[Take Screenshot Here]` Container status table.

3. **"Logs are arriving from Computer 1."**
   - `curl -s http://127.0.0.1:9200/honeypot-logs-*/_count` shows a non-zero
     count (the seed traffic plus any attacks already run).

4. **"Open Kibana."**
   - Browser → `http://192.168.1.20:5601`, click Dashboards → "Honeypot
     Overview".
   - `[Take Screenshot Here]` Dashboard with live data.

5. **"As attacks come in, watch the panels update."**
   - Switch back to Computer 3, run the attack suite, switch back to Kibana.
   - `[Take Screenshot Here]` Top attackers panel showing 192.168.1.30.
   - `[Take Screenshot Here]` Attack class breakdown donut.
   - `[Take Screenshot Here]` Geo map (will be mostly the lab subnet /
     localhost; explain this is because the lab is air-gapped).

6. **"Now we extract the dataset."**
   - `make ingest` — shows "N events in honeypot-logs-*".
   - `make stats` — show class distribution.

7. **"Train six models."**
   - `make train` — runs ~1–3 min depending on dataset size; show CV metrics
     printing live.
   - `[Take Screenshot Here]` CV metrics table.

8. **"Evaluate and compare."**
   - `make evaluate` — prints model_comparison.csv.
   - Open `reports/confusion_matrix_<best>.png` and `reports/roc_curve_<best>.png`.
   - `[Take Screenshot Here]` Confusion matrix.
   - `[Take Screenshot Here]` ROC curve.

9. **"The best model is saved."**
   - `ls trained_models/` — show the four handover files.

10. **"Future deployment."**
    - Walk through the deployment-target list (Section 12 below).
    - Emphasize: model is NOT in the live path — it is a saved artifact.

---

## 11. Troubleshooting (Computer 2 specific)

| Symptom                                        | Fix                                                       |
|------------------------------------------------|-----------------------------------------------------------|
| `make elk-up` exits but ES is red              | `docker logs elk-elasticsearch`; usually memory_lock      |
| Kibana shows "no indices"                      | Run `make dashboards`; verify index pattern exists        |
| `01_ingest.py` returns 0 events                | Confirm Computer 1 filebeat is shipping; check ufw 5044   |
| Logstash drops events                          | `docker logs elk-logstash`; check `20-honeypot-filter`    |
| `03_train.py` OOM                              | Lower `n_estimators`, subsample the dataset, increase RAM |
| XGBoost import fails                           | `pip install xgboost==2.0.3 --no-build-isolation`         |
| `make evaluate` skips ROC                      | SVM/best model must have `predict_proba` (it does)        |

Full troubleshooting guide: `docs/13_Troubleshooting.md`.

---

## 12. Where the trained model could be deployed (future work)

> These are **future** deployment paths. None of them are wired in this
> project — they are documented to show the committee the real-world value
> of the trained artifact.

| Target                        | How it would consume the model                                |
|-------------------------------|---------------------------------------------------------------|
| **SIEM (Splunk/Elastic/Wazuh)**| A scheduled search ships candidate events to an inference     |
|                               | microservice that loads `best_model_*.joblib` and returns a  |
|                               | label + probability; high-probability malicious events raise  |
|                               | alerts.                                                       |
| **Firewall / inline IDS**     | A eBPF/Zeek tap mirrors flow metadata to the classifier;      |
|                               | on `malicious` verdict the firewall inserts a drop rule.     |
| **EDR / XDR**                 | Endpoint sensor enriches process/network events with the     |
|                               | model's verdict as a risk score.                              |
| **Cloud security platform**   | A serverless function (Lambda/Cloud Run) loads the joblib,    |
|                               | ingests VPC flow + CloudTrail, tags anomalies.                |
| **SOAR playbook**             | The classifier's output triggers an automated containment    |
|                               | workflow (isolate host, block IP, rotate creds).             |

See `docs/14_Future_Work.md` for the full discussion.

---

## 13. Viva questions (Computer 2 presenter)

**Q1.** Why did you choose ELK over Graylog or OpenSearch?
**A1.** ELK is the de-facto standard in SOCs and has the richest Kibana
visualization ecosystem. Graylog is excellent but its dashboards are weaker
out-of-the-box. OpenSearch is a viable fork but we chose the canonical Elastic
stack to maximize transferability of the skills demonstrated.

**Q2.** Why disable xpack security?
**A2.** The lab is air-gapped on `192.168.1.0/24` with no Internet uplink.
Disabling TLS and auth simplifies the demo and avoids certificate
bootstrapping overhead. In production we would enable TLS, RBAC, API keys,
and audit logging.

**Q3.** How does Logstash enrich the logs?
**A3.** Three ways: (1) it flattens the JSON that Filebeat's
`decode_json_fields` produced; (2) it runs GeoIP on `src_ip` to add country,
region, city, and geo_point; (3) it derives a coarse `attack_class` label from
the per-container `attack_type_hint` heuristic, which becomes the ML target.

**Q4.** Why do you derive `attack_class` in Logstash and not in Python?
**A4.** Centralizing the labeling logic in Logstash means every consumer
(Kibana dashboards, the ML pipeline, future SIEM alerts) sees the same label.
If we labeled in Python we'd have to re-implement the mapping in every
downstream system.

**Q5.** Why six models instead of just one?
**A5.** Different model families have different inductive biases. We train a
linear baseline (Logistic Regression), two tree-based families (Decision Tree,
Random Forest), a kernel method (SVM), and two gradient-boosted trees
(XGBoost, LightGBM). Comparing them empirically on the same dataset is the
scientifically honest way to choose the best classifier for this data.

**Q6.** How do you handle class imbalance?
**A6.** Three mechanisms: (1) stratified train/test split and stratified
5-fold CV so every fold sees all classes; (2) `class_weight="balanced"` on
the tree/sklearn models so minority classes get higher loss weight; (3)
macro-averaged F1 as the primary metric (not accuracy) so minority classes
count as much as the majority. We could also apply SMOTE (imbalanced-learn
is in requirements.txt) but the balanced class weights were sufficient.

**Q7.** Why is F1 macro your primary metric?
**A7.** Accuracy is misleading under imbalance — a model that predicts
"benign" for everything gets ~60% accuracy on this dataset but is useless.
F1 macro averages the F1 of each class equally, so it punishes models that
ignore minority classes.

**Q8.** Why is the model NOT deployed?
**A8.** Three reasons: (1) the academic objective is the methodology, not a
production system; (2) deploying an inline classifier changes the honeypot's
behavior (it would block attacks, defeating the data-collection purpose);
(3) deployment is a separate engineering project with its own latency,
safety, and rollback requirements. We document the deployment path in
`trained_models/README.md` and `docs/14_Future_Work.md` so the artifact is
immediately usable.

**Q9.** How long does training take?
**A9.** On the reference hardware (8 cores, 16 GB) with a ~50k-event dataset,
the full `03_train.py` run takes 2–4 minutes. SVM is the slowest (O(n²) in the
training-set size); the tree-based models scale near-linearly.

**Q10.** What's the expected accuracy?
**A10.** On the lab dataset, Random Forest and XGBoost typically reach
>0.98 test F1 macro because the honeypot produces very clean signatures
(SQL keywords, shell metacharacters). Real Internet noise would lower this
significantly — which is exactly why future work includes adversarial
robustness testing (see `docs/14_Future_Work.md`).

---

## 14. Ethical & safety statement

Computer 2 stores attacker-attribution data (source IPs). In the air-gapped
lab these are all private IPs (`192.168.1.30`), but the pipeline supports
GeoIP enrichment for future Internet-facing deployments. No data leaves the
lab except via the operator's manually inspected export to the project
report.

---

**End of Computer 2 README.**
