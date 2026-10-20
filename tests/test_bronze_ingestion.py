import unittest
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "processed_bronze"

EXPECTED_ROWS = {
    "customers": 5,
    "orders": 5,
    "payments": 5,
    "refunds": 2,
    "website_events": 5,
}

class TestBronzeIngestion(unittest.TestCase):
    def test_output_row_counts(self):
        for dataset, expected_count in EXPECTED_ROWS.items():
            with self.subTest(dataset=dataset):
                path = OUTPUT_DIR / f"{dataset}.csv"
                self.assertTrue(path.exists(), f"Missing {path}")
                
                df = pd.read_csv(path, dtype=str, keep_default_na=False)
                self.assertEqual(len(df), expected_count)

    def test_ingestion_metadata(self):
        for dataset in EXPECTED_ROWS:
            with self.subTest(dataset=dataset):
                path = OUTPUT_DIR / f"{dataset}.csv"
                df = pd.read_csv(path, dtype=str, keep_default_na=False)
                
                self.assertIn("source_file", df.columns)
                self.assertIn("ingestion_timestamp", df.columns)
                self.assertTrue((df["source_file"] != "").all())
                self.assertTrue((df["ingestion_timestamp"] != "").all())

if __name__ == "__main__":
    unittest.main()