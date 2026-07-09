# 16 — Project Presentation

Speaking scripts for each presenter. Print and read aloud during the demo.

---

## 16.1 Project Lead — Introduction (3 minutes)

> Good morning/afternoon, distinguished members of the evaluation
> committee. Our Final Year Project is titled **"AI Based Honeypot IDS
> using Docker Containers and Centralized Log Analysis."**
>
> The problem we address is this: modern Intrusion Detection Systems rely on
> signatures that lag behind new attack techniques. We propose a
> deception-based approach — a honeypot of intentionally vulnerable Docker
> containers that emulate IoT devices and common servers.
>
> Our project spans three computers on an air-gapped lab network:
> - Computer 1 is the honeypot, running 11 vulnerable Docker containers.
> - Computer 2 is the SIEM and ML training machine, running the ELK Stack
>   and a Python machine-learning pipeline.
> - Computer 3 is the attacker, running Kali Linux with a suite of ten
>   attack scripts.
>
> Every interaction with the honeypot is logged as structured JSON,
> forwarded to the SIEM, visualized in Kibana, transformed into a labeled
> dataset, and used to train six machine-learning classifiers. The best
> model is saved as a deployable artifact that can later be integrated into
> a SIEM, firewall, EDR, or cloud security product.
>
> I'll now hand over to the Computer 1 presenter.

---

## 16.2 Computer 1 Presenter — Honeypot (5 minutes)

> Thank you. Computer 1 is the deception layer of our project, hosted at
> 192.168.1.10. We run eleven Docker containers, each emulating a different
> vulnerable IoT device or network service.
>
> *[Show `make status` output]*
>
> These include a CCTV camera with command injection and path traversal, a
> smart microwave whose REST API passes user input to `eval()`, a smart TV
> with SSRF, a router login panel, a NAS, a printer with raw PJL on port
> 9100, and SSH, FTP, HTTP, and Telnet honeypots with weak credentials.
>
> Every interaction — benign or malicious — is captured as a structured
> JSON log line and shipped in real time to Computer 2 by Filebeat.
>
> *[Show `docker logs hp-http | head -1`]*
>
> Here's a sample log line. You can see the timestamp, source IP, port,
> protocol, payload, and an attack-type hint that the per-container
> heuristic computed.
>
> Filebeat uses Docker autodiscover: any container with the `honeypot=true`
> label is automatically picked up. The logs travel over TCP port 5044 to
> Logstash on Computer 2.
>
> We also seed benign baseline traffic so the ML model has a normal class
> to learn from. *[Run `make seed` briefly]*
>
> All healthy — handing over to Computer 2.

---

## 16.3 Computer 2 Presenter — SIEM & ML (8 minutes)

> Thank you. Computer 2 at 192.168.1.20 is the brain of our project. It
> does four things: receives logs, stores and visualizes them, transforms
> them into a labeled dataset, and trains six machine-learning classifiers.
>
> *[Show `make elk-status`]*
>
> We run Elasticsearch, Logstash, and Kibana — the ELK Stack. Logstash
> listens on port 5044 for Filebeat, parses the JSON, enriches it with
> GeoIP, and derives a coarse `attack_class` label that becomes the ML
> target.
>
> *[Open Kibana, show Overview dashboard]*
>
> Here's our Kibana dashboard. As attacks come in from Computer 3, you'll
> see the panels update in real time: top attackers, top targeted ports,
> most attacked container, attack timeline, attack-class breakdown, protocol
> distribution, and a geo map.
>
> *[Switch to Computer 3 briefly, run `run_all_attacks.sh`, switch back to
> Kibana periodically]*
>
> Now we extract the dataset. *[Run `make ingest`]*
>
> *[Run `make stats` — show class distribution]*
>
> The dataset has roughly two thousand events across eleven classes. We
> engineer twenty numeric features — lengths, ratios, signature flags,
> time-of-day — and four categorical features. We scale numerics with
> StandardScaler and one-hot encode categoricals.
>
> *[Run `make train`]*
>
> We train six models: Logistic Regression as a baseline, Decision Tree,
> Random Forest, SVM, XGBoost, and LightGBM. Five-fold stratified
> cross-validation. *[Show CV metrics printing]*
>
> *[Run `make evaluate`]*
>
> *[Show confusion matrix PNG]*
> *[Show ROC curve PNG]*
>
> Our best model achieves over ninety-eight percent macro-F1 on the held-out
> test set. We save it as a joblib artifact.
>
> *[Show `ls trained_models/`]*
>
> **Important:** the trained model is NOT deployed in this project. It is
> saved as a deployment-ready artifact. The `trained_models/README.md`
> documents exactly how a SIEM, firewall, EDR, or cloud security product
> would load and use it. This separation keeps the honeypot passive (so it
> keeps collecting data) while making the model available for future
> deployment.

