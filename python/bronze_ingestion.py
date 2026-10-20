from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "data" / "bronze"
OUTPUT_DIR = ROOT / "data" / "processed_bronze"

# Adjusted to match the exact schemas of the CSVs created in Day 4
DATASETS = {
    "customers": {
        "file": "customers.csv",
        "primary_key": "customer_id",
        "required_columns": ["customer_id", "name", "email", "city", "status", "created_at"],
    },
    "orders": {
        "file": "orders.csv",
        "primary_key": "order_id",
        "required_columns": ["order_id", "customer_id", "order_time", "amount"],
    },
    "payments": {
        "file": "payments.csv",
        "primary_key": "payment_id",
        "required_columns": ["payment_id", "order_id", "payment_time", "paid_amount"],
    },
    "refunds": {
        "file": "refunds.csv",
        "primary_key": "refund_id",
        "required_columns": ["refund_id", "order_id", "refund_time", "refund_amount"],
    },
    "website_events": {
        "file": "website_events.csv",
        "primary_key": "event_id",
        "required_columns": ["event_id", "customer_id", "event_time", "event_type"],
    },
}

def ingest_dataset(dataset_name, config):
    source_path = INPUT_DIR / config["file"]
    if not source_path.exists():
        raise FileNotFoundError(f"Missing source file: {source_path}")

    df = pd.read_csv(source_path, dtype=str, keep_default_na=False)

    # 1. Validate required structure
    missing_cols = [col for col in config["required_columns"] if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # 2. Check primary keys (No blanks, no duplicates)
    pk = config["primary_key"]
    if df[pk].isin(["", None]).any():
        raise ValueError(f"Blank primary keys found in {pk}")
    if df[pk].duplicated().any():
        raise ValueError(f"Duplicate primary keys found in {pk}")

    # 3. Add ingestion metadata
    df["source_file"] = config["file"]
    df["ingestion_timestamp"] = datetime.now(timezone.utc).isoformat()

    # 4. Write processed output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / config["file"]
    df.to_csv(output_path, index=False)

    return len(df), output_path

def main():
    report_data = []
    for dataset_name, config in DATASETS.items():
        try:
            rows, out_path = ingest_dataset(dataset_name, config)
            print(f"{dataset_name}: SUCCESS | rows={rows} | output={out_path.relative_to(ROOT)}")
            report_data.append({"dataset": dataset_name, "status": "SUCCESS", "rows": rows, "error": ""})
        except Exception as e:
            print(f"{dataset_name}: FAILED | error={e}")
            report_data.append({"dataset": dataset_name, "status": "FAILED", "rows": 0, "error": str(e)})
            
    # Generate Run Summary
    report_df = pd.DataFrame(report_data)
    report_df.to_csv(OUTPUT_DIR / "ingestion_report.csv", index=False)

if __name__ == "__main__":
    main()