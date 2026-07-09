# 10 — Model Training

## 10.1 Pipeline overview

```
data/raw.parquet
   │ 02_features.py
   ▼
data/features.parquet  +  models/scaler.joblib  +  models/feature_columns.json
   │ 03_train.py
   ▼
models/{logreg,decision_tree,random_forest,svm,xgboost,lightgbm}.joblib
   │ 04_evaluate.py
   ▼
reports/{summary.json, model_comparison.csv, confusion_matrix_*.png, roc_curve_*.png}
   │
   ▼
trained_models/{best_model_*.joblib, scaler.joblib, feature_columns.json, labels.json}
```

## 10.2 Feature engineering (`02_features.py`)

### Numeric features (20)
| Feature                       | Source              | Notes                          |
|-------------------------------|---------------------|--------------------------------|
| `src_port`                    | log                 | client ephemeral port          |
| `dst_port`                    | log                 | honeypot port                  |
| `response_code`               | log                 | HTTP status / proto return     |
| `payload_len`                 | derived             | len(payload)                   |
| `path_len`                    | derived             | len(path)                      |
| `query_len`                   | derived             | len(query)                     |
| `username_len`                | derived             | len(username)                  |
| `password_len`                | derived             | len(password)                  |
| `ua_len`                      | derived             | len(user_agent)                |
| `hour_of_day`                 | @timestamp          | 0–23                           |
| `day_of_week`                 | @timestamp          | 0–6                            |
| `is_weekend`                  | day_of_week         | 1 if Sat/Sun                   |
| `auth_attempt`                | username != ""      | 0/1                            |
| `auth_success_int`            | auth_success        | 0/1                            |
| `special_chars_payload`       | payload             | count of non-alnum, non-space  |
| `digit_ratio_payload`         | payload             | digits / len                   |
| `uppercase_ratio_payload`     | payload             | uppercase / len                |
| `has_sql_keywords`            | payload regex       | 0/1                            |
| `has_cmd_keywords`            | payload regex       | 0/1                            |
| `has_xss_keywords`            | payload regex       | 0/1                            |
| `has_traversal_keywords`      | payload regex       | 0/1                            |

### Categorical features (4, one-hot encoded)
- `container_service`
- `protocol`
- `method`
- `geo_country`

### Scaling
`StandardScaler` is fitted on the training numerics and saved as
`models/scaler.joblib`. At inference time the same scaler is loaded —
**never** refit on new data.

### One-hot encoding
`pd.get_dummies` produces N boolean columns per categorical. The exact
column order is saved to `models/feature_columns.json` so inference can
reindex missing columns to 0.

## 10.3 Train/test split

- 80/20 stratified split (`random_state=42`).
- Stratification ensures every class is represented in both sets in proportion.

## 10.4 Cross-validation

- 5-fold stratified (`StratifiedKFold`, shuffle=True, random_state=42).
- Metrics: accuracy, F1 macro, F1 weighted.
- Run on the **train** set only; the test set is held out for final
  evaluation.

## 10.5 The six models (`config.MODELS`)

| Name           | Class                              | Why included                       |
|----------------|------------------------------------|------------------------------------|
| logreg         | LogisticRegression                 | Linear baseline                    |
| decision_tree  | DecisionTreeClassifier             | Interpretable, single tree         |
| random_forest  | RandomForestClassifier             | Strong tabular baseline            |
| svm            | SVC (RBF, probability=True)        | Kernel method, different bias      |
| xgboost        | XGBClassifier                      | Gradient boosting, often best      |
| lightgbm       | LGBMClassifier                     | Gradient boosting, fast            |

All use `class_weight="balanced"` (where supported) to counter class
imbalance.

## 10.6 Hyperparameters

Defaults in `config.py`:

| Model          | Key hyperparameters                                  |
|----------------|------------------------------------------------------|
| logreg         | `max_iter=1000`                                      |
| decision_tree  | `max_depth=12`                                       |
| random_forest  | `n_estimators=200, max_depth=16`                     |
| svm            | `kernel=rbf, C=1.0, probability=True`                |
| xgboost        | `n_estimators=300, max_depth=8, learning_rate=0.1`   |
| lightgbm       | `n_estimators=300, num_leaves=63, learning_rate=0.1` |

For a more rigorous model selection, wrap each model in `GridSearchCV` or
`OptunaSearchCV`. We keep the grid small for lab-time tractability.

## 10.7 Training run (`03_train.py`)

For each model:
1. Cross-validate on the train set (5 folds).
2. Refit on the full train set.
3. Predict on the test set.
4. Save the model to `models/<name>.joblib`.
5. Record CV + test metrics.

Outputs:
- `reports/cv_metrics.json`
- `reports/best_model.txt`

## 10.8 Evaluation (`04_evaluate.py`)

For each model:
- Accuracy, macro precision/recall/F1, weighted F1.
- Confusion matrix PNG.
- Per-class classification report JSON.

For the best model only:
- OvR micro-averaged ROC curve PNG (requires `predict_proba`).

Outputs:
- `reports/summary.json`
- `reports/model_comparison.csv`
- `reports/confusion_matrix_<name>.png`
- `reports/roc_curve_<name>.png`
- `reports/classification_report_<name>.json`

## 10.9 Choosing the best model

The best model is the one with the highest **test F1 macro**. We use macro
(not weighted) F1 because:
- Macro averages each class equally → punishes models that ignore minorities.
- Weighted is dominated by the majority class → hides poor minority
  performance.

Typical lab result: Random Forest and XGBoost tie at ~0.98 F1 macro. The
pipeline picks whichever is higher; both are saved.

## 10.10 Model artifacts (`trained_models/`)

After `04_evaluate.py`:
- `best_model_<name>.joblib` — the winning classifier.
- `scaler.joblib` — the StandardScaler.
- `feature_columns.json` — exact feature column order.
- `labels.json` — label string ↔ integer mapping.
- `README.md` — loading + inference example, deployment paths.

## 10.11 ⚠️ The model is NOT deployed

Repeating the project's central design choice: the trained model is saved as
a deployable artifact but is **NOT** wired into live detection. Reasons:

1. The academic objective is the methodology, not a production system.
2. An inline classifier would change the honeypot's behavior (blocking
   attacks would defeat the data-collection purpose).
3. Deployment is a separate engineering project with its own latency,
   safety, and rollback requirements.

The `trained_models/README.md` documents exactly how a downstream system
(SIEM, firewall, EDR, cloud) would load and use the artifacts. See
`14_Future_Work.md` for the full deployment discussion.

## 10.12 Reproducibility

To retrain from scratch:
```bash
cd Computer-2-Analysis
make all-models
```

This runs ingest → features → train → evaluate → stats. Total wall-clock on
the reference hardware: 3–5 minutes for a 2k-row dataset.
