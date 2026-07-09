# 14 — Future Work

## 14.1 Real-time model inference

The most obvious next step is to **deploy the trained model** as an inline
classifier. Several integration paths:

### 14.1.1 Inside Logstash (ruby-filter → inference microservice)
- Run a small FastAPI/Flask service on Computer 2 that loads
  `best_model_*.joblib` + `scaler.joblib`.
- Add a Logstash `http` filter that POSTs each event to the service and
  adds the predicted `attack_class` + probability as new fields.
- High-probability malicious events raise alerts (Elastic Alerting / Kibana
  Rules).

### 14.1.2 In a SIEM (Splunk / Elastic / Wazuh)
- A scheduled search exports candidate events to the inference service.
- Results are written back as a lookup/enrichment.
- SIEM correlation rules fire on the predicted label.

### 14.1.3 On a firewall / inline IDS
- A Zeke/eBPF tap mirrors flow metadata to the classifier.
- On a `malicious` verdict the firewall inserts a drop rule.
- Latency budget: <50 ms per event (achievable with the saved joblib models
  on commodity hardware).

### 14.1.4 In an EDR / XDR
- Endpoint sensor enriches process/network events with the model's verdict.
- The verdict becomes a risk-score component.

### 14.1.5 In a cloud security platform
- A serverless function (AWS Lambda / GCP Cloud Run) loads the joblib.
- VPC Flow Logs + CloudTrail events are streamed to it.
- Anomalies are tagged in the SIEM.

### 14.1.6 In a SOAR playbook
- The classifier's output triggers automated containment: isolate host,
  block IP, rotate credentials, snapshot the honeypot.

## 14.2 Honeypot enhancements

- **Federation:** multiple geographically distributed honeypots feeding one
  SIEM. This produces a much more diverse dataset and enables
  attack-campaign tracking.
- **Higher-interaction SSH/FTP/Telnet:** swap our minimal Python honeypots
  for Cowrie (medium-interaction SSH/Telnet) or a real FTP server in a
  sandboxed VM.
- **Real firmware emulation:** use Firmadyne or ARAT to emulate actual IoT
  firmware images instead of Flask lookalikes.
- **Container-escape detection:** install Falco on the Docker host to detect
  attempts to break out of a container.

## 14.3 Threat-intel enrichment

- Add Logstash filters that query AbuseIPDB, VirusTotal, and AlienVault OTX
  for each `src_ip` at ingest time.
- Tag events with `threat_intel.reputation` (clean / suspicious / malicious).
- Use the reputation as an additional ML feature.

## 14.4 ML improvements

- **Adversarial robustness:** generate adversarial payloads (e.g. SQLi with
  whitespace/comment evasion) and re-train. Measure the drop in accuracy.
- **Deep learning:** compare against an LSTM/Transformer on the raw payload
  text (no hand-engineered features).
- **Online learning:** retrain the model incrementally as new honeypot data
  arrives.
- **Explainability:** add SHAP values to the saved model so an analyst can
  see *why* an event was classified malicious.
- **Class taxonomy extension:** split `benign` into `benign_normal` vs
  `benign_dos_burst`; add a `dos` class based on per-source-IP request rate.

## 14.5 Operationalization

- **CI/CD for the model:** version the dataset, the model, and the metrics;
  auto-retrain on a schedule; canary-deploy new models alongside the old one.
- **Model monitoring:** track prediction distribution drift; alert if the
  benign/malicious ratio shifts dramatically.
- **Audit trail:** every prediction logged with model version + feature
  snapshot for forensic review.

## 14.6 Security hardening of the lab itself

- Enable TLS + RBAC in Elasticsearch.
- Move Filebeat → Logstash to mutual TLS.
- Add an audit log on Computer 1 recording every `docker exec` and `docker
  compose` command.
- Sign container images and verify on deploy.

## 14.7 Reporting

- Auto-generate a weekly PDF report from Kibana dashboards.
- Push key metrics (events/day, top attacker, model F1) to a Slack/Teams
  channel via webhook.

## 14.8 Open research questions

1. Does a model trained on lab data generalize to Internet-facing honeypots?
2. How quickly does model accuracy decay as attackers evolve their
   techniques?
3. Can we use the honeypot's own logs to *generate* adversarial examples
   automatically?
4. Is there a single "universal" feature set that works across all honeypot
   types (web, SSH, FTP, IoT REST), or must each surface have its own model?

These questions are the natural follow-up research directions and could
form the basis of a Master's thesis.
