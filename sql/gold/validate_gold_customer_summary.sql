
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
