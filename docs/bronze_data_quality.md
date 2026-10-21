# Bronze Layer Data Quality Report

## 1. Objective

Validate the Bronze layer after loading the source CSV files into the existing MySQL `dataeng_demo` schema.

## 2. Row Count Validation

| Dataset | Expected Rows | Actual Rows | Status |
|---|---:|---:|---|
| Customers | 5 | 5 | PASS |
| Orders | 5 | 5 | PASS |
| Payments | 5 | 5 | PASS |
| Refunds | 2 | 2 | PASS |
| Website Events | 5 | 5 | PASS |
| **Total** | **22** | **22** | **PASS** |

## 3. Data Quality Checks

| Check | Result | Status |
|---|---|---|
| Duplicate customer IDs | No duplicates found | PASS |
| Null customer IDs | No null IDs found | PASS |
| Duplicate order IDs | No duplicates found | PASS |
| Duplicate payment IDs | No duplicates found | PASS |
| Duplicate refund IDs | No duplicates found | PASS |
| Duplicate event IDs | No duplicates found | PASS |
| Orders referencing missing customers | No orphaned orders found | PASS |
| Negative order amounts | None found | PASS |
| Negative payment amounts | None found | PASS |
| Negative refund amounts | None found | PASS |

## 4. Database Details

- Database: `dataeng_demo`
- Database engine: MySQL
- Layer: Bronze
- Source format: CSV
- Total validated records: 22

## 5. Conclusion

All executed Bronze data-quality checks passed. The five Bronze tables contain the expected row counts, business keys are unique within each table, customer IDs are populated, and order-to-customer references are valid.

These checks establish the current data-quality baseline. Repeatable database ingestion and duplicate prevention remain separate engineering tasks and must be tested before the ingestion pipeline is considered production-ready.
