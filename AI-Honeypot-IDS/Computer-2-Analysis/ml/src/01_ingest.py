"""
Computer 2 — ML pipeline — 01_ingest.py
=======================================
Pulls all honeypot log events from Elasticsearch into a local Parquet file
(data/raw.parquet). This decouples the ML pipeline from the live SIEM so
training can be re-run offline.

Usage:
    python src/01_ingest.py
    python src/01_ingest.py --days 7      # only last 7 days
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path
import pandas as pd
from elasticsearch import Elasticsearch
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="Ingest honeypot logs from Elasticsearch")
    p.add_argument("--days", type=int, default=0,
                   help="Only ingest last N days (0 = all)")
    p.add_argument("--index", default=config.ES_INDEX_PATTERN)
    return p.parse_args()


def main():
    args = parse_args()
    print(f"[ingest] connecting to {config.ES_HOST}")
    es = Elasticsearch(config.ES_HOST, request_timeout=60)
    if not es.ping():
        print("[ingest][FATAL] cannot reach Elasticsearch")
        sys.exit(2)

    body: dict = {"query": {"match_all": {}}, "sort": [{"@timestamp": "asc"}]}
    if args.days > 0:
        body["query"] = {"range": {"@timestamp": {"gte": f"now-{args.days}d/d"}}}

    # Count first
    cnt = es.count(index=args.index, body={"query": body["query"]})["count"]
    print(f"[ingest] {cnt} events in {args.index}")

    if cnt == 0:
        print("[ingest][WARN] no events found. Did you run attacks yet?")
        # Write an empty parquet so downstream scripts don't crash
        pd.DataFrame().to_parquet(config.RAW_PARQUET, index=False)
        return

    # Scroll
    rows = []
    resp = es.search(index=args.index, body=body, size=config.ES_SCROLL_SIZE,
                     scroll=config.ES_SCROLL_TIME)
    sid = resp["_scroll_id"]
    hits = resp["hits"]["hits"]
    with tqdm(total=cnt, unit="ev", desc="ingest") as pbar:
        while hits:
            for h in hits:
                rows.append(h["_source"])
            pbar.update(len(hits))
            resp = es.scroll(scroll_id=sid, scroll=config.ES_SCROLL_TIME)
            sid = resp["_scroll_id"]
            hits = resp["hits"]["hits"]
    try:
        es.clear_scroll(scroll_id=sid)
    except Exception:  # noqa: BLE001
        pass

    df = pd.DataFrame(rows)
    # Normalize nested geo
    if "geo" in df.columns:
        geo_df = pd.json_normalize(df["geo"].apply(lambda x: x if isinstance(x, dict) else {}))
        geo_df.columns = [f"geo_{c}" for c in geo_df.columns]
        df = pd.concat([df.drop(columns=["geo"]), geo_df], axis=1)

    print(f"[ingest] dataframe shape: {df.shape}")
    print(f"[ingest] columns: {list(df.columns)}")
    print(f"[ingest] attack_class distribution:")
    if "attack_class" in df.columns:
        print(df["attack_class"].value_counts())

    df.to_parquet(config.RAW_PARQUET, index=False)
    print(f"[ingest] wrote {config.RAW_PARQUET}")
    # Also copy the labeled subset to the global datasets/ folder for sharing
    if "attack_class" in df.columns and "payload" in df.columns:
        export_cols = [c for c in [
            "@timestamp", "container_name", "container_service", "src_ip",
            "src_port", "dst_port", "protocol", "method", "path", "query",
            "username", "password", "payload", "user_agent", "attack_type_hint",
            "attack_class", "response_code", "auth_success"
        ] if c in df.columns]
        df[export_cols].to_csv(config.DATASET_CSV, index=False)
        print(f"[ingest] wrote {config.DATASET_CSV}")


if __name__ == "__main__":
    main()
