
USE dataeng_demo;

-- Refresh the customer-level Gold summary.
-- Aggregate each fact table independently to prevent join fan-out.

START TRANSACTION;

DELETE FROM gold_customer_summary;

INSERT INTO gold_customer_summary (
    customer_id,
    customer_status,
    order_count,
    total_order_amount,
    total_paid_amount,
    total_refund_amount,
    net_paid_amount,
    website_event_count,
    last_order_time,
    refreshed_at,
    has_refund_without_payment
)
SELECT
    c.customer_id,
    c.status,
    COALESCE(o.order_count, 0),
    COALESCE(o.total_order_amount, 0.00),
    COALESCE(p.total_paid_amount, 0.00),
    COALESCE(r.total_refund_amount, 0.00),
    COALESCE(p.total_paid_amount, 0.00)
        - COALESCE(r.total_refund_amount, 0.00),
    COALESCE(e.website_event_count, 0),
    o.last_order_time,
    CURRENT_TIMESTAMP,
    COALESCE(a.has_refund_without_payment, 0)
FROM silver_customers c
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS total_order_amount,
        MAX(order_time) AS last_order_time
    FROM silver_orders
    GROUP BY customer_id
) o ON o.customer_id = c.customer_id
LEFT JOIN (
    SELECT
        ord.customer_id,
        SUM(pay.paid_amount) AS total_paid_amount
    FROM silver_payments pay
    JOIN silver_orders ord ON ord.order_id = pay.order_id
    GROUP BY ord.customer_id
) p ON p.customer_id = c.customer_id
LEFT JOIN (
    SELECT
        ord.customer_id,
        SUM(ref.refund_amount) AS total_refund_amount
    FROM silver_refunds ref
    JOIN silver_orders ord ON ord.order_id = ref.order_id
    GROUP BY ord.customer_id
) r ON r.customer_id = c.customer_id
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) AS website_event_count
    FROM silver_website_events
    GROUP BY customer_id
) e ON e.customer_id = c.customer_id
LEFT JOIN (
    SELECT
        ord.customer_id,
        1 AS has_refund_without_payment
    FROM silver_orders ord
    JOIN silver_refunds ref ON ref.order_id = ord.order_id
    LEFT JOIN (
        SELECT
            order_id,
            SUM(paid_amount) AS payment_total
        FROM silver_payments
        GROUP BY order_id
    ) pay ON pay.order_id = ord.order_id
    WHERE ref.refund_amount > 0
      AND COALESCE(pay.payment_total, 0) = 0
    GROUP BY ord.customer_id
) a ON a.customer_id = c.customer_id;

COMMIT;

-- Validation: customer count and key metrics.
SELECT
    COUNT(*) AS customer_count,
    SUM(order_count) AS total_orders,
    SUM(total_order_amount) AS total_order_amount,
    SUM(total_paid_amount) AS total_paid_amount,
    SUM(total_refund_amount) AS total_refund_amount,
    SUM(has_refund_without_payment) AS flagged_customers
FROM gold_customer_summary;

SELECT *
FROM gold_customer_summary
ORDER BY customer_id;
