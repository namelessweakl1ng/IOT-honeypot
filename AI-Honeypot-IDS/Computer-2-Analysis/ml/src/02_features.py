"""
Computer 2 — ML pipeline — 02_features.py
=========================================
Reads data/raw.parquet, cleans, engineers features, encodes categoricals,
scales numerics, writes data/features.parquet.

The output has columns:
    [all numeric features] + [one-hot categorical features] + label + label_id

This is the file 03_train.py consumes.
"""
from __future__ import annotations
import sys, re
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config  # noqa: E402

# ---------------------------------------------------------------------------
# Heuristic keyword lists for feature flags
# ---------------------------------------------------------------------------
SQL_KEYWORDS = re.compile(
    r"\b(union|select|insert|update|delete|drop|or 1=1|information_schema|sleep\(|benchmark\(|--|;)\b",
    re.I,
)
CMD_KEYWORDS = re.compile(r"(\$?\(|`|;|\||&&|\|\||/bin/sh|/bin/bash|cat |wget |curl |nc |/etc/passwd)", re.I)
XSS_KEYWORDS = re.compile(r"(<script|onerror=|javascript:|<img src=x|<svg|alert\()", re.I)
TRAVERSAL_KEYWORDS = re.compile(r"(\.\./|\.\.\\|%2e%2e|/etc/passwd|/etc/shadow|c:\\windows)", re.I)


def _safe_len(x) -> int:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 0
    return len(str(x))


def _digit_ratio(s) -> float:
    s = str(s or "")
    if not s:
        return 0.0
    digits = sum(c.isdigit() for c in s)
    return digits / len(s)


def _upper_ratio(s) -> float:
    s = str(s or "")
    if not s:
        return 0.0
    up = sum(c.isupper() for c in s)
    return up / len(s)


