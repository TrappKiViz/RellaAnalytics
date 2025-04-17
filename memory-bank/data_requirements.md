# Data Requirements for Advanced Analytics

This document outlines the specific data formats and fields required to enable the planned advanced analytics features, such as time series forecasting and association rule mining, within the Rella Analytics Platform.

The current `Product Sales.csv` dataset provides valuable aggregate information but lacks the granularity needed for these specific modeling techniques.

## 1. Time Series Forecasting (e.g., Sales Prediction)

**Goal:** Predict future sales trends (overall, per location, per product).

**Required Data:**

*   **Timestamp:** A specific date (e.g., `YYYY-MM-DD`) or date-time for each sales record or aggregation period (e.g., daily, weekly sales totals).
*   **Metric:** The value to be forecasted (e.g., `Net Retail Product Sales`, `Product Quantity Sold`).
*   **Dimensions (Optional but Recommended):** Fields to segment the forecast (e.g., `Location name`, `Product name`).

**Current Limitation (`Product Sales.csv`):** Lacks a date/timestamp column. The data represents quarterly totals, preventing analysis of trends *within* the quarter.

**Example Required Format (Daily Sales):**

| Date       | Location Name | Product Name       | Daily Sales | Daily Quantity |
| :--------- | :------------ | :----------------- | ----------: | -------------: |
| 2024-01-01 | Napa          | Botox              |     1500.00 |            150 |
| 2024-01-01 | Vacaville     | Tirzepatide 1x Month |      725.00 |              1 |
| 2024-01-02 | Napa          | Botox              |     1200.00 |            120 |
| ...        | ...           | ...                |         ... |            ... |

## 2. Association Rule Mining (e.g., Market Basket Analysis)

**Goal:** Identify which products or services are frequently purchased together within the same transaction.

**Required Data:**

*   **Transaction Identifier:** A unique ID for each distinct customer purchase/transaction.
*   **Item Identifier:** The name or ID of the product/service purchased in that transaction.

**Current Limitation (`Product Sales.csv`):** Lacks a transaction identifier. The data aggregates sales per product over the quarter, making it impossible to know which products were bought *together* by a single customer at one time.

**Example Required Format:**

| Transaction ID | Item Name                 |
| :------------- | :------------------------ |
| T1001          | Botox                     |
| T1001          | Juvederm Ultra XC         |
| T1002          | Semaglutide x1 Month Supply |
| T1003          | Tinted Defense            |
| T1003          | Lipid Cloud               |
| ...            | ...                       |

## Summary

To enable robust predictive modeling and deeper insights as outlined in the project brief, access to more granular data containing **specific dates/timestamps** and **unique transaction identifiers** is essential. 