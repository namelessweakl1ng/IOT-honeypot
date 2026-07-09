# 18 — References

## 18.1 Academic papers

1. Spitzner, L. (2003). *Honeypots: Tracking Hackers.* Addison-Wesley.
   — The foundational text on honeypot theory and deployment.

2. Provos, N. (2004). *A Virtual Honeypot Framework.* USENIX Security
   Symposium. — Introduces Honeyd, the basis for most low-interaction
   honeypots.

3. Thonnard, O., & Dacier, M. (2008). *A Framework for Attack Patterns'
   Discovery in Honeynet Data.* DFRWS. — On extracting attack patterns
   from honeypot logs.

4. Nawrocki, M., Wählisch, M., et al. (2021). *A Survey on Honeypot
   Software and Data Analysis.* ACM Computing Surveys. — Modern survey
   covering Cowrie, T-Pot, and others.

5. Sommer, R., & Paxson, V. (2010). *Outside the Closed World: On Using
   Machine Learning for Network Intrusion Detection.* IEEE S&P. — Classic
   paper on the challenges of ML for IDS.

6. Buczak, A. L., & Guven, E. (2016). *A Survey of Data Mining and
   Machine Learning Methods for Cyber Security Intrusion Detection.*
   IEEE Communications Surveys & Tutorials.

7. Sharafaldin, I., Lashkari, A. H., & Ghorbani, A. A. (2018). *Toward
   Generating a New Intrusion Detection Dataset and Intrusion Traffic
   Characterization.* ICISSP. — The NSL-KDD / CICIDS2017 lineage.

8. Cohen, G., et al. (2018). *Omni: A Malware Detection System Based on
   Honeypot Data.* IEEE.

## 18.2 Tools (with versions used in this project)

| Tool          | Version | Purpose                       | URL                                            |
|---------------|---------|-------------------------------|------------------------------------------------|
| Docker        | 24+     | Container runtime             | https://www.docker.com/                        |
| Docker Compose| v2      | Multi-container orchestration | https://docs.docker.com/compose/               |
| Filebeat      | 8.13.4  | Log shipper                   | https://www.elastic.co/beats/filebeat          |
| Elasticsearch | 8.13.4  | Search & storage              | https://www.elastic.co/elasticsearch/          |
| Logstash      | 8.13.4  | Log parsing & enrichment      | https://www.elastic.co/logstash                |
| Kibana        | 8.13.4  | Visualization                 | https://www.elastic.co/kibana                  |
| Python        | 3.11    | ML runtime                    | https://www.python.org/                        |
| scikit-learn  | 1.5.0   | Classical ML                  | https://scikit-learn.org/                      |
| XGBoost       | 2.0.3   | Gradient-boosted trees        | https://xgboost.readthedocs.io/                |
| LightGBM      | 4.3.0   | Gradient-boosted trees        | https://lightgbm.readthedocs.io/               |
| pandas        | 2.2.2   | Dataframes                    | https://pandas.pydata.org/                     |
| imbalanced-learn | 0.12.3 | Resampling                  | https://imbalanced-learn.org/                  |
| paramiko      | 3.4.0   | SSH library (honeypot)        | https://www.paramiko.org/                      |
| pyftpdlib     | 1.5.9   | FTP library (honeypot)        | https://github.com/giampaolo/pyftpdlib         |
| Flask         | 3.0.3   | Web framework (honeypot)      | https://flask.palletsprojects.com/             |
| nmap          | 7.94+   | Port scanner                  | https://nmap.org/                              |
| masscan       | 1.3+    | Fast port scanner             | https://github.com/robertdavidgraham/masscan   |
| hydra         | 9.5+    | Brute force                   | https://github.com/vanhauser-thc/thc-hydra     |
| nikto         | 2.5+    | Web vulnerability scanner     | https://github.com/sullo/nikto                 |
| gobuster      | 3.6+    | Directory enumeration         | https://github.com/OJ/gobuster                 |
| sqlmap        | 1.8+    | Automated SQLi                | https://sqlmap.org/                            |
| netcat        | any     | Raw TCP / banner grab         | https://nc110.sourceforge.io/                  |

## 18.3 Standards & frameworks

- **MITRE ATT&CK** — https://attack.mitre.org/ — adversary tactics &
  techniques taxonomy used to map our attack classes in `docs/11_Attacks.md`.
- **NIST SP 800-94** — Guide to Intrusion Detection and Prevention Systems.
- **NIST SP 800-61** — Computer Security Incident Handling Guide.
- **ISO/IEC 27037** — Guidelines for identification, collection,
  acquisition and preservation of digital evidence.
- **OWASP Top 10** — https://owasp.org/Top10/ — the web vulnerabilities
  our `http` container implements (A01 Broken Access Control, A03 Injection,
  A07 Identification & Authentication Failures, etc.).
- **CIS Docker Benchmark** — hardening guidelines we reference for the
  honeypot containers.

## 18.4 Related open-source projects

- **Cowrie** — medium-interaction SSH/Telnet honeypot.
  https://github.com/cowrie/cowrie
- **T-Pot** — all-in-one honeypot platform by Telekom Security.
  https://github.com/telekom-security/tpotce
- **Dionaea** — multi-protocol honeypot (SMB, FTP, TFTP, HTTP, …).
  https://github.com/DinoTools/dionaea
- **Honeyd** — the original low-interaction honeypot framework.
  https://github.com/DataSoft/Honeyd
- **ConPot** — ICS/SCADA honeypot.
  https://github.com/mushorg/conpot
- **Elastic Stack** documentation — https://www.elastic.co/guide/

## 18.5 Books

- Spitzner, L. (2002). *Honeypots: Tracking Hackers.* Addison-Wesley.
- Schroeder, B. (2014). *Cybersecurity: Attack and Defense Strategies.*
- Chio, K., & Freeman, L. (2018). *Machine Learning and Security.* O'Reilly.
- SANS Institute Reading Room — https://www.sans.org/reading-room/

## 18.6 Datasets referenced for comparison

- **NSL-KDD** — refined KDD'99 intrusion dataset.
- **CICIDS2017** — modern intrusion dataset from the Canadian Institute for
  Cybersecurity.
- **UNSW-NB15** — comprehensive network attack dataset.
- **CTU-13** — botnet traffic dataset from CTU Prague.

These are the canonical benchmarks our approach is spiritually aligned
with; our dataset is smaller (lab-scale) but has cleaner labels because it
is generated by scripts with known intent.

## 18.7 Image / icon credits

All diagrams in this repository are original work. No third-party images
are included.

---

> If you cite this project in academic work, please use the citation format
> in the master README §21.
