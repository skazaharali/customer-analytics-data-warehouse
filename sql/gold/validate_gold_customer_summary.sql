
USE dataeng_demo;

-- 1. Customer count validation.
SELECT
    CASE
        WHEN (SELECT COUNT(*) FROM silver_customers) =
             (SELECT COUNT(*) FROM gold_customer_summary)
        THEN 'PASS'
        ELSE 'FAIL'
    END AS customer_count_check;

-- 2. Duplicate customer key validation.
SELECT
    CASE
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS duplicate_customer_check
FROM (
    SELECT customer_id
    FROM gold_customer_summary
    GROUP BY customer_id
    HAVING COUNT(*) > 1
) duplicates;

-- 3. Financial and order reconciliation.
SELECT
    CASE WHEN
        (SELECT COUNT(*) FROM silver_orders) =
        (SELECT COALESCE(SUM(order_count), 0)
         FROM gold_customer_summary)
    THEN 'PASS' ELSE 'FAIL'
    END AS order_count_check,

    CASE WHEN
        (SELECT COALESCE(SUM(amount), 0) FROM silver_orders) =
        (SELECT COALESCE(SUM(total_order_amount), 0)
         FROM gold_customer_summary)
    THEN 'PASS' ELSE 'FAIL'
    END AS order_amount_check,

    CASE WHEN
        (SELECT COALESCE(SUM(paid_amount), 0) FROM silver_payments) =
        (SELECT COALESCE(SUM(total_paid_amount), 0)
         FROM gold_customer_summary)
    THEN 'PASS' ELSE 'FAIL'
    END AS payment_amount_check,

    CASE WHEN
        (SELECT COALESCE(SUM(refund_amount), 0) FROM silver_refunds) =
        (SELECT COALESCE(SUM(total_refund_amount), 0)
         FROM gold_customer_summary)
    THEN 'PASS' ELSE 'FAIL'
    END AS refund_amount_check;

-- 4. Verify the known refund-without-payment exception.
SELECT customer_id, has_refund_without_payment
FROM gold_customer_summary
WHERE has_refund_without_payment = 1;

-- 5. Identify orders with positive refunds and no recorded payment.
SELECT
    o.order_id,
    o.customer_id,
    SUM(r.refund_amount) AS refund_total
FROM silver_orders o
JOIN silver_refunds r ON r.order_id = o.order_id
LEFT JOIN (
    SELECT order_id, SUM(paid_amount) AS payment_total
    FROM silver_payments
    GROUP BY order_id
) p ON p.order_id = o.order_id
WHERE r.refund_amount > 0
GROUP BY o.order_id, o.customer_id, p.payment_total
HAVING COALESCE(p.payment_total, 0) = 0;


-- 6. Customer-level Gold reconciliation.
WITH
order_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS order_count,
        SUM(amount) AS total_order_amount,
        MAX(order_time) AS last_order_time
    FROM silver_orders
    GROUP BY customer_id
),
payment_metrics AS (
    SELECT
        o.customer_id,
        SUM(p.paid_amount) AS total_paid_amount
    FROM silver_orders o
    JOIN silver_payments p
        ON p.order_id = o.order_id
    GROUP BY o.customer_id
),
refund_metrics AS (
    SELECT
        o.customer_id,
        SUM(r.refund_amount) AS total_refund_amount
    FROM silver_orders o
    JOIN silver_refunds r
        ON r.order_id = o.order_id
    GROUP BY o.customer_id
),
event_metrics AS (
    SELECT
        customer_id,
        COUNT(*) AS website_event_count
    FROM silver_website_events
    GROUP BY customer_id
),
refund_flag_metrics AS (
    SELECT
        ord.customer_id,
        1 AS has_refund_without_payment
    FROM silver_orders ord
    JOIN silver_refunds ref
        ON ref.order_id = ord.order_id
    LEFT JOIN (
        SELECT
            order_id,
            SUM(paid_amount) AS payment_total
        FROM silver_payments
        GROUP BY order_id
    ) pay
        ON pay.order_id = ord.order_id
    WHERE ref.refund_amount > 0
      AND COALESCE(pay.payment_total, 0) = 0
    GROUP BY ord.customer_id
),
customer_mismatches AS (
    SELECT c.customer_id
    FROM silver_customers c
    LEFT JOIN order_metrics o
        ON o.customer_id = c.customer_id
    LEFT JOIN payment_metrics p
        ON p.customer_id = c.customer_id
    LEFT JOIN refund_metrics r
        ON r.customer_id = c.customer_id
    LEFT JOIN event_metrics e
        ON e.customer_id = c.customer_id
    LEFT JOIN refund_flag_metrics f
        ON f.customer_id = c.customer_id
    LEFT JOIN gold_customer_summary g
        ON g.customer_id = c.customer_id
    WHERE
           g.customer_id IS NULL
        OR NOT (g.customer_status <=> c.status)
        OR NOT (g.order_count <=> COALESCE(o.order_count, 0))
        OR NOT (g.total_order_amount <=> COALESCE(o.total_order_amount, 0))
        OR NOT (g.total_paid_amount <=> COALESCE(p.total_paid_amount, 0))
        OR NOT (g.total_refund_amount <=> COALESCE(r.total_refund_amount, 0))
        OR NOT (
            g.net_paid_amount
            <=> COALESCE(p.total_paid_amount, 0)
               - COALESCE(r.total_refund_amount, 0)
        )
        OR NOT (g.website_event_count <=> COALESCE(e.website_event_count, 0))
        OR NOT (g.last_order_time <=> o.last_order_time)
        OR NOT (
            g.has_refund_without_payment
            <=> COALESCE(f.has_refund_without_payment, 0)
        )

    UNION ALL

    SELECT g.customer_id
    FROM gold_customer_summary g
    LEFT JOIN silver_customers c
        ON c.customer_id = g.customer_id
    WHERE c.customer_id IS NULL
)
SELECT
    CASE
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS customer_metrics_check
FROM customer_mismatches;