def _special_chars(s) -> int:
    s = str(s or "")
    return sum(1 for c in s if not c.isalnum() and c != " ")


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    print(f"[features] input shape: {df.shape}")

    # ---- 1. Coerce / fill NA ------------------------------------------------
    for col in ["src_port", "dst_port", "response_code"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    for col in ["username", "password", "payload", "path", "query", "user_agent"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    if "auth_success" in df.columns:
        df["auth_success"] = df["auth_success"].astype(str).str.lower().isin(["true", "1", "yes"])
    else:
        df["auth_success"] = False

    # ---- 2. Timestamp features ----------------------------------------------
    if "@timestamp" in df.columns:
        ts = pd.to_datetime(df["@timestamp"], errors="coerce", utc=True)
        df["hour_of_day"] = ts.dt.hour.fillna(0).astype(int)
        df["day_of_week"] = ts.dt.dayofweek.fillna(0).astype(int)
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    else:
        df["hour_of_day"] = 0
        df["day_of_week"] = 0
        df["is_weekend"] = 0

    # ---- 3. Length features --------------------------------------------------
    df["payload_len"] = df["payload"].apply(_safe_len)
    df["path_len"] = df["path"].apply(_safe_len)
    df["query_len"] = df["query"].apply(_safe_len)
    df["username_len"] = df["username"].apply(_safe_len)
    df["password_len"] = df["password"].apply(_safe_len)
    df["ua_len"] = df["user_agent"].apply(_safe_len)

    # ---- 4. Auth flags -------------------------------------------------------
    df["auth_attempt"] = df["username"].apply(lambda x: 1 if x and x != "" else 0).astype(int)
    df["auth_success_int"] = df["auth_success"].astype(int)

    # ---- 5. Payload composition ---------------------------------------------
    df["special_chars_payload"] = df["payload"].apply(_special_chars).astype(int)
    df["digit_ratio_payload"] = df["payload"].apply(_digit_ratio)
    df["uppercase_ratio_payload"] = df["payload"].apply(_upper_ratio)

    # ---- 6. Signature flags --------------------------------------------------
    df["has_sql_keywords"] = df["payload"].apply(lambda x: 1 if SQL_KEYWORDS.search(x) else 0).astype(int)
    df["has_cmd_keywords"] = df["payload"].apply(lambda x: 1 if CMD_KEYWORDS.search(x) else 0).astype(int)
    df["has_xss_keywords"] = df["payload"].apply(lambda x: 1 if XSS_KEYWORDS.search(x) else 0).astype(int)
    df["has_traversal_keywords"] = df["payload"].apply(lambda x: 1 if TRAVERSAL_KEYWORDS.search(x) else 0).astype(int)

    # ---- 7. Categorical features --------------------------------------------
    for col in ["container_service", "protocol", "method"]:
        if col not in df.columns:
            df[col] = "unknown"
        df[col] = df[col].fillna("unknown").astype(str)
    if "geo_country" not in df.columns:
        # try geo.country_name
        if "geo_country_name" in df.columns:
            df["geo_country"] = df["geo_country_name"]
        else:
            df["geo_country"] = "unknown"
    df["geo_country"] = df["geo_country"].fillna("unknown").astype(str)

    # ---- 8. Label ------------------------------------------------------------
    if "attack_class" not in df.columns:
        # Fall back to attack_type_hint → attack_class mapping (same as Logstash)
        mapping = {
            "benign": "benign", "login_success": "benign", "ftp_login_success": "benign",
            "recon": "recon", "directory_enum": "recon", "ftp_connect": "recon",
            "telnet_connect": "recon", "telnet_error": "recon", "ssh_protocol_error": "recon",
            "sql_injection": "sqli",
            "command_injection": "cmdi", "ssh_command_injection": "cmdi",
            "ssh_command_exec": "cmdi", "telnet_command_exec": "cmdi",
            "xss": "xss",
            "path_traversal": "traversal",
            "brute_force_login": "bruteforce", "ssh_brute_force": "bruteforce",
            "ftp_brute_force": "bruteforce", "telnet_brute_force": "bruteforce",
            "ssh_key_attempt": "bruteforce",
            "ftp_retr": "exfil",
            "ftp_stor": "implant", "file_upload": "implant",
            "ssrf": "ssrf",
            "printer_abuse": "abuse",
        }
        df["attack_class"] = df.get("attack_type_hint", pd.Series(["benign"] * len(df))) \
            .fillna("benign").map(mapping).fillna("unknown")

    # Drop rows with unknown labels (very rare; Logstash mapping covers all)
    df = df[df["attack_class"].isin(config.LABELS)].reset_index(drop=True)

    df["label"] = df["attack_class"]
    df["label_id"] = df["label"].map(config.LABEL_TO_ID)

    # ---- 9. One-hot encode categoricals -------------------------------------
    df_enc = pd.get_dummies(df[config.CATEGORICAL_FEATURES], prefix="cat", dummy_na=False)

    # ---- 10. Scale numerics --------------------------------------------------
    num = df[config.NUMERIC_FEATURES].fillna(0).astype(float)
    scaler = StandardScaler()
    num_scaled = pd.DataFrame(scaler.fit_transform(num), columns=config.NUMERIC_FEATURES)

    # ---- 11. Combine ---------------------------------------------------------
    out = pd.concat([num_scaled, df_enc, df[["label", "label_id"]]], axis=1)
    print(f"[features] output shape: {out.shape}")
    print(f"[features] label distribution:")
    print(out["label"].value_counts())
    out.to_parquet(config.FEATURES_PARQUET, index=False)
    print(f"[features] wrote {config.FEATURES_PARQUET}")

    # Persist the scaler for inference-time use
    import joblib
    joblib.dump(scaler, config.MODELS_DIR / "scaler.joblib")
    print(f"[features] wrote scaler to {config.MODELS_DIR / 'scaler.joblib'}")

    # Persist the one-hot column list (needed at inference time)
    (config.MODELS_DIR / "feature_columns.json").write_text(
        out.drop(columns=["label", "label_id"]).columns.to_json()
    )
    print(f"[features] wrote feature_columns.json")
    return out


if __name__ == "__main__":
    if not config.RAW_PARQUET.exists():
        print("[features][FATAL] raw.parquet missing. Run 01_ingest.py first.")
        sys.exit(2)
    df = pd.read_parquet(config.RAW_PARQUET)
    build_features(df)
