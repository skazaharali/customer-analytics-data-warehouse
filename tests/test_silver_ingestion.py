
import unittest
from unittest.mock import Mock, patch

from python import load_silver_to_mysql as silver_loader


class TestSilverIngestion(unittest.TestCase):
    def test_validate_environment_rejects_wrong_database(self):
        env = {
            "DB_HOST": "localhost",
            "DB_PORT": "3306",
            "DB_NAME": "some_other_database",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_password",
        }

        with patch.dict("os.environ", env, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "refusing to run against another database",
            ):
                silver_loader.validate_environment()

    def test_validate_environment_rejects_missing_password(self):
        env = {
            "DB_HOST": "localhost",
            "DB_PORT": "3306",
            "DB_NAME": "dataeng_demo",
            "DB_USER": "test_user",
        }

        with patch.dict("os.environ", env, clear=True):
            with self.assertRaisesRegex(
                RuntimeError,
                "DB_PASSWORD",
            ):
                silver_loader.validate_environment()

    def test_staging_count_mismatch_aborts_validation(self):
        cursor = Mock()
        cursor.fetchone.return_value = (4,)

        with self.assertRaisesRegex(ValueError, "expected 5 rows"):
            silver_loader.validate_staging_tables(cursor)
    
    def test_validate_staging_tables_accepts_expected_counts(self):
        cursor = Mock()
        cursor.fetchone.side_effect = [
            (5,),  # customers
            (5,),  # orders
            (5,),  # payments
            (2,),  # refunds
            (5,),  # website events
            (0,),  # orders without customer
            (0,),  # payments without order
            (0,),  # refunds without order
            (0,),  # events without customer
        ]

        counts = silver_loader.validate_staging_tables(cursor)

        self.assertEqual(
            counts,
            {
                "customers": 5,
                "orders": 5,
                "payments": 5,
                "refunds": 2,
                "website_events": 5,
            },
        )


    def test_failed_refresh_rolls_back_transaction(self):
        connection = Mock()
        connection.is_connected.return_value = True
        connection.in_transaction = False

        cursor = Mock()
        connection.cursor.return_value = cursor

        with (
            patch.object(
                silver_loader,
                "validate_environment",
            ),
            patch(
                "mysql.connector.connect",
                return_value=connection,
            ),
            patch.object(
                silver_loader,
                "create_staging_tables",
            ),
            patch.object(
                silver_loader,
                "load_staging_tables",
                side_effect=RuntimeError("simulated staging failure"),
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "simulated staging failure",
            ):
                silver_loader.main()

        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()
        cursor.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
