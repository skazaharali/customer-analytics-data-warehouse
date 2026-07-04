# Business Requirements

## Background

NovaCart is a fast-growing e-commerce company that sells products through multiple online channels.

The company currently receives operational data from several independent systems including customer management, orders, payments, refunds, and website events.

Different departments calculate KPIs differently, causing inconsistent reporting across the organization.

To solve this problem, the analytics team requires a centralized Customer Analytics Data Warehouse that produces trusted business metrics.

## Business Goals

The warehouse should enable:

- Daily revenue reporting
- Customer Lifetime Value (CLV)
- Refund analysis
- Payment success analysis
- Customer status tracking
- Website conversion analysis
- Executive dashboards

## Source Systems

1. Customer Management System

Contains

- customer_id
- registration
- customer profile

2. Order Management System

Contains

- orders
- order items

3. Payment Gateway

Contains

- payment attempts
- payment status

4. Refund Service

Contains

- refund requests
- refund completion

5. Website Tracking

Contains

- clicks
- sessions
- page views

6. Customer Status Service

Contains historical customer status changes.

## KPIs

Daily Revenue

Daily Orders

Average Order Value

Refund Rate

Payment Success Rate

Conversion Rate

Customer Lifetime Value

Revenue by Customer Status

Top Customers

## Functional Requirements

The warehouse shall

- Store historical customer status
- Support late-arriving events
- Support incremental loading
- Maintain historical accuracy
- Produce daily aggregates
- Support dashboard reporting
- Preserve additive metrics

## Non Functional Requirements

The pipeline shall

Finish within 30 minutes

Be idempotent

Support historical backfills

Support partition pruning

Be scalable

Support data quality validation

Handle late-arriving data

Be maintainable

## Assumptions

Orders are immutable.

Payments may arrive late.

Refunds may be partial.

Customers may change status.

Historical reporting must remain correct.

Processing time and event time are different.

Every order belongs to exactly one customer.

One order may have multiple payments.

One order may have multiple refunds.