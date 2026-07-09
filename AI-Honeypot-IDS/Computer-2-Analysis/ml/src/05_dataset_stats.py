"""
Computer 2 — ML pipeline — 05_dataset_stats.py
Quick EDA: prints dataset shape, class balance, per-container counts, and
writes reports/dataset_stats.md (used in the project report).
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402


def main():
    if not config.RAW_PARQUET.exists():
        print("[stats][FATAL] raw.parquet missing.")
        sys.exit(2)
    df = pd.read_parquet(config.RAW_PARQUET)
    md = []
    md.append("# Dataset statistics\n")
    md.append(f"- Total events: **{len(df)}**\n")
    md.append(f"- Columns: {len(df.columns)}\n")
    md.append(f"- Time range: {df.get('@timestamp', pd.Series()).min()} → {df.get('@timestamp', pd.Series()).max()}\n")
    if "attack_class" in df.columns:
        md.append("\n## Class distribution\n")
        vc = df["attack_class"].value_counts()
        for k, v in vc.items():
            md.append(f"- {k}: {v} ({v/len(df)*100:.1f}%)")
    if "container_name" in df.columns:
        md.append("\n## Per-container event counts\n")
        vc = df["container_name"].value_counts()
        for k, v in vc.items():
            md.append(f"- {k}: {v}")
    if "src_ip" in df.columns:
        md.append("\n## Top 10 source IPs\n")
        vc = df["src_ip"].value_counts().head(10)
        for k, v in vc.items():
            md.append(f"- {k}: {v}")
    out = config.REPORTS_DIR / "dataset_stats.md"
    out.write_text("\n".join(md))
    print(f"[stats] wrote {out}")
    print("\n".join(md))


if __name__ == "__main__":
    main()
