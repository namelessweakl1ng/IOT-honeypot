# Models folder (gitignored unless artifacts are released)

Saved model artifacts produced by `03_train.py`:

- `scaler.joblib` — StandardScaler fitted on training numerics
- `feature_columns.json` — exact feature column order
- `logreg.joblib`, `decision_tree.joblib`, `random_forest.joblib`,
  `svm.joblib`, `xgboost.joblib`, `lightgbm.joblib`

The **best** model is also copied to the project-root `trained_models/` folder
for handover to evaluators.
