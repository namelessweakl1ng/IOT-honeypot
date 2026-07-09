# Honeypot ML pipeline

This folder contains the Python pipeline that turns honeypot logs into a
trained IDS classifier.

## Layout
```
ml/
├── requirements.txt
├── src/
│   ├── config.py            ← paths, labels, model specs (edit here)
│   ├── 01_ingest.py         ← pull logs from Elasticsearch → data/raw.parquet
│   ├── 02_features.py       ← feature engineering + scaling → data/features.parquet
│   ├── 03_train.py          ← train all 6 models, CV, save artifacts
│   ├── 04_evaluate.py       ← confusion matrix, ROC, comparison → reports/
│   └── 05_dataset_stats.py  ← EDA summary → reports/dataset_stats.md
├── data/                    ← raw.parquet, features.parquet (gitignored)
├── models/                  ← *.joblib (scaler + per-model)
├── reports/                 ← metrics, plots, comparison table
└── notebooks/               ← exploratory Jupyter notebooks (optional)
```

## Run
```bash
source ~/.venvs/honeypot-ml/bin/activate
cd Computer-2-Analysis/ml
python src/01_ingest.py
python src/02_features.py
python src/03_train.py
python src/04_evaluate.py
python src/05_dataset_stats.py
```

## Models trained (see config.py)
| Name           | Class                              | Notes                       |
|----------------|------------------------------------|-----------------------------|
| logreg         | LogisticRegression                 | linear baseline             |
| decision_tree  | DecisionTreeClassifier             | interpretable               |
| random_forest  | RandomForestClassifier             | strong tabular baseline     |
| svm            | SVC (RBF, probability=True)        | slower, good on small data  |
| xgboost        | XGBClassifier                      | boosting, often best        |
| lightgbm       | LGBMClassifier                     | boosting, fast              |

## Labels (config.LABELS)
`benign, recon, sqli, cmdi, xss, traversal, bruteforce, exfil, implant, ssrf, abuse`

## ⚠️ The model is NOT deployed in this project
This pipeline **trains and saves** a classifier. It is not wired into live
detection. See `docs/14_Future_Work.md` and the README inside `trained_models/`
for how the saved artifacts would be loaded by a SIEM, firewall, EDR, or cloud
security product.