---

## 16.4 Computer 3 Presenter — Attacker (5 minutes)

> Thank you. Computer 3 at 192.168.1.30 is the attacker machine, running
> Kali Linux 2024.1.
>
> *[Show `ls scripts/`]*
>
> We have ten attack scripts, each targeting a specific class of
> vulnerability:
>
> 1. **Port scanning** with nmap and masscan.
> 2. **Brute force** with hydra against SSH, FTP, Telnet, and the router
>    login panel.
> 3. **Web attacks** — SQL injection, command injection, XSS, path
>    traversal, SSRF — delivered via curl.
> 4. **Directory enumeration** with gobuster and dirb.
> 5. **Nikto** web vulnerability scanning.
> 6. **sqlmap** automated SQL injection exploitation — it dumps the users
>    table from the vulnerable web app.
> 7. **Netcat** for banner grabbing, printer PJL abuse, and a reverse-shell
>    payload simulation.
> 8. A controlled **DoS simulation** — a burst of two hundred requests to
>    create a visible spike in the timeline.
> 9. A curated suite of **custom payloads** covering every variant of every
>    attack class — this is our primary dataset-generation script.
> 10. **Post-authentication activity** — once brute force discovers weak
>     credentials, we log in, exfiltrate data, and upload an implant.
>
> Every attack is labeled because every script has a known intent. This is
> what gives us clean ground-truth labels for the ML pipeline.
>
> *[Show one attack result, e.g. `cat results/06_sqlmap/main/main.log |
> tail -20`]*
>
> Here sqlmap has dumped the users table — admin, alice, bob with their
> passwords. The honeypot captured every probe.

---

## 16.5 Project Lead — Conclusion (2 minutes)

> To summarize: we built a three-computer deception-based IDS laboratory.
> Computer 1 hosts eleven vulnerable Docker honeypots. Computer 2 runs the
> ELK SIEM and a Python ML pipeline that trains six classifiers on the
> captured logs. Computer 3 generates a labeled attack dataset via ten
> attack scripts.
>
> Our best model — Random Forest / XGBoost — achieves over ninety-eight
> percent macro-F1 across eleven attack classes. The trained artifact is
> saved and ready for future deployment in a SIEM, firewall, EDR, or cloud
> security product.
>
> The entire project — code, configs, documentation, and presentation
> notes — is in the repository. Every folder has a README. Every
> configuration file is commented line-by-line.
>
> Thank you. We welcome your questions.

---

## 16.6 Suggested slide deck (one slide per topic)

1. Title slide
2. Problem statement
3. Architecture diagram (the ASCII one from the master README)
4. Network topology (Mermaid rendered)
5. Computer 1 — containers table
6. Computer 1 — log schema
7. Computer 2 — ELK architecture
8. Computer 2 — Kibana dashboard screenshot
9. Computer 2 — ML pipeline diagram
10. Computer 2 — model comparison table
11. Computer 2 — confusion matrix screenshot
12. Computer 2 — ROC curve screenshot
13. Computer 3 — attack scripts list
14. Computer 3 — sample attack output (sqlmap)
15. Attack-to-ATT&CK mapping
16. Future work
17. Limitations
18. References
19. Thank you / Q&A
