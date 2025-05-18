---
id: sale
title: Sale
sidebar_label: Sale
---

## Definition

A **Sale** refers to the successful transaction where a customer purchases a product — either via Cash or PAYG.

## Business Logic

- For a transaction to count as a Sale:
  - The order status must be **"Confirmed"**
  - The payment must be **>= minimum deposit required**
  - Sale date = date when payment confirmed

## Source Systems

- MySQL: `orders` table
- PostgreSQL: `sales_fact` mart

## Power BI Dashboard

[View Sale Report in Power BI](https://app.powerbi.com/your-link-here)

## Notes

- If a sale is later refunded, it’s not subtracted from total sales but shown separately under "Refunds".