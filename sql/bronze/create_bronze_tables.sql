use dataeng_demo;

CREATE TABLE bronze_customers (
    customer_id INT,
    name VARCHAR(100),
    email VARCHAR(255),
    city VARCHAR(100),
    status VARCHAR(20),
    created_at TIMESTAMP,
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bronze_orders (
    order_id INT,
    customer_id INT,
    order_time TIMESTAMP,
    amount DECIMAL(10, 2),
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bronze_payments (
    payment_id INT,
    order_id INT,
    payment_time TIMESTAMP,
    paid_amount DECIMAL(10, 2),
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bronze_refunds (
    refund_id INT,
    order_id INT,
    refund_time TIMESTAMP,
    refund_amount DECIMAL(10, 2),
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bronze_website_events (
    event_id INT,
    customer_id INT,
    event_time TIMESTAMP,
    event_type VARCHAR(50),
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);