
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLD_REFRESH_SQL = (
    PROJECT_ROOT / "sql" / "gold" / "refresh_gold_customer_summary.sql"
)
GOLD_VALIDATION_SQL = (
    PROJECT_ROOT / "sql" / "gold" / "validate_gold_customer_summary.sql"
)
GOLD_DOCUMENTATION = PROJECT_ROOT / "docs" / "gold_data_model.md"


class TestGoldLayer(unittest.TestCase):
    def test_refresh_sql_exists_and_is_not_empty(self):
        self.assertTrue(GOLD_REFRESH_SQL.is_file())

        sql = GOLD_REFRESH_SQL.read_text(encoding="utf-8").strip()
        self.assertTrue(sql, "Gold refresh SQL must not be empty")

    def test_refresh_sql_uses_existing_database(self):
        sql = GOLD_REFRESH_SQL.read_text(encoding="utf-8").lower()

        self.assertIn("use dataeng_demo", sql)
        self.assertNotIn("create database", sql)

    def test_refresh_sql_aggregates_fact_tables_independently(self):
        sql = GOLD_REFRESH_SQL.read_text(encoding="utf-8").lower()

        for table in (
            "silver_orders",
            "silver_payments",
            "silver_refunds",
            "silver_website_events",
        ):
            with self.subTest(table=table):
                self.assertIn(table, sql)

        self.assertIn("gold_customer_summary", sql)

    def test_refresh_sql_includes_refund_without_payment_flag(self):
        sql = GOLD_REFRESH_SQL.read_text(encoding="utf-8").lower()

        self.assertIn("has_refund_without_payment", sql)

    def test_validation_sql_exists_and_checks_gold_table(self):
        self.assertTrue(GOLD_VALIDATION_SQL.is_file())

        sql = GOLD_VALIDATION_SQL.read_text(encoding="utf-8").lower()
        self.assertIn("gold_customer_summary", sql)
        self.assertIn("silver_orders", sql)
        self.assertIn("silver_payments", sql)
        self.assertIn("silver_refunds", sql)

    def test_gold_documentation_exists_and_describes_grain(self):
        self.assertTrue(GOLD_DOCUMENTATION.is_file())

        documentation = GOLD_DOCUMENTATION.read_text(
            encoding="utf-8"
        ).lower()

        self.assertIn("one row per customer", documentation)
        self.assertIn("has_refund_without_payment", documentation)
        self.assertIn("fan-out", documentation)


if __name__ == "__main__":
    unittest.main()
