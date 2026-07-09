"""
Computer 2 — ML pipeline — 04_evaluate.py
=========================================
For each trained model:
  - compute test-set predictions
  - save confusion matrix PNG
  - save per-class classification report (JSON + CSV)
  - save ROC curve (one-vs-rest micro-average) PNG for the BEST model
  - write reports/summary.json
Also copies the best model + scaler into trained_models/ (root) for handover.
"""
from __future__ import annotations
import sys, json, shutil
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    confusion_matrix, classification_report, accuracy_score,
    f1_score, precision_score, recall_score, roc_curve, auc,
)
from sklearn.preprocessing import label_binarize
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

ROOT_TRAINED = config.ROOT.parent / "trained_models"
ROOT_TRAINED.mkdir(parents=True, exist_ok=True)


def plot_confusion(cm: np.ndarray, labels, title: str, out: Path):
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def plot_roc(y_true, y_proba, labels, title: str, out: Path):
    # micro-average OvR ROC
    y_bin = label_binarize(y_true, classes=list(range(len(labels))))
    fpr, tpr, _ = roc_curve(y_bin.ravel(), y_proba.ravel())
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(fpr, tpr, label=f"micro-avg (AUC={roc_auc:.3f})", lw=2)
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(title)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)
    return roc_auc


def main():
    if not config.FEATURES_PARQUET.exists():
        print("[eval][FATAL] features.parquet missing.")
        sys.exit(2)

    df = pd.read_parquet(config.FEATURES_PARQUET)
    y = df["label_id"].values
    X = df.drop(columns=["label", "label_id"]).values
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=config.TEST_SIZE, stratify=y, random_state=config.RANDOM_STATE
    )

    cv_metrics = json.loads((config.REPORTS_DIR / "cv_metrics.json").read_text())
    best_name = (config.REPORTS_DIR / "best_model.txt").read_text().strip()
    print(f"[eval] best model = {best_name}")

    summary = {}
    for name in config.MODELS:
        model_path = config.MODELS_DIR / f"{name}.joblib"
        if not model_path.exists():
            print(f"[eval][WARN] {model_path} missing, skipping")
            continue
        print(f"\n=== Evaluating {name} ===")
        model = joblib.load(model_path)
        y_pred = model.predict(X_te)
        acc = accuracy_score(y_te, y_pred)
        f1m = f1_score(y_te, y_pred, average="macro", zero_division=0)
        f1w = f1_score(y_te, y_pred, average="weighted", zero_division=0)
        prec = precision_score(y_te, y_pred, average="macro", zero_division=0)
        rec = recall_score(y_te, y_pred, average="macro", zero_division=0)

        cm = confusion_matrix(y_te, y_pred, labels=list(range(len(config.LABELS))))
        plot_confusion(cm, config.LABELS, f"Confusion Matrix — {name}",
                       config.REPORTS_DIR / f"confusion_matrix_{name}.png")
        report = classification_report(y_te, y_pred,
                                       target_names=config.LABELS,
                                       output_dict=True, zero_division=0)
        (config.REPORTS_DIR / f"classification_report_{name}.json").write_text(
            json.dumps(report, indent=2)
        )

        summary[name] = {
            "accuracy": float(acc),
            "precision_macro": float(prec),
            "recall_macro": float(rec),
            "f1_macro": float(f1m),
            "f1_weighted": float(f1w),
            "confusion_matrix": cm.tolist(),
            "per_class": report,
        }
        print(f"  acc={acc:.4f}  prec={prec:.4f}  rec={rec:.4f}  f1m={f1m:.4f}  f1w={f1w:.4f}")

        # ROC curve for the BEST model only (probability-intensive)
        if name == best_name and hasattr(model, "predict_proba"):
            y_proba = model.predict_proba(X_te)
            auc_val = plot_roc(y_te, y_proba, config.LABELS,
                               f"ROC (OvR micro-avg) — {name}",
                               config.REPORTS_DIR / f"roc_curve_{name}.png")
            summary[name]["roc_auc_micro"] = float(auc_val)
            print(f"  roc_auc_micro={auc_val:.4f}")

    (config.REPORTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    # Also a friendly comparison table
    comp = pd.DataFrame([
        {"model": n, **{k: v for k, v in d.items() if k in ["accuracy", "precision_macro", "recall_macro", "f1_macro", "f1_weighted"]}}
        for n, d in summary.items()
    ]).sort_values("f1_macro", ascending=False)
    comp.to_csv(config.REPORTS_DIR / "model_comparison.csv", index=False)
    print("\n[eval] Model comparison:")
    print(comp.to_string(index=False))

    # Copy best model + scaler to root trained_models/
    print(f"\n[eval] copying best model '{best_name}' to {ROOT_TRAINED}")
    shutil.copy2(config.MODELS_DIR / f"{best_name}.joblib", ROOT_TRAINED / f"best_model_{best_name}.joblib")
    shutil.copy2(config.MODELS_DIR / "scaler.joblib", ROOT_TRAINED / "scaler.joblib")
    shutil.copy2(config.MODELS_DIR / "feature_columns.json", ROOT_TRAINED / "feature_columns.json")
    (ROOT_TRAINED / "labels.json").write_text(json.dumps(config.LABELS, indent=2))
    (ROOT_TRAINED / "README.md").write_text(README_TRAINED_MODELS.format(best=best_name))
    print("[eval] done.")


README_TRAINED_MODELS = """# Trained models

This folder contains the saved artifacts from the ML pipeline.

## Files
- `best_model_{best}.joblib` — the best-performing classifier (joblib-serialized)
- `scaler.joblib` — the StandardScaler fitted on the training data
- `feature_columns.json` — the exact feature column order expected by the model
- `labels.json` — the label string ↔ integer id mapping

## How to load and use for inference (NOT part of this project — illustration only)

```python
import joblib, json, pandas as pd
model = joblib.load("best_model_{best}.joblib")
scaler = joblib.load("scaler.joblib")
feature_cols = json.loads(open("feature_columns.json").read())
labels = json.loads(open("labels.json").read())

# Suppose `event` is a dict from your SIEM with the same fields as the
# honeypot logs. Build the same feature vector:
#   1. Engineer the same numeric features (lengths, ratios, signature flags, …)
#   2. One-hot encode the same categoricals
#   3. Reindex to feature_cols (filling missing with 0)
#   4. Scale numerics with the loaded scaler
#   5. model.predict_proba(X) → class probabilities
#   6. argmax → label_id → labels[id]
```

## Where this could be deployed
- Inside Logstash as a ruby-filter that calls a small inference microservice
- In a SIEM (Splunk / Elastic / Wazuh) as a custom alerting rule
- On a firewall / IDS as an inline classifier
- In an EDR / XDR product as an enrichment module
- In a cloud security platform as a serverless inference function

See docs/14_Future_Work.md for the full deployment discussion.
"""

if __name__ == "__main__":
    main()
