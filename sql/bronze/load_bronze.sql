COPY bronze_customers
FROM 'data/bronze/customers.csv'
DELIMITER ','
CSV HEADER;

COPY bronze_orders
FROM 'data/bronze/orders.csv'
DELIMITER ','
CSV HEADER;

COPY bronze_payments
FROM 'data/bronze/payments.csv'
DELIMITER ','
CSV HEADER;

COPY bronze_refunds
FROM 'data/bronze/refunds.csv'
DELIMITER ','
CSV HEADER;

COPY bronze_website_events
FROM 'data/bronze/website_events.csv'
DELIMITER ','
CSV HEADER;