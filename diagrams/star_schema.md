erDiagram
    dim_date ||--o{ fact_orders : "filters by"
    dim_date ||--o{ fact_payments : "filters by"
    dim_date ||--o{ fact_refunds : "filters by"
    dim_date ||--o{ fact_events : "filters by"
    
    dim_customer_scd ||--o{ fact_orders : "places (customer_sk)"
    dim_customer_scd ||--o{ fact_payments : "makes (customer_sk)"
    dim_customer_scd ||--o{ fact_refunds : "receives (customer_sk)"
    dim_customer_scd ||--o{ fact_events : "generates (customer_sk)"

    fact_orders ||--o{ fact_payments : "has"
    fact_orders ||--o{ fact_refunds : "has"