# Warehouse Metrics Classification

Understanding which metrics are additive ensures they are aggregated correctly in the BI layer. Non-additive metrics must be calculated at the visualization layer, not pre-aggregated in the warehouse.

| Metric | Additive |
| :--- | :--- |
| `order_amount` | ✅ |
| `refund_amount` | ✅ |
| `payment_amount` | ✅ |
| `total_orders` | ✅ |
| `conversion_rate` | ❌ |
| `refund_rate` | ❌ |
| `average_order_value` | ❌ |