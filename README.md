# Customer Analytics Data Warehouse

A portfolio project demonstrating a SQL and Python data pipeline that transforms customer, order, payment, refund, and website-event CSV data through Bronze, Silver, and Gold layers using a MySQL database.

## Project Overview

This project demonstrates foundational data engineering practices, including:

- CSV ingestion and schema validation
- Primary-key validation and duplicate detection
- Bronze-layer loading into MySQL
- Silver-layer data cleaning and referential-integrity checks
- Gold-layer customer-level business aggregations
- SQL-based reconciliation and data-quality validation
- Transaction handling, rollback, and automated unit tests

The pipeline uses a small e-commerce demonstration dataset to illustrate how raw operational data can be prepared for analytical reporting.

## Business Problem

Customer analytics requires combining data from several operational sources. Orders describe purchases, payments record money received, refunds capture money returned, and website events represent customer activity.

Combining these datasets without controlling data quality or aggregation grain can produce inaccurate metrics, including duplicated order amounts and incorrect payment or refund totals.

This project builds a repeatable pipeline to clean, validate, and aggregate these datasets for customer-level analysis.

## Business Requirements

The demonstration pipeline is designed to:

1. Ingest five CSV datasets: customers, orders, payments, refunds, and website events.
2. Validate required columns and primary-key uniqueness.
3. Record source-file and ingestion-timestamp metadata in processed Bronze CSVs.
4. Load the processed datasets into MySQL Bronze tables.
5. Standardize customer and event attributes and filter invalid records.
6. Validate relationships between customers, orders, payments, refunds, and website events.
7. Generate a customer-level Gold summary with order, payment, refund, and website-event metrics.
8. Reconcile Gold metrics against Silver data and report data-quality exceptions.

## Architecture

```text
Source CSV Files
      |
      v
Bronze CSV Processing
  - Schema validation
  - Primary-key validation
  - Ingestion metadata
      |
      v
Processed Bronze CSVs
      |
      v
MySQL Bronze Tables
      |
      v
Silver Transformation
  - Standardization
  - Invalid-record filtering
  - Referential-integrity checks
      |
      v
MySQL Silver Tables
      |
      v
Gold Aggregation and Validation
  - Customer-level metrics
  - Reconciliation checks
  - Data-quality exception reporting
      |
      v
gold_customer_summary
```

### Medallion layers

**Bronze**

The Bronze processing script reads the original CSV files from `data/bronze/`, validates their structure and primary keys, adds `source_file` and `ingestion_timestamp`, and writes processed files to `data/processed_bronze/`.

A separate loader inserts these processed records into the MySQL Bronze tables.

**Silver**

The Silver loader standardizes and filters records, checks expected demonstration row counts, and validates relationships between the datasets. It stages transformed data in temporary tables before replacing the Silver tables.

**Gold**

The Gold refresh SQL builds a customer-level summary from Silver data. Orders, payments, refunds, and website events are aggregated independently before being joined to customers, preventing one-to-many joins from multiplying monetary totals.

The Gold refresh is followed by SQL validation and reconciliation checks.

## Technology Stack

- **Language:** Python
- **Data processing:** Pandas
- **Database:** MySQL
- **SQL:** Data transformation, aggregation, and validation
- **Database connectivity:** MySQL Connector/Python
- **Testing:** Python `unittest`
- **Version control:** Git and GitHub

## Repository Structure

```text
customer-analytics-data-warehouse/
├── data/
│   ├── bronze/                  # Source CSV files
│   └── processed_bronze/        # Generated processed CSVs
├── docs/
│   ├── architecture.md
│   └── silver_data_quality.md
├── python/
│   ├── bronze_ingestion.py
│   ├── load_bronze_to_mysql.py
│   ├── load_silver_to_mysql.py
│   └── load_gold_to_mysql.py
├── sql/
│   └── gold/
│       ├── refresh_gold_customer_summary.sql
│       └── validate_gold_customer_summary.sql
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

The repository may contain additional SQL scripts, documentation, and tests beyond those listed above.

## Source Datasets

| Dataset | Primary key | Required columns |
|---|---|---|
| Customers | `customer_id` | `customer_id`, `name`, `email`, `city`, `status`, `created_at` |
| Orders | `order_id` | `order_id`, `customer_id`, `order_time`, `amount` |
| Payments | `payment_id` | `payment_id`, `order_id`, `payment_time`, `paid_amount` |
| Refunds | `refund_id` | `refund_id`, `order_id`, `refund_time`, `refund_amount` |
| Website events | `event_id` | `event_id`, `customer_id`, `event_time`, `event_type` |

## Data Model and Grain

The Bronze and Silver layers retain separate datasets for customers, orders, payments, refunds, and website events.

The Gold table, `gold_customer_summary`, contains one summary row per customer.

Its metrics include:

- `order_count`
- `total_order_amount`
- `total_paid_amount`
- `total_refund_amount`
- `net_paid_amount`
- `website_event_count`
- `last_order_time`
- `has_refund_without_payment`
- `refreshed_at`

The monetary metrics are aggregated at their appropriate source grains before being combined into the customer-level summary. This avoids fan-out errors caused by directly joining multiple one-to-many relationships.

## ETL Pipeline

### 1. Bronze CSV processing

Script: `python/bronze_ingestion.py`

Responsibilities:

- Read the five source CSV files.
- Validate required columns.
- Reject blank and duplicate primary keys.
- Add source-file and UTC ingestion-timestamp metadata.
- Write processed CSVs to `data/processed_bronze/`.
- Generate `ingestion_report.csv`.

The script records a status for each dataset and continues processing other datasets if one fails. Review the report and console output before proceeding.

### 2. Bronze MySQL loading

Script: `python/load_bronze_to_mysql.py`

Responsibilities:

- Read processed Bronze CSVs.
- Validate required columns and primary keys.
- Insert records into the five MySQL Bronze tables.
- Use duplicate-key handling to avoid inserting an existing primary key again.
- Commit the datasets together or roll back the transaction on failure.

The current duplicate-key behavior leaves an existing record unchanged; it does not update it with newer source values.

### 3. Silver transformation

Script: `python/load_silver_to_mysql.py`

Responsibilities:

- Normalize customer names, email addresses, cities, statuses, and website-event types where applicable.
- Filter records with missing required values or invalid negative monetary amounts.
- Check customer and order relationships.
- Validate expected demonstration row counts.
- Replace the Silver tables after validation succeeds.

The Silver process is a **full replacement**, not an incremental merge.

### 4. Gold refresh and validation

Script: `python/load_gold_to_mysql.py`

Responsibilities:

- Execute the Gold refresh SQL.
- Build customer-level aggregates from Silver tables.
- Run mandatory reconciliation checks.
- Roll back the refresh if a required validation fails.
- Log nonfatal data-quality exceptions as warnings.

The Gold refresh rebuilds the summary table rather than incrementally updating only changed customers.

## Data Quality Checks

The pipeline includes checks for:

- Missing required CSV columns
- Blank and duplicate primary keys
- Missing required values
- Invalid negative monetary values
- Orders without valid customers
- Payments or refunds without valid orders
- Website events without valid customers
- Expected demonstration dataset counts
- Duplicate customer IDs in Gold
- Customer-count reconciliation between Silver and Gold
- Order-count and monetary-total reconciliation
- Refunds associated with orders without recorded payments

### Expected demonstration row counts

| Dataset | Expected rows |
|---|---:|
| Customers | 5 |
| Orders | 5 |
| Payments | 5 |
| Refunds | 2 |
| Website events | 5 |

These counts describe the current demonstration dataset, not a general production requirement.

### Known data-quality exception

The demonstration dataset contains a refund of 1,500 for order `1004` associated with customer `104`, with no recorded payment for that order.

The Gold layer flags this condition through `has_refund_without_payment`. Depending on the data, the customer's `net_paid_amount` can therefore be negative.

This is intentionally reported as a data-quality exception rather than silently correcting the source data. In a production environment, the next step would be to investigate the source records and business rules.

## Processing Strategy and Limitations

The current implementation is designed for a small, reproducible demonstration dataset.

- Bronze CSV processing generates a fresh ingestion timestamp when it runs.
- Bronze MySQL loading avoids duplicate primary-key inserts but does not update existing records.
- Silver processing stages and validates data, then replaces the Silver tables.
- Gold processing deletes and rebuilds the customer summary.
- Silver expects fixed row counts for the current demo dataset.
- The project does not yet implement a complete end-to-end incremental pipeline.
- A production deployment would require additional orchestration, monitoring, schema evolution handling, and recovery strategies.

These limitations are documented rather than presented as completed production capabilities.

## Local Setup

### Prerequisites

- Python installed
- MySQL Server running
- MySQL Workbench or another MySQL client
- Access to the existing `dataeng_demo` database
- Source CSV files in `data/bronze/`

**This project uses the existing `dataeng_demo` database. Do not create a new database for this workflow.**

### 1. Clone the repository

```bash
git clone https://github.com/skazaharali/customer-analytics-data-warehouse.git
cd customer-analytics-data-warehouse
```

If you already have the repository locally, open a terminal in the existing project directory instead.

### 2. Create and activate a virtual environment

On Windows Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bat
python -m pip install -r requirements.txt
```

