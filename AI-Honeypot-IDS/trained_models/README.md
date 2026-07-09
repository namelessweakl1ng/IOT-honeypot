# Trained models

This folder is the **handover artifact** for the trained IDS classifier. It
is produced by `Computer-2-Analysis/ml/src/04_evaluate.py` and contains
everything needed to deploy the model in a downstream system.

## Files

| File                          | Purpose                                              |
|-------------------------------|------------------------------------------------------|
| `best_model_<name>.joblib`    | The best-performing classifier (joblib-serialized)   |
| `scaler.joblib`               | The StandardScaler fitted on training numerics       |
| `feature_columns.json`        | The exact feature column order expected by the model |
| `labels.json`                 | The label string ↔ integer id mapping                |
| `README.md`                   | This file                                            |

> The `<name>` placeholder is filled in by `04_evaluate.py` based on the
> best model name written to `reports/best_model.txt` (typically
> `random_forest` or `xgboost`).

## ⚠️ The model is NOT deployed in this project

This artifact is **trained and saved only**. It is not wired into live
detection. The academic objective of this project is the *methodology* —
proving that Docker-honeypot logs can train a high-accuracy multi-class
classifier. Deployment is treated as future engineering work, documented
below and in `docs/14_Future_Work.md`.

## Loading and using the model for inference

```python
import joblib, json
import pandas as pd
import numpy as np

# 1. Load artifacts
model   = joblib.load("best_model_random_forest.joblib")
scaler  = joblib.load("scaler.joblib")
cols    = json.loads(open("feature_columns.json").read())
labels  = json.loads(open("labels.json").read())

# 2. Build the same feature vector the training pipeline produced.
#    `event` is a dict with the same fields as a honeypot log line.
def featurize(event: dict) -> np.ndarray:
    import re
    SQL = re.compile(r"\b(union|select|insert|update|delete|drop|or 1=1|information_schema|sleep\(|benchmark\(|--|;)\b", re.I)
    CMD = re.compile(r"(\$?\(|`|;|\||&&|\|\||/bin/sh|/bin/bash|cat |wget |curl |nc |/etc/passwd)", re.I)
    XSS = re.compile(r"(<script|onerror=|javascript:|<img src=x|<svg|alert\()", re.I)
    TRV = re.compile(r"(\.\./|\.\.\\|%2e%2e|/etc/passwd|/etc/shadow|c:\\windows)", re.I)
    p = str(event.get("payload", "")) or ""
    u = str(event.get("username", "")) or ""
    pw = str(event.get("password", "")) or ""
    ua = str(event.get("user_agent", "")) or ""
    ts = pd.to_datetime(event.get("@timestamp"), utc=True, errors="coerce")
    row = {
        "src_port": int(event.get("src_port") or 0),
        "dst_port": int(event.get("dst_port") or 0),
        "response_code": int(event.get("response_code") or 0),
        "payload_len": len(p), "path_len": len(str(event.get("path",""))),
        "query_len": len(str(event.get("query",""))),
        "username_len": len(u), "password_len": len(pw), "ua_len": len(ua),
        "hour_of_day": ts.hour if ts is not pd.NaT else 0,
        "day_of_week": ts.dayofweek if ts is not pd.NaT else 0,
        "is_weekend": int(ts.dayofweek in (5,6) if ts is not pd.NaT else False),
        "auth_attempt": int(bool(u)),
        "auth_success_int": int(str(event.get("auth_success")).lower() in ("true","1","yes")),
        "special_chars_payload": sum(1 for c in p if not c.isalnum() and c != " "),
        "digit_ratio_payload": sum(c.isdigit() for c in p) / max(len(p),1),
        "uppercase_ratio_payload": sum(c.isupper() for c in p) / max(len(p),1),
        "has_sql_keywords": int(bool(SQL.search(p))),
        "has_cmd_keywords": int(bool(CMD.search(p))),
        "has_xss_keywords": int(bool(XSS.search(p))),
        "has_traversal_keywords": int(bool(TRV.search(p))),
    }
    # Categorical one-hot — must match training columns exactly
    cat_vals = {
        "container_service": event.get("container_service","unknown"),
        "protocol":          event.get("protocol","unknown"),
        "method":            event.get("method","unknown"),
        "geo_country":       (event.get("geo") or {}).get("country_name","unknown") if isinstance(event.get("geo"),dict) else "unknown",
    }
    for col in cols:
        if col.startswith("cat_"):
            # cat_<field>_<value>
            _, field, value = col.split("_", 2)
            row[col] = int(cat_vals.get(field,"") == value)
    df = pd.DataFrame([row]).reindex(columns=cols, fill_value=0)
    # Scale numerics (first 20 columns are numeric — see config.NUMERIC_FEATURES)
    NUM = ["src_port","dst_port","response_code","payload_len","path_len",
           "query_len","username_len","password_len","ua_len","hour_of_day",
           "day_of_week","is_weekend","auth_attempt","auth_success_int",
           "special_chars_payload","digit_ratio_payload","uppercase_ratio_payload",
           "has_sql_keywords","has_cmd_keywords","has_xss_keywords",
           "has_traversal_keywords"]
    df[NUM] = scaler.transform(df[NUM])
    return df.values

# 3. Predict
event = {"@timestamp":"2024-05-01T12:00:00Z","container_service":"http",
         "src_port":54321,"dst_port":8080,"response_code":200,
         "payload":"1 UNION SELECT user,pass,1 FROM users",
         "username":"","password":"","user_agent":"curl/7.81",
         "protocol":"HTTP","method":"GET","auth_success":False}
X = featurize(event)
pred_id = int(model.predict(X)[0])
proba = model.predict_proba(X)[0]
print(f"Predicted: {labels[pred_id]}  (p={proba[pred_id]:.3f})")
```

## Where this model could be deployed

| Target                        | How it would consume the model                                |
|-------------------------------|---------------------------------------------------------------|
| **SIEM (Splunk/Elastic/Wazuh)**| A scheduled search ships candidate events to an inference     |
|                               | microservice that loads this joblib and returns label + prob. |
| **Firewall / inline IDS**     | An eBPF/Zeek tap mirrors flow metadata to the classifier;     |
|                               | on `malicious` verdict the firewall inserts a drop rule.      |
| **EDR / XDR**                 | Endpoint sensor enriches process/network events with the      |
|                               | model's verdict as a risk score.                              |
| **Cloud security platform**   | A serverless function (Lambda/Cloud Run) loads this joblib,    |
|                               | ingests VPC flow + CloudTrail, tags anomalies.                |
| **SOAR playbook**             | The classifier's output triggers automated containment        |
|                               | (isolate host, block IP, rotate creds).                       |

See `docs/14_Future_Work.md` for the full deployment discussion.

## Reproducibility

To retrain from scratch:
```bash
cd Computer-2-Analysis
make all-models    # ingest → features → train → evaluate → stats
```

The artifacts in this folder are regenerated on every training run. The
specific `<name>` in `best_model_<name>.joblib` is the model with the
highest test F1 macro on the current dataset.
