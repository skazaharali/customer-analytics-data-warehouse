# Logical Data Model

## Business Entities
Based on the business requirements, we have identified the following core entities from our source systems:
*   Customer
*   Order
*   Payment
*   Refund
*   Website Event
*   Customer Status
*   Date

## Entity Classification (Fact vs. Dimension)

| Entity | Type | Why |
| :--- | :--- | :--- |
| **Customer** | Dimension | Describes the customer. |
| **Customer Status** | Dimension (SCD2) | Changes over time. |
| **Date** | Dimension | Shared calendar lookup. |
| **Order** | Fact | Core business transaction. |
| **Payment** | Fact | Financial event tied to an order. |
| **Refund** | Fact | Financial event tied to an order. |
| **Website Event** | Fact | High-velocity behavioral event. |

## High-Level Data Flow

```text
Customer CSV
Order CSV
Payment CSV
Refund CSV
Website Events CSV
       ↓
    [Bronze] (Raw Data / Immutable)
       ↓
    [Silver] (Cleansed / Standardized / Deduplicated)
       ↓
     [Gold]  (Star Schema / Business Aggregations)
       ↓
  [Dashboard] (Executive Reporting & BI)