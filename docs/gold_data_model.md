# Gold Layer — Customer Summary

## Purpose

The Gold layer provides a customer-level analytical summary for customer activity, order value, payments, refunds, and refund reconciliation exceptions.

**Source tables:** Silver layer tables in the `dataeng_demo` MySQL database.

**Target table:** `gold_customer_summary`

## Table Grain

One row per customer.

The `customer_id` column is the primary key. Customers with no orders are retained so that the summary represents the customer population, not only customers who have placed orders.

## Business Metrics

| Column | Definition |
|---|---|
| `customer_status` | Normalized customer status from Silver |
| `order_count` | Number of orders placed by the customer |
| `total_order_amount` | Sum of the customer's order amounts |
| `total_paid_amount` | Sum of recorded payments associated with the customer's orders |
| `total_refund_amount` | Sum of recorded refunds associated with the customer's orders |
| `net_paid_amount` | Total recorded payments minus total recorded refunds |
| `website_event_count` | Number of website events associated with the customer |
| `last_order_time` | Timestamp of the customer's most recent order, or NULL if no orders exist |
| `refreshed_at` | Timestamp indicating when the Gold row was refreshed |
| `has_refund_without_payment` | Boolean indicator that at least one order has a positive refund and no recorded payment |

## Aggregation Rules

Order, payment, refund, and website-event metrics are aggregated independently before they are joined to the customer dimension.

This avoids fact-table fan-out, where joining multiple one-to-many tables directly can multiply rows and inflate financial totals.

Customers with no matching activity receive zero for the applicable counts and monetary metrics. Their `last_order_time` remains NULL when no order exists.

## Financial Reconciliation

The following invariants are validated against the current Silver source data:

- Silver order count equals the sum of Gold `order_count`.
- Silver order amount equals Gold `total_order_amount`.
- Silver payment amount equals Gold `total_paid_amount`.
- Silver refund amount equals Gold `total_refund_amount`.

These checks confirm that the current Gold aggregates preserve the corresponding Silver totals.

## Known Business Exception

Customer `104` has an order (`1004`) with a recorded refund of `1500.00` and no recorded payment in Silver.

The Gold layer flags this customer using `has_refund_without_payment = 1`.

This flag identifies a reconciliation exception. It does not establish that the refund is invalid, nor does it prove that no payment occurred outside the available source records. The source data should be investigated rather than silently altered.

## Refresh Strategy

The Gold summary is refreshed by `sql/gold/refresh_gold_customer_summary.sql`.

The current strategy rebuilds the summary from Silver data within a transaction. The validation queries are maintained separately in `sql/gold/validate_gold_customer_summary.sql`.

The refresh should be rerun whenever the Silver source data changes, followed by the validation checks.