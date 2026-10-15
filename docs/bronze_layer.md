# Bronze Layer

The Bronze layer serves as the raw, immutable landing zone for all operational data entering the data warehouse.

## Design Principles
*   **Immutability:** Data in this layer is never updated or deleted. It represents an exact historical record of the source system at the time of extraction.
*   **Schema on Read:** Minimal type casting is enforced during ingestion to prevent load failures.
*   **Auditability:** Every record includes an `ingestion_time` metadata column.

## Metadata Column: `ingestion_time`
An `ingestion_time` column (`TIMESTAMP DEFAULT CURRENT_TIMESTAMP`) is appended to all Bronze tables. This is a critical production pattern that enables:
*   **Incremental Processing:** Downstream Silver models can filter by `ingestion_time` to process only new records.
*   **Late-Arriving Data Detection:** Allows engineers to compare `event_time` against `ingestion_time` to monitor data latency and update dirty partitions.
*   **Debugging:** Determines exactly when corrupted or anomalous records entered the pipeline.

## Datasets
*   `bronze_customers`: Customer dimension snapshots.
*   `bronze_orders`: Core transactional sales data.
*   `bronze_payments`: Payment attempts (including partial payments).
*   `bronze_refunds`: Refund transaction records.
*   `bronze_website_events`: High-velocity behavioral tracking events.