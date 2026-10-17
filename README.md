Markdown
# Customer Analytics Data Warehouse

Production-style Customer Analytics Data Warehouse using SQL, Python, Medallion Architecture, Incremental ETL, and Slowly Changing Dimensions (SCD Type 2).

## Project Overview

## Business Problem

## Business Requirements

## Architecture Overview
This project processes raw e-commerce data (orders, payments, refunds, and high-velocity website events) through a strict Medallion Architecture:
*   **Bronze:** Raw, immutable landing zone with `ingestion_time` metadata.
*   **Silver:** Cleansed, deduplicated, and standardized data.
*   **Gold:** Star schema optimized for BI reporting, utilizing surrogate keys to preserve historical accuracy (SCD Type 2).

## Technology Stack

## Project Structure

## Data Model

## ETL Pipeline

## Data Quality Checks

## Incremental Processing Strategy

## Handling Late Arriving Data

## Dashboard

## Future Enhancements

## How to Run

## Pipeline Execution Log

## Bronze Layer — Current Implementation
The initial Bronze ingestion pipeline processes five local CSV datasets: `customers`, `orders`, `payments`, `refunds`, and `website_events`. 

The Python pipeline (`bronze_ingestion.py`):
1. Validates required columns and primary-key uniqueness.
2. Injects `source_file` and UTC `ingestion_timestamp` metadata.
3. Writes processed CSV outputs to an isolated directory.
4. Generates a pipeline execution run report.

## How to Run Locally

**1. Set up the environment**
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt