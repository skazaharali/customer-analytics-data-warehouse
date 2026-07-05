# Table Grain Definitions

Defining the exact grain of each table is critical to prevent dual-fact fan-out traps and ensure accurate aggregations.

| Table | Grain |
| :--- | :--- |
| `dim_customer_scd` | One row per customer version. |
| `dim_date` | One row per calendar date. |
| `fact_orders` | One row per order. |
| `fact_payments` | One row per payment. |
| `fact_refunds` | One row per refund. |
| `fact_events` | One row per event. |