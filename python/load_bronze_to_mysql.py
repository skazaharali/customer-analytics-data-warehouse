
import csv
import os
from pathlib import Path

import mysql.connector


ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "data" / "processed_bronze"

# Only these source columns are inserted.
# source_file and ingestion_timestamp are processing metadata,
# not columns in the existing MySQL tables.
DATASETS = {
    "customers": {
        "file": "customers.csv",
        "table": "bronze_customers",
        "primary_key": "customer_id",
        "columns": [
            "customer_id", "name", "email",
            "city", "status", "created_at",
        ],
    },
    "orders": {
        "file": "orders.csv",
        "table": "bronze_orders",
        "primary_key": "order_id",
        "columns": [
            "order_id", "customer_id", "order_time", "amount",
        ],
    },
    "payments": {
        "file": "payments.csv",
        "table": "bronze_payments",
        "primary_key": "payment_id",
        "columns": [
            "payment_id", "order_id", "payment_time", "paid_amount",
        ],
    },
    "refunds": {
        "file": "refunds.csv",
        "table": "bronze_refunds",
        "primary_key": "refund_id",
        "columns": [
            "refund_id", "order_id", "refund_time", "refund_amount",
        ],
    },
    "website_events": {
        "file": "website_events.csv",
        "table": "bronze_website_events",
        "primary_key": "event_id",
        "columns": [
            "event_id", "customer_id", "event_time", "event_type",
        ],
    },
}


def read_and_validate_csv(config):
    path = INPUT_DIR / config["file"]

    if not path.exists():
        raise FileNotFoundError(f"Processed CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")

        missing = set(config["columns"]) - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"{config['file']} is missing columns: {sorted(missing)}"
            )

        rows = []
        seen_keys = set()
        primary_key = config["primary_key"]

        for line_number, row in enumerate(reader, start=2):
            values = [row.get(col) for col in config["columns"]]

            # Ignore completely blank lines.
            if all(value is None or not value.strip()
                   for value in values):
                continue

            key = (row.get(primary_key) or "").strip()

            if not key:
                raise ValueError(
                    f"Blank {primary_key} in {config['file']} "
                    f"at line {line_number}"
                )

            if key in seen_keys:
                raise ValueError(
                    f"Duplicate {primary_key}={key} in "
                    f"{config['file']}"
                )

            seen_keys.add(key)

            # Preserve CSV values; let MySQL convert numeric and
            # timestamp strings according to the existing table schema.
            rows.append(tuple(
                None if value == "" else value
                for value in values
            ))

    return rows


def main():
    # Validate every input before opening a database transaction.
    prepared = {}

    for name, config in DATASETS.items():
        rows = read_and_validate_csv(config)
        prepared[name] = rows
        print(f"{name}: VALIDATED | source_rows={len(rows)}")

    required_env = [
        "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"
    ]
    missing_env = [name for name in required_env if not os.getenv(name)]

    if missing_env:
        raise RuntimeError(
            "Missing environment variables: " + ", ".join(missing_env)
        )

    connection = None
    cursor = None

    try:
        connection = mysql.connector.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            database=os.environ["DB_NAME"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
        )

        cursor = connection.cursor()
        connection.start_transaction()

        for name, config in DATASETS.items():
            columns = config["columns"]
            table = config["table"]
            primary_key = config["primary_key"]
            rows = prepared[name]

            column_sql = ", ".join(f"`{col}`" for col in columns)
            placeholders = ", ".join(["%s"] * len(columns))

            # A duplicate business key leaves the existing row unchanged.
            # Unique indexes in MySQL enforce this behavior.
            query = (
                f"INSERT INTO `{table}` ({column_sql}) "
                f"VALUES ({placeholders}) "
                f"ON DUPLICATE KEY UPDATE "
                f"`{primary_key}` = `{primary_key}`"
            )

            if rows:
                cursor.executemany(query, rows)

            print(f"{name}: STAGED | source_rows={len(rows)}")

        # All five datasets commit together.
        connection.commit()
        print("Database transaction: COMMITTED")

        for name, config in DATASETS.items():
            cursor.execute(
                f"SELECT COUNT(*) FROM `{config['table']}`"
            )
            count = cursor.fetchone()[0]
            print(f"{name}: database_rows={count}")

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
            print("Database transaction: ROLLED BACK")
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
