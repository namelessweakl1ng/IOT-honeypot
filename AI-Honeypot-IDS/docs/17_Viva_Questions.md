# 17 — Viva Questions

Likely viva questions, organized by topic, with model answers.

---

## 17.1 Architecture & design

**Q1.** Why three computers? Could you do this on one?
**A.** Three computers reflect real-world separation of concerns: the
honeypot (deception), the SIEM (detection & analysis), and the attacker
(simulation). Doing it on one machine would conflate these roles and
defeat the network-level realism. It's also how a real SOC operates — the
honeypot is on the production network, the SIEM is in a separate management
network, and the analyst's workstation is separate again.

**Q2.** Why an air-gapped network?
**A.** Two reasons: (1) safety — the honeypot is intentionally vulnerable,
so exposing it to the Internet would invite real attackers and potentially
make us part of a botnet; (2) control — on an air-gapped network we control
100% of the traffic, so the dataset is clean and reproducible.

**Q3.** How would you scale this to an enterprise deployment?
**A.** The honeypot scales horizontally (more containers, more hosts behind
a load balancer). Logstash scales with multiple pipelines and workers.
Elasticsearch scales by adding nodes (the index template already supports
sharding; we just set replicas to 0 for the single-node lab). The ML
pipeline scales by sampling the dataset or moving to distributed frameworks
like Spark MLlib.

---

## 17.2 Honeypot (Computer 1)

**Q4.** What is a honeypot? How does it differ from an IDS?
**A.** A honeypot is a decoy system with no production value — any traffic
to it is suspicious by definition. An IDS monitors real traffic for
suspicious patterns. A honeypot produces *cleaner* data (no false positives
from legitimate use) but covers only the traffic that reaches it.

**Q5.** Low-interaction vs high-interaction honeypots — where does yours sit?
**A.** Ours is low-to-medium interaction. The HTTP containers are medium
(they have real Flask apps with real vulnerabilities); the SSH/FTP/Telnet
honeypots are low (they accept credentials and log commands but don't
execute them). A high-interaction honeypot would run a real OS in a
sandboxed VM.

**Q6.** How does an attacker not realize they're in a honeypot?
**A.** In our lab, the attacker *knows* (we are the attacker). In a real
deployment you'd: (1) match banners to real firmware versions, (2) place
the honeypot on a believable IP range, (3) respond at realistic speeds,
(4) vary the honeypot's "vulnerabilities" so it doesn't look too perfectly
broken.

**Q7.** How does Filebeat know which containers to log?
**A.** Docker label `honeypot=true` set in `docker-compose.yml`. Filebeat's
`autodiscover` provider subscribes to the Docker event stream and matches
on that label.

**Q8.** What happens if a container crashes?
**A.** `restart: unless-stopped` brings it back. The healthcheck marks it
unhealthy after 3 failed probes; `make status` flags this. Logs from before
the crash are preserved in Elasticsearch.

---

## 17.3 SIEM & logging (Computer 2)

**Q9.** Why Elasticsearch and not a relational database for logs?
**A.** Elasticsearch is a distributed search engine optimized for
time-series, semi-structured data. It handles full-text search, nested
fields, aggregations, and geo queries orders of magnitude faster than a
relational DB on this workload. It also scales horizontally.

**Q10.** What is an Elasticsearch index? Why one per day?
**A.** An index is a logical partition of data with its own Lucene shards.
One-per-day makes it trivial to delete old data (drop the whole index
instead of deleting rows) and to query a specific day efficiently. The
index template applies our strict mappings automatically when a new daily
index is created.

**Q11.** Why is `attack_class` derived in Logstash and not in Python?
**A.** Centralizing the mapping in Logstash means every consumer (Kibana,
ML pipeline, future alerting) sees the same label. If we labeled in Python
we'd have to re-implement the mapping in every downstream system.

**Q12.** How does Logstash handle a surge of events?
**A.** Logstash pipelines have a bounded in-memory queue plus persistent
queue support. Multiple worker threads process events in parallel. If the
queue fills, Filebeat's own in-memory queue buffers up to 4096 events and
retries.

**Q13.** What is GeoIP enrichment?
**A.** Looking up the country/region/city/geo-coordinates of a source IP
using a MaxMind database. We do it in Logstash so every event is enriched
at ingest time. In the lab all IPs are private so it returns nothing; in
an Internet deployment it populates the geo map automatically.

---

## 17.4 Machine learning (Computer 2)

**Q14.** Why six models?
**A.** Different model families have different inductive biases. Comparing
them empirically on the same dataset is the scientifically honest way to
choose. We include a linear baseline (Logistic Regression), trees (Decision
Tree, Random Forest), a kernel method (SVM), and two gradient-boosted
trees (XGBoost, LightGBM).

**Q15.** Why Random Forest over a single Decision Tree?
**A.** A single tree overfits. Random Forest averages many trees trained on
bootstrapped samples with random feature subsets, which dramatically
reduces variance and improves generalization.

**Q16.** Why F1 macro as the primary metric?
**A.** Our dataset is imbalanced (benign/recon/bruteforce dominate).
Accuracy is misleading — a model that predicts "benign" for everything
gets ~30% accuracy but is useless. Macro F1 averages each class's F1
equally, so it punishes models that ignore minority classes.

