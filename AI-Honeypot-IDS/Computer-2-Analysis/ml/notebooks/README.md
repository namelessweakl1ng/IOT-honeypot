# Exploratory notebooks

Optional Jupyter notebooks for live exploration during the viva.

- `01_eda.ipynb` — load `data/raw.parquet`, show class balance, per-container
  counts, sample payloads per attack class.
- `02_model_debug.ipynb` — load a saved model, show feature importances,
  inspect mis-classified examples.

To run:
```
source ~/.venvs/honeypot-ml/bin/activate
pip install jupyterlab
jupyter lab
```
