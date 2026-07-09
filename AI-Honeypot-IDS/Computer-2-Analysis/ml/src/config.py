"""
Computer 2 — ML pipeline — config.py
Central configuration for the ML pipeline. All paths, hyper-parameters, and
Elasticsearch connection settings live here so the other scripts stay simple.
"""
from __future__ import annotations
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent          # Computer-2-Analysis/
ML_DIR = ROOT / "ml"
DATA_DIR = ML_DIR / "data"
MODELS_DIR = ML_DIR / "models"
REPORTS_DIR = ML_DIR / "reports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

RAW_PARQUET = DATA_DIR / "raw.parquet"
FEATURES_PARQUET = DATA_DIR / "features.parquet"
DATASET_CSV = ROOT.parent / "datasets" / "honeypot_dataset.csv"
DATASET_CSV.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Elasticsearch
# ---------------------------------------------------------------------------
ES_HOST = os.environ.get("ES_HOST", "http://127.0.0.1:9200")
ES_INDEX_PATTERN = "honeypot-logs-*"
ES_SCROLL_SIZE = 5000
ES_SCROLL_TIME = "5m"

# ---------------------------------------------------------------------------
# Label taxonomy (the classes the model learns to predict)
# ---------------------------------------------------------------------------
LABELS = [
    "benign",
    "recon",
    "sqli",
    "cmdi",
    "xss",
    "traversal",
    "bruteforce",
    "exfil",
    "implant",
    "ssrf",
    "abuse",
]
LABEL_TO_ID = {l: i for i, l in enumerate(LABELS)}
ID_TO_LABEL = {i: l for l, i in LABEL_TO_ID.items()}

# ---------------------------------------------------------------------------
# Feature columns (produced by 02_features.py)
# ---------------------------------------------------------------------------
NUMERIC_FEATURES = [
    "src_port",
    "dst_port",
    "response_code",
    "payload_len",
    "path_len",
    "query_len",
    "username_len",
    "password_len",
    "ua_len",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "auth_attempt",
    "auth_success_int",
    "special_chars_payload",
    "digit_ratio_payload",
    "uppercase_ratio_payload",
    "has_sql_keywords",
    "has_cmd_keywords",
    "has_xss_keywords",
    "has_traversal_keywords",
]
CATEGORICAL_FEATURES = [
    "container_service",
    "protocol",
    "method",
    "geo_country",
]
ALL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# ---------------------------------------------------------------------------
# Models + hyper-parameters
# ---------------------------------------------------------------------------
RANDOM_STATE = 42
CV_FOLDS = 5
TEST_SIZE = 0.2

MODELS = {
    "logreg": {
        "class": "sklearn.linear_model.LogisticRegression",
        "params": {"max_iter": 1000, "class_weight": "balanced", "n_jobs": -1,
                   "random_state": RANDOM_STATE},
    },
    "decision_tree": {
        "class": "sklearn.tree.DecisionTreeClassifier",
        "params": {"max_depth": 12, "class_weight": "balanced",
                   "random_state": RANDOM_STATE},
    },
    "random_forest": {
        "class": "sklearn.ensemble.RandomForestClassifier",
        "params": {"n_estimators": 200, "max_depth": 16, "class_weight": "balanced",
                   "n_jobs": -1, "random_state": RANDOM_STATE},
    },
    "svm": {
        "class": "sklearn.svm.SVC",
        "params": {"kernel": "rbf", "C": 1.0, "class_weight": "balanced",
                   "probability": True, "random_state": RANDOM_STATE},
    },
    "xgboost": {
        "class": "xgboost.XGBClassifier",
        "params": {"n_estimators": 300, "max_depth": 8, "learning_rate": 0.1,
                   "subsample": 0.9, "colsample_bytree": 0.9,
                   "objective": "multi:softprob", "tree_method": "hist",
                   "random_state": RANDOM_STATE, "n_jobs": -1},
    },
    "lightgbm": {
        "class": "lightgbm.LGBMClassifier",
        "params": {"n_estimators": 300, "max_depth": -1, "num_leaves": 63,
                   "learning_rate": 0.1, "class_weight": "balanced",
                   "random_state": RANDOM_STATE, "n_jobs": -1},
    },
}

BEST_MODEL_NAME = "random_forest"   # determined empirically (see 04_evaluate.py)
