
import os
from pathlib import Path

import mysql.connector


ROOT = Path(__file__).resolve().parents[1]
DATABASE_NAME = "dataeng_demo"

TABLES = {
    "customers": "silver_customers",
    "orders": "silver_orders",
    "payments": "silver_payments",
    "refunds": "silver_refunds",
    "website_events": "silver_website_events",
}

EXPECTED_COUNTS = {
    "customers": 5,
    "orders": 5,
    "payments": 5,
    "refunds": 2,
    "website_events": 5,
}


def validate_environment():
    required = [
        "DB_HOST", "DB_PORT", "DB_NAME",
        "DB_USER", "DB_PASSWORD",
    ]
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        raise RuntimeError(
            "Missing environment variables: " + ", ".join(missing)
        )

    if os.environ["DB_NAME"] != DATABASE_NAME:
        raise RuntimeError(
            f"Expected DB_NAME={DATABASE_NAME}; "
            "refusing to run against another database."
        )


def create_staging_tables(cursor):
    # Temporary tables exist only for this database connection.
    for table in TABLES.values():
        cursor.execute(
            f"DROP TEMPORARY TABLE IF EXISTS `stage_{table}`"
        )
        cursor.execute(
            f"CREATE TEMPORARY TABLE `stage_{table}` LIKE `{table}`"
        )


def load_staging_tables(cursor):
    statements = [
        (
            "customers",
            """
            INSERT INTO stage_silver_customers
                (customer_id, name, email, city, status, created_at)
            SELECT
                customer_id,
                TRIM(name),
                LOWER(TRIM(email)),
                TRIM(city),
                LOWER(TRIM(status)),
                created_at
            FROM bronze_customers
            WHERE customer_id IS NOT NULL
              AND name IS NOT NULL AND TRIM(name) <> ''
              AND email IS NOT NULL AND TRIM(email) <> ''
              AND city IS NOT NULL AND TRIM(city) <> ''
              AND status IS NOT NULL AND TRIM(status) <> ''
            """,
        ),
        (
            "orders",
            """
            INSERT INTO stage_silver_orders
                (order_id, customer_id, order_time, amount)
            SELECT
                o.order_id, o.customer_id, o.order_time, o.amount
            FROM bronze_orders o
            INNER JOIN stage_silver_customers c
                ON o.customer_id = c.customer_id
            WHERE o.order_id IS NOT NULL
              AND o.order_time IS NOT NULL
              AND o.amount IS NOT NULL
              AND o.amount >= 0
            """,
        ),
        (
            "payments",
            """
            INSERT INTO stage_silver_payments
                (payment_id, order_id, payment_time, paid_amount)
            SELECT
                p.payment_id, p.order_id,
                p.payment_time, p.paid_amount
            FROM bronze_payments p
            INNER JOIN stage_silver_orders o
                ON p.order_id = o.order_id
            WHERE p.payment_id IS NOT NULL
              AND p.payment_time IS NOT NULL
              AND p.paid_amount IS NOT NULL
              AND p.paid_amount >= 0
            """,
        ),
        (
            "refunds",
            """
            INSERT INTO stage_silver_refunds
                (refund_id, order_id, refund_time, refund_amount)
            SELECT
                r.refund_id, r.order_id,
                r.refund_time, r.refund_amount
            FROM bronze_refunds r
            INNER JOIN stage_silver_orders o
                ON r.order_id = o.order_id
            WHERE r.refund_id IS NOT NULL
              AND r.refund_time IS NOT NULL
              AND r.refund_amount IS NOT NULL
              AND r.refund_amount >= 0
            """,
        ),
        (
            "website_events",
            """
            INSERT INTO stage_silver_website_events
                (event_id, customer_id, event_time, event_type)
            SELECT
                e.event_id,
                e.customer_id,
                e.event_time,
                LOWER(TRIM(e.event_type))
            FROM bronze_website_events e
            INNER JOIN stage_silver_customers c
                ON e.customer_id = c.customer_id
            WHERE e.event_id IS NOT NULL
              AND e.event_time IS NOT NULL
              AND e.event_type IS NOT NULL
              AND TRIM(e.event_type) <> ''
            """,
        ),
    ]

    for name, sql in statements:
        cursor.execute(sql)
        print(f"{name}: STAGED | rows={cursor.rowcount}")


def validate_staging_tables(cursor):
    counts = {}

    for name, target in TABLES.items():
        cursor.execute(f"SELECT COUNT(*) FROM `stage_{target}`")
        count = cursor.fetchone()[0]
        counts[name] = count

        print(f"{name}: staged_rows={count}")

        # These counts are the expected contract for the current demo
        # dataset. Update them deliberately when the fixture changes.
        if count != EXPECTED_COUNTS[name]:
            raise ValueError(
                f"{name}: expected {EXPECTED_COUNTS[name]} rows, "
                f"found {count}. Refresh aborted."
            )

    checks = [
        (
            "orders_without_customer",
            """
            SELECT COUNT(*)
            FROM stage_silver_orders o
            LEFT JOIN stage_silver_customers c
                ON o.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
            """,
        ),
        (
            "payments_without_order",
            """
            SELECT COUNT(*)
            FROM stage_silver_payments p
            LEFT JOIN stage_silver_orders o
                ON p.order_id = o.order_id
            WHERE o.order_id IS NULL
            """,
        ),
        (
            "refunds_without_order",
            """
            SELECT COUNT(*)
            FROM stage_silver_refunds r
            LEFT JOIN stage_silver_orders o
                ON r.order_id = o.order_id
            WHERE o.order_id IS NULL
            """,
        ),
        (
            "events_without_customer",
            """
            SELECT COUNT(*)
            FROM stage_silver_website_events e
            LEFT JOIN stage_silver_customers c
                ON e.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
            """,
        ),
    ]

    for name, sql in checks:
        cursor.execute(sql)
        issues = cursor.fetchone()[0]

        if issues:
            raise ValueError(f"{name}: found {issues} invalid rows")

        print(f"{name}: PASS | issues=0")

    return counts


def replace_silver_tables(cursor, counts):
    # No foreign keys currently exist. If they are added later,
    # child tables must be deleted before parent tables.
    for name in (
        "website_events", "refunds", "payments",
        "orders", "customers",
    ):
        cursor.execute(f"DELETE FROM `{TABLES[name]}`")

    for name, target in TABLES.items():
        cursor.execute(
            f"INSERT INTO `{target}` SELECT * FROM `stage_{target}`"
        )

        cursor.execute(f"SELECT COUNT(*) FROM `{target}`")
        actual = cursor.fetchone()[0]

        if actual != counts[name]:
            raise ValueError(
                f"{target}: staged={counts[name]}, loaded={actual}"
            )

        print(f"{target}: VERIFIED | rows={actual}")


def main():
    validate_environment()

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

        # Temporary-table DDL is performed before the data transaction.
        create_staging_tables(cursor)

        # Ensure no transaction was opened implicitly by the connector.
        if connection.in_transaction:
            connection.rollback()

        connection.start_transaction()

        load_staging_tables(cursor)
        counts = validate_staging_tables(cursor)
        replace_silver_tables(cursor, counts)

        connection.commit()
        print("Silver transaction: COMMITTED")
        print("Silver load completed successfully.")

    except Exception:
        if connection is not None and connection.is_connected():
            connection.rollback()
            print("Silver transaction: ROLLED BACK")
        raise

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    main()
