# API Endpoint Definitions (V1) - Rella Analytics

This document outlines the initial set of proposed REST API endpoints for the backend. All endpoints are prefixed with `/api/v1`.

**Common Parameters:**
*   `location_id` (integer, optional): Filter results by location.
*   `start_date` (string, YYYY-MM-DD, optional): Start of date range filter.
*   `end_date` (string, YYYY-MM-DD, optional): End of date range filter.

## Dashboard KPIs & Summaries

*   **GET `/kpis`**
    *   **Description:** Retrieves key performance indicators for a specified period/location.
    *   **Parameters:** `location_id`, `start_date`, `end_date`.
    *   **Response:** Object containing metrics like Total Net Sales, Total Expenses, Profit, Avg Transaction Value, New Customers, Booking Conversion Rate (%), Top Selling Service/Product.

*   **GET `/sales/summary`** (Partially exists)
    *   **Description:** Retrieves summary sales data.
    *   **Parameters:** `location_id`, `start_date`, `end_date`.
    *   **Response:** Aggregated sales totals, potentially broken down by location/category (as currently mocked).

## Sales & Revenue Analysis

*   **GET `/sales/over_time`**
    *   **Description:** Retrieves net sales data aggregated by time interval (day, week, month).
    *   **Parameters:** `location_id`, `start_date`, `end_date`, `interval` (string: 'day', 'week', 'month').
    *   **Response:** Array of objects `[{date: YYYY-MM-DD, total_sales: number}]`.

*   **GET `/sales/by_category`**
    *   **Description:** Retrieves net sales broken down by treatment category.
    *   **Parameters:** `location_id`, `start_date`, `end_date`.
    *   **Response:** Array of objects `[{category_name: string, total_sales: number}]`.

*   **GET `/sales/by_service`**
    *   **Description:** Retrieves net sales broken down by individual service.
    *   **Parameters:** `location_id`, `start_date`, `end_date`, `category_id` (optional).
    *   **Response:** Array of objects `[{service_name: string, total_sales: number, quantity_sold: number}]`.

*   **GET `/sales/by_product`**
    *   **Description:** Retrieves net sales broken down by individual product.
    *   **Parameters:** `location_id`, `start_date`, `end_date`.
    *   **Response:** Array of objects `[{product_name: string, total_sales: number, quantity_sold: number}]`.

## Expense Analysis

*   **GET `/expenses/over_time`**
    *   **Description:** Retrieves total expenses aggregated by time interval.
    *   **Parameters:** `location_id`, `start_date`, `end_date`, `interval`.
    *   **Response:** Array of objects `[{date: YYYY-MM-DD, total_expenses: number}]`.

*   **GET `/expenses/by_category`**
    *   **Description:** Retrieves expenses broken down by expense category.
    *   **Parameters:** `location_id`, `start_date`, `end_date`.
    *   **Response:** Array of objects `[{category_name: string, total_expenses: number}]`.

## Employee Performance

*   **GET `/employees/performance`**
    *   **Description:** Retrieves performance metrics per employee.
    *   **Parameters:** `location_id`, `start_date`, `end_date`.
    *   **Response:** Array of objects `[{employee_id: number, employee_name: string, total_revenue_generated: number, total_bookings_completed: number, avg_transaction_value: number}]`.

## Booking & Utilization Analysis

*   **GET `/bookings/summary`**
    *   **Description:** Retrieves booking counts by status (Scheduled, Completed, Cancelled, No Show).
    *   **Parameters:** `location_id`, `start_date`, `end_date`, `employee_id` (optional), `service_id` (optional).
    *   **Response:** Object ` {scheduled: number, completed: number, cancelled: number, no_show: number}`.

*   **GET `/tools/utilization`**
    *   **Description:** Retrieves utilization metrics for service tools.
    *   **Parameters:** `location_id`, `start_date`, `end_date`.
    *   **Response:** Array of objects `[{tool_id: number, tool_name: string, total_usage_minutes: number, number_of_sessions: number, revenue_generated: number, utilization_percent: number}]` (Utilization % might require defining available hours).

## Predictive Endpoints (Future - require models)

*   **GET `/forecast/sales`** (Example)
    *   **Description:** Retrieves future sales forecast.
    *   **Parameters:** `location_id`, `forecast_period_days`.
    *   **Response:** Array of objects `[{date: YYYY-MM-DD, predicted_sales: number, lower_bound: number, upper_bound: number}]`.

*   **GET `/analysis/product_associations`** (Example)
    *   **Description:** Retrieves products frequently purchased together.
    *   **Parameters:** `location_id`, `start_date`, `end_date`, `min_support` (optional).
    *   **Response:** Array of association rules `[{antecedents: [product], consequents: [product], support: number, confidence: number}]`.

## Utility Endpoints

*   **GET `/locations`**
    *   **Description:** Retrieves list of available locations.
*   **GET `/treatment_categories`**
    *   **Description:** Retrieves list of treatment categories.
*   **GET `/services`**
    *   **Description:** Retrieves list of services (potentially filter by category).
*   **GET `/products`**
    *   **Description:** Retrieves list of products.
*   **GET `/employees`**
    *   **Description:** Retrieves list of employees (potentially filter by location/role). 