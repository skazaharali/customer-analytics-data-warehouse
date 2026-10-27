# Silver Layer — Data Quality and Transformation

## 1. Overview

The Silver layer transforms raw Bronze data into cleaned, standardized, and validated tables using MySQL.

**Database:** `dataeng_demo`

**Source:** Bronze tables

**Target:** Silver tables

**Load strategy:** Full refresh

## 2. Source and Target Tables

| Bronze Source | Silver Target | Expected Rows |
|---|---|---:|
| `bronze_customers` | `silver_customers` | 5 |
| `bronze_orders` | `silver_orders` | 5 |
| `bronze_payments` | `silver_payments` | 5 |
| `bronze_refunds` | `silver_refunds` | 2 |
| `bronze_website_events` | `silver_website_events` | 5 |
| **Total** | | **22** |

## 3. Transformation Rules

### Customers

- Trim leading and trailing whitespace from `name` and `city`.
- Trim whitespace and convert `email` to lowercase.
- Trim whitespace and convert `status` to lowercase.
- Exclude records with a missing customer ID or blank required text fields.
- Preserve `created_at`.

### Orders

- Retain valid order IDs, timestamps, and non-negative amounts.
- Require a matching customer in Bronze.
- Load only orders whose customers satisfy the Silver customer validation rules.

### Payments

- Retain valid payment IDs, timestamps, and non-negative payment amounts.
- Require a matching order in Silver.
- Preserve one row per `payment_id`.

### Refunds

- Retain valid refund IDs, timestamps, and non-negative refund amounts.
- Require a matching order in Silver.
- Preserve one row per `refund_id`.

### Website Events

- Retain valid event IDs and timestamps.
- Exclude missing or blank event types.
- Trim whitespace and convert `event_type` to lowercase.
- Require a matching customer in Silver.

## 4. Data Quality Checks

The following checks were executed against the Silver tables.

| Check | Result |
|---|---|
| Duplicate business-key groups | 0 across all five tables |
| Negative order amounts | 0 |
| Negative payment amounts | 0 |
| Negative refund amounts | 0 |
| Orders without customers | 0 |
| Payments without orders | 0 |
| Refunds without orders | 0 |
| Website events without customers | 0 |

Primary keys enforce uniqueness for each table's business key.

## 5. Row Count Validation

| Table | Expected | Actual | Result |
|---|---:|---:|---|
| `silver_customers` | 5 | 5 | PASS |
| `silver_orders` | 5 | 5 | PASS |
| `silver_payments` | 5 | 5 | PASS |
| `silver_refunds` | 2 | 2 | PASS |
| `silver_website_events` | 5 | 5 | PASS |
| **Total** | **22** | **22** | **PASS** |

The same row counts were observed after rerunning the full-refresh load.

## 6. Loading Strategy and Idempotency

The Silver load uses a full-refresh strategy:

1. Delete existing Silver records.
2. Load validated and transformed records from Bronze.
3. Commit the transaction after successful inserts.

The load was rerun successfully without increasing the row counts.

This demonstrates repeatable full-refresh behavior for the current dataset. It is not an incremental load and does not implement change data capture (CDC).

The Silver tables currently do not have foreign-key constraints; relationships are validated through transformation joins and data quality queries.

## 7. Limitations and Future Improvements

- Add automated tests for the MySQL Silver loader.
- Test rollback and recovery after a deliberately simulated load failure.
- Introduce an explicit rejected-record or quarantine process.
- Consider foreign-key constraints after reviewing the desired schema design.
- Implement incremental loading and late-arriving data handling in a later stage.
- Expand testing with nulls, duplicate source records, orphan records, and negative amounts.

## 8. Completion Status

The Silver tables were created, populated, and validated against the current Bronze dataset. All five tables contain the expected row counts, and the executed quality checks returned zero issues.
