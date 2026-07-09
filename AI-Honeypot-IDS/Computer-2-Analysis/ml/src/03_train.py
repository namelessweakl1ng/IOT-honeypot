"""
Computer 2 — ML pipeline — 03_train.py
======================================
Trains all 6 models on data/features.parquet with stratified k-fold
cross-validation. Saves each model to models/<name>.joblib. Prints CV metrics.
"""
from __future__ import annotations
import sys, json, importlib, time
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.metrics import classification_report, accuracy_score, f1_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402


def instantiate_model(spec: dict):
    cls_path = spec["class"]
    module_name, cls_name = cls_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    cls = getattr(module, cls_name)
    return cls(**spec["params"])


def main():
    if not config.FEATURES_PARQUET.exists():
        print("[train][FATAL] features.parquet missing. Run 02_features.py first.")
        sys.exit(2)

    df = pd.read_parquet(config.FEATURES_PARQUET)
    y = df["label_id"].values
    X = df.drop(columns=["label", "label_id"]).values

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=config.TEST_SIZE, stratify=y, random_state=config.RANDOM_STATE
    )
    print(f"[train] train={X_tr.shape} test={X_te.shape} classes={len(config.LABELS)}")

    skf = StratifiedKFold(n_splits=config.CV_FOLDS, shuffle=True,
                          random_state=config.RANDOM_STATE)

    results = {}
    for name, spec in config.MODELS.items():
        print(f"\n=== Training {name} ===")
        model = instantiate_model(spec)
        t0 = time.time()
        # Cross-validation on train set
        cv_res = cross_validate(
            model, X_tr, y_tr, cv=skf, scoring=["accuracy", "f1_macro", "f1_weighted"],
            n_jobs=-1, return_train_score=False
        )
        cv_time = time.time() - t0
        cv_acc = float(np.mean(cv_res["test_accuracy"]))
        cv_f1_macro = float(np.mean(cv_res["test_f1_macro"]))
        cv_f1_weighted = float(np.mean(cv_res["test_f1_weighted"]))

        # Refit on full train, evaluate on held-out test
        model.fit(X_tr, y_tr)
        y_pred = model.predict(X_te)
        test_acc = float(accuracy_score(y_te, y_pred))
        test_f1_macro = float(f1_score(y_te, y_pred, average="macro", zero_division=0))
        test_f1_weighted = float(f1_score(y_te, y_pred, average="weighted", zero_division=0))

        results[name] = {
            "cv_accuracy": cv_acc,
            "cv_f1_macro": cv_f1_macro,
            "cv_f1_weighted": cv_f1_weighted,
            "cv_time_sec": cv_time,
            "test_accuracy": test_acc,
            "test_f1_macro": test_f1_macro,
            "test_f1_weighted": test_f1_weighted,
            "params": spec["params"],
            "class": spec["class"],
        }

        # Save the model
        out_path = config.MODELS_DIR / f"{name}.joblib"
        joblib.dump(model, out_path)
        print(f"  CV  acc={cv_acc:.4f}  f1_macro={cv_f1_macro:.4f}  f1_w={cv_f1_weighted:.4f}  ({cv_time:.1f}s)")
        print(f"  TEST acc={test_acc:.4f}  f1_macro={test_f1_macro:.4f}  f1_w={test_f1_weighted:.4f}")
        print(f"  saved {out_path}")

    # Save consolidated metrics
    metrics_path = config.REPORTS_DIR / "cv_metrics.json"
    metrics_path.write_text(json.dumps(results, indent=2))
    print(f"\n[train] wrote {metrics_path}")

    # Choose best model by test F1 macro
    best = max(results.items(), key=lambda kv: kv[1]["test_f1_macro"])
    print(f"\n[train] BEST model: {best[0]} (test_f1_macro={best[1]['test_f1_macro']:.4f})")
    (config.REPORTS_DIR / "best_model.txt").write_text(best[0])


if __name__ == "__main__":
    main()