**Q17.** How do you handle class imbalance?
**A.** Three mechanisms: (1) stratified train/test split and stratified
5-fold CV; (2) `class_weight="balanced"` so minority classes get higher
loss weight; (3) macro-averaged F1 as the primary metric. We could also
apply SMOTE (it's in requirements.txt) but balanced class weights were
sufficient.

**Q18.** What is cross-validation? Why stratified?
**A.** K-fold CV splits the training set into K folds, trains on K-1 and
validates on the held-out fold, K times. The mean validation score is a
less biased estimate of generalization than a single train/test split.
Stratified means each fold preserves the class distribution, which is
critical for imbalanced data.

**Q19.** Why is the model NOT deployed?
**A.** (1) The academic objective is the methodology, not a production
system; (2) an inline classifier would change the honeypot's behavior
(blocking attacks defeats data collection); (3) deployment is a separate
engineering project with its own latency, safety, and rollback requirements.
The artifact is deployment-ready and the deployment paths are documented.

**Q20.** How would you deploy the model in a SIEM?
**A.** Wrap the joblib in a small HTTP microservice. Have the SIEM (Splunk
or Elastic) call it for each candidate event. Add the predicted class +
probability as enrichment fields. Alert on high-probability malicious
predictions.

**Q21.** What is overfitting? How do you avoid it?
**A.** Overfitting is when a model learns the training data so well
(including noise) that it fails to generalize. We avoid it by: (1) holding
out a test set the model never sees during training; (2) cross-validation
on the train set; (3) limiting tree depth; (4) using ensembles that
average out individual trees' overfitting; (5) monitoring the train vs
validation gap.

**Q22.** Could an attacker evade this model?
**A.** Yes — for example, SQLi with whitespace/comments to break the
keyword regex, or command injection with rare metacharacters. This is
called adversarial ML and is exactly why Future Work includes adversarial
robustness testing.

**Q23.** How long does training take?
**A.** On 8 cores + 16 GB with a 2k-event dataset, the full `03_train.py`
takes 2–4 minutes. SVM is the slowest (O(n²) in training-set size); the
tree models are near-instant.

**Q24.** What's the difference between XGBoost and LightGBM?
**A.** Both are gradient-boosted trees. XGBoost grows trees level-wise;
LightGBM grows leaf-wise (best-first). LightGBM is typically faster and
uses less memory; XGBoost has a longer track record. We include both and
let the data decide.

---

## 17.5 Attacks (Computer 3)

**Q25.** What is SQL injection?
**A.** A vulnerability where user input is concatenated into a SQL query
without parameterization. An attacker can break out of the intended query
and execute arbitrary SQL — read data (`UNION SELECT`), modify data, or in
some cases execute OS commands (`xp_cmdshell` on SQL Server). The fix is
parameterized queries.

**Q26.** What is command injection?
**A.** User input is concatenated into a shell command (`subprocess.run(f"...
{input}", shell=True)`). An attacker injects shell metacharacters (`;`,
`|`, `&&`, `$()`, backticks) to chain additional commands. The fix is
`shell=False` with a list of arguments, plus input validation.

**Q27.** What is SSRF?
**A.** Server-Side Request Forgery: the server fetches a URL supplied by
the user. An attacker can make the server fetch internal resources (the
cloud metadata IP `169.254.169.254`, internal services, `file://` URIs).
The fix is an allowlist of permitted hosts/schemes.

**Q28.** What is path traversal?
**A.** User input is concatenated into a file path without normalization.
`../../etc/passwd` escapes the intended directory. The fix is to
canonicalize the path with `os.path.realpath` and verify it stays within an
allowed root.

**Q29.** What is a reverse shell?
**A.** A shell where the victim machine connects outbound to the attacker's
listener (rather than the attacker connecting in). It bypasses ingress
firewalls because the connection is initiated from inside. We *simulate*
the payload delivery in our lab; we don't run a real listener.

**Q30.** How does hydra parallelize?
**A.** N threads, each opening an independent connection. `-f` stops on
first success. We throttle to 4 threads for telnet because its handshake
is slow.

**Q31.** How does nmap `-sS` work?
**A.** It sends a raw TCP SYN packet. If the target responds with
SYN-ACK, the port is open; nmap then sends RST to tear down the half-open
connection (no application-level log). Requires root for raw sockets.

---

## 17.6 Ethics & safety

**Q32.** Could this project be misused?
**A.** The attack scripts are standard pentest tools and publicly
available. The honeypot code is intentionally vulnerable and clearly
labeled as such. We mitigate misuse by: (1) running only in an air-gapped
lab, (2) requiring explicit authorization before any test, (3) documenting
the legal framework in every README.

**Q33.** What legal frameworks apply?
**A.** In India, the IT Act 2000 (especially Sections 43 and 66) and the
Indian Penal Code. Internationally, the US Computer Fraud and Abuse Act,
the UK Computer Misuse Act, and the EU GDPR (for any personal data
processed). All require explicit authorization before testing any system
you don't own.

**Q34.** What's the difference between a pentest and a honeypot?
**A.** A pentest is an authorized active attack on a known target to find
vulnerabilities. A honeypot is a passive decoy that observes attackers who
come to it. Both are defensive techniques; they produce different kinds of
intelligence.
