# Data folder (gitignored)

This folder holds the working datasets produced by the ML pipeline:

- `raw.parquet` — raw events pulled from Elasticsearch by `01_ingest.py`
- `features.parquet` — engineered feature matrix from `02_features.py`

These files are NOT committed (they can be large and they contain IP
addresses from the lab). They are regenerated on demand.

A **canonical labeled CSV export** is written to the project root
`datasets/honeypot_dataset.csv` by `01_ingest.py` for sharing with evaluators.
