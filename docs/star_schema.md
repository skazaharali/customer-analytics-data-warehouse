# Star Schema Design

## 1. Dimensions

### `dim_customer_scd`
*   **Purpose:** Stores customer history and tracks status changes over time.
*   **Grain:** One row per customer version.
*   **Business/Natural Key:** `customer_id`
*   **Surrogate Key:** `customer_sk`
*   **SCD Type:** Type 2

**Attributes:**
*   `customer_sk` (Primary Key)
*   `customer_id` 
*   `customer_name`
*   `email`
*   `city`
*   `status`
*   `start_date`
*   `end_date`
*   `is_current`

### `dim_date`
*   **Purpose:** Shared calendar analysis.
*   **Grain:** One row per calendar date.

**Attributes:**
*   `date_key` (Primary Key)
*   `date`
*   `year`
*   `month`
*   `quarter`
*   `weekday`
*   `is_weekend`

---

## 2. Facts

### `fact_orders`
*   **Purpose:** Records every completed purchase.
*   **Grain:** Exactly 1 row per order.
*   **Business Key:** `order_id`
*   **Foreign Keys:** `customer_sk`, `date_key`
*   **Measures:** `order_amount`, `shipping_amount`, `discount`, `tax`

### `fact_payments`
*   **Purpose:** Records payment attempts.
*   **Grain:** 1 row per payment_id.
*   **Foreign Keys:** `customer_sk`, `date_key`, `order_id`
*   **Measures:** `paid_amount`

### `fact_refunds`
*   **Purpose:** Records refund events.
*   **Grain:** 1 row per refund_id.
*   **Foreign Keys:** `customer_sk`, `date_key`, `order_id`
*   **Measures:** `refund_amount`

### `fact_events`
*   **Purpose:** Captures website activity and behavioral events.
*   **Grain:** 1 row per event.
*   **Foreign Keys:** `customer_sk`, `date_key`
*   **Measures:** None (Primarily used for counts and sessionization)

---

## 3. Core Architectural Decision: The Surrogate Key
We explicitly use `customer_sk` instead of `customer_id` in our fact tables. Because `dim_customer_scd` is an SCD Type 2 dimension, a single `customer_id` will have multiple rows (representing different historical states). By mapping facts to the `customer_sk`, every order accurately points to the exact historical version of the customer that was valid at the time the transaction occurred, guaranteeing strict point-in-time reporting accuracy.

---

## 4. Entity Relationship Diagram (ERD)

```text
                 [ dim_date ]
                      |
                      |
[ dim_customer ] -- [ fact_orders ] ----- [ fact_payments ]
          |                   |
          |                   |
          |             [ fact_refunds ]
          |
  [ fact_events ]