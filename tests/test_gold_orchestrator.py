
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from python import load_gold_to_mysql as gold



class FakeCursor:
    def __init__(self, validation_result="PASS"):
        self.validation_result = validation_result
        self.description = None
        self.closed = False

    def execute(self, statement):
        check_names = (
            "customer_count_check",
            "duplicate_customer_check",
            "order_count_check",
            "order_amount_check",
            "payment_amount_check",
            "refund_amount_check",
        )

        matched = [
            name for name in check_names
            if name in statement
        ]

        self.description = (
            tuple((name,) for name in matched)
            if matched else None
        )

    def fetchall(self):
        if self.description is None:
            return []

        return [
            tuple(
                self.validation_result
                for _ in self.description
            )
        ]

    def close(self):
        self.closed = True




class FakeConnection:
    def __init__(self, validation_result="PASS"):
        self.fake_cursor = FakeCursor(validation_result)
        self.committed = False
        self.rolled_back = False
        self.closed = False
        self.transaction_started = False

    def cursor(self):
        return self.fake_cursor

    def start_transaction(self):
        self.transaction_started = True

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def is_connected(self):
        return not self.closed

    def close(self):
        self.closed = True


class TestGoldOrchestrator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.directory = Path(self.temp_dir.name)

        self.refresh_file = self.directory / "refresh.sql"
        self.validation_file = self.directory / "validate.sql"

        self.refresh_file.write_text(
            "DELETE FROM gold_customer_summary;",
            encoding="utf-8",
        )
        self.validation_file.write_text(
            """
            SELECT 'PASS' AS customer_count_check;

            SELECT 'PASS' AS duplicate_customer_check;

            SELECT
                'PASS' AS order_count_check,
                'PASS' AS order_amount_check,
                'PASS' AS payment_amount_check,
                'PASS' AS refund_amount_check;
            """,
            encoding="utf-8",
        )

        self.env = patch.dict(os.environ, {
            "DB_HOST": "localhost",
            "DB_PORT": "3306",
            "DB_NAME": "dataeng_demo",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_password",
        })
        self.env.start()
        self.addCleanup(self.env.stop)

    def run_pipeline(self, connection):
        with (
            patch.object(gold, "REFRESH_SQL", self.refresh_file),
            patch.object(gold, "VALIDATE_SQL", self.validation_file),
            patch.object(
                gold.mysql.connector,
                "connect",
                return_value=connection,
            ),
        ):
            gold.main()

    def test_sql_file_splits_into_statements(self):
        statements = gold.split_sql_file(self.refresh_file)
        self.assertEqual(
            statements,
            ["DELETE FROM gold_customer_summary"],
        )

    def test_validation_pass_is_accepted(self):
        connection = FakeConnection("PASS")
        self.run_pipeline(connection)

    def test_validation_fail_raises_error(self):
        connection = FakeConnection("FAIL")

        with self.assertRaisesRegex(
            RuntimeError,
            "Gold validation failed",
        ):
            self.run_pipeline(connection)

    def test_unexpected_validation_result_fails(self):
        connection = FakeConnection("UNKNOWN")

        with self.assertRaisesRegex(
            RuntimeError,
            "Gold validation failed",
        ):
            self.run_pipeline(connection)

    def test_successful_pipeline_commits(self):
        connection = FakeConnection("PASS")
        self.run_pipeline(connection)

        self.assertTrue(connection.transaction_started)
        self.assertTrue(connection.committed)
        self.assertFalse(connection.rolled_back)
        self.assertTrue(connection.closed)

    def test_failed_validation_rolls_back_without_commit(self):
        connection = FakeConnection("FAIL")

        with self.assertRaises(RuntimeError):
            self.run_pipeline(connection)

        self.assertTrue(connection.rolled_back)
        self.assertFalse(connection.committed)
        self.assertTrue(connection.closed)


if __name__ == "__main__":
    unittest.main()