### 4. Configure database environment variables

The scripts require these environment variables:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

Set them in your terminal session using your own MySQL connection details. For example, in Windows Command Prompt:

```bat
set DB_HOST=localhost
set DB_PORT=3306
set DB_NAME=dataeng_demo
set DB_USER=your_mysql_username
set DB_PASSWORD=your_mysql_password
```

Replace the example username and password with your actual credentials. Do not commit credentials to GitHub.

The repository ignores `.env`. Creating a `.env` file alone does not make these variables available unless the scripts explicitly load that file.

### 5. Verify the source CSVs

Confirm that the following files exist:

```text
data/bronze/customers.csv
data/bronze/orders.csv
data/bronze/payments.csv
data/bronze/refunds.csv
data/bronze/website_events.csv
```

Each file must contain the required columns listed in the Source Datasets section.

## How to Run the Pipeline

Run the scripts from the repository root, with the virtual environment activated and the database environment variables configured.

**Step 1 — Process the source CSVs**

```bat
python python\bronze_ingestion.py
```

Review the console output and:

```text
data/processed_bronze/ingestion_report.csv
```

Proceed only if all five datasets report `SUCCESS`.

**Step 2 — Load Bronze into MySQL**

```bat
python python\load_bronze_to_mysql.py
```

**Step 3 — Transform and validate Silver**

```bat
python python\load_silver_to_mysql.py
```

**Step 4 — Refresh and validate Gold**

```bat
python python\load_gold_to_mysql.py
```

Each step depends on the preceding layer being loaded successfully. Stop and investigate any failure before running the next step.

## Testing

Run the automated tests from the repository root:

```bat
python -m unittest discover -s tests -v
```

The test suite covers the implemented pipeline behavior and validation scenarios. A successful test run is indicated by the final `OK` summary.

The tests validate code behavior; they do not by themselves establish production readiness or guarantee that every real-world data-quality scenario is handled.

## Future Enhancements

Potential next steps include:

- Implementing incremental Silver processing using watermarks or change tracking
- Adding robust upsert and late-arriving-data handling
- Introducing Slowly Changing Dimensions (SCD Type 2) where historical attribute tracking is required
- Adding orchestration and scheduled pipeline execution
- Expanding monitoring, logging, and data-quality reporting
- Building a Power BI dashboard on top of validated Gold data
- Adding integration tests against a controlled MySQL test environment

These are planned enhancements, not claims about functionality already implemented.

## Project Status

The current repository demonstrates a working, layered data pipeline with Python-based ingestion, MySQL Bronze and Silver tables, a customer-level Gold summary, validation logic, and automated tests.

The implementation is a portfolio-scale demonstration. Incremental processing, historical SCD Type 2 tracking, orchestration, and a BI dashboard remain future enhancements unless implemented separately.
