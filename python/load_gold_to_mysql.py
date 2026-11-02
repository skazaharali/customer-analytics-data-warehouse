
import logging
import os
import re
from pathlib import Path

import mysql.connector


ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql" / "gold"

REFRESH_SQL = SQL_DIR / "refresh_gold_customer_summary.sql"
VALIDATE_SQL = SQL_DIR / "validate_gold_customer_summary.sql"

REQUIRED_ENV = (
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
)

REQUIRED_GOLD_CHECKS = {
    "customer_count_check",
    "duplicate_customer_check",
    "order_count_check",
    "order_amount_check",
    "payment_amount_check",
    "refund_amount_check",
    "customer_metrics_check",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def split_sql_file(path):
    """Split the current project SQL files into executable statements."""
    if not path.is_file():
        raise FileNotFoundError(f"SQL file not found: {path}")

    content = path.read_text(encoding="utf-8-sig")

    # Remove SQL comments before splitting this project's statements.
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    content = re.sub(r"(?m)^\s*--.*$", "", content)

    return [
        statement.strip()
        for statement in content.split(";")
        if statement.strip()
    ]


def execute_sql_file(cursor, path, validation=False):
    """Execute statements and fail if any required validation fails."""
    observed_checks = set()
    for statement in split_sql_file(path):
        normalized = statement.strip().upper()

        # The connection already selects DB_NAME.
        if normalized.startswith("USE "):
            continue

        # Python owns the transaction, so SQL transaction-control
        # statements in the refresh file are intentionally skipped.
        if normalized in ("START TRANSACTION", "BEGIN", "COMMIT"):
            continue

        cursor.execute(statement)

        if cursor.description is None:
            logger.info("SQL statement executed successfully")
            continue

        columns = [item[0] for item in cursor.description]
        rows = cursor.fetchall()

        # Required validation queries have columns ending in "_check".
        check_columns = [
            index
            for index, name in enumerate(columns)
            if name.lower().endswith("_check")
        ]

        if validation and check_columns:
            for row in rows:
                for index in check_columns:
                    check_name = columns[index]
                    result = str(row[index]).upper()
                    observed_checks.add(check_name.lower())

                    logger.info("%s: %s", check_name, result)

                    if result != "PASS":
                        raise RuntimeError(
                            f"Gold validation failed: "
                            f"{check_name}={result}"
                        )

        elif validation:
            # These result sets identify data exceptions. They are
            # reported for review, not automatically treated as failure.
            logger.warning(
                "Validation exception query returned %d row(s)",
                len(rows),
            )

            for row in rows:
                logger.warning("%s", dict(zip(columns, row)))

        elif rows and columns:
            # Refresh summary and Gold table results.
            logger.info("Query returned %d row(s)", len(rows))

            for row in rows:
                logger.info("%s", dict(zip(columns, row)))
    return observed_checks

def main():
    missing = [
        name for name in REQUIRED_ENV
        if not os.getenv(name)
    ]

    if missing:
        raise RuntimeError(
            "Missing environment variables: " + ", ".join(missing)
        )

    if not REFRESH_SQL.is_file():
        raise FileNotFoundError(f"Missing SQL file: {REFRESH_SQL}")

    if not VALIDATE_SQL.is_file():
        raise FileNotFoundError(f"Missing SQL file: {VALIDATE_SQL}")

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

        logger.info("Starting Gold customer summary refresh")

        execute_sql_file(cursor, REFRESH_SQL)

        logger.info("Running Gold data quality checks")

        observed_checks = execute_sql_file(
            cursor,
            VALIDATE_SQL,
            validation=True,
        )

        missing_checks = REQUIRED_GOLD_CHECKS - observed_checks

        if missing_checks:
            raise RuntimeError(
                "Gold validation did not execute all required checks. "
                f"Missing: {sorted(missing_checks)}"
            )

        connection.commit()
        logger.info("Gold refresh and validation: SUCCESS")

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
            logger.error("Transaction rolled back")

        logger.exception("Gold pipeline failed")
        raise

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
