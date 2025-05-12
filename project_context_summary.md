# Project Context Summary (Rella Analytics Dashboard)

**Date:** 2024-07-26

**Goal:** Develop the Profit Analytics section of the Rella Analytics dashboard using React (frontend) and Flask (backend).

**Current Focus:** Displaying accurate profitability data in the main table view.

**Current Status:**

1.  **Frontend:**
    *   Routing setup in `frontend/src/App.jsx` directs `/profitability` to `ProfitAnalyticsLayout`.
    *   The main `ProductProfitability.jsx` component fetches data from the backend `/api/v1/kpis` endpoint and displays it in a table.
    *   Placeholders exist for "Services", "Discounts", and "Trends" tabs.
    *   Visual indicators added to the `ProductProfitability.jsx` table:
        *   `*` next to "Total Sales" indicates revenue may have been reallocated by the backend heuristic (`isAdjusted=true`).
        *   `†` next to "Total Cost" indicates product cost was estimated (feature removed as we now use CSV). _(Note: The code for `†` might still be present but inactive as `isCostEstimated` is no longer set)._
    *   A legend explaining the indicators is below the table.

2.  **Backend (`backend/app.py`):**
    *   The `/api/v1/kpis` endpoint fetches detailed order data from the Boulevard API using `boulevard_client.get_boulevard_kpi_data`.
    *   **Product Costs:** Now sourced by reading `backend/Inventory On-Hand.csv`. The backend calculates unit cost (`Cost Value` / `Current Quantity`) and uses this where available. Products not in the CSV default to $0 cost. The previous logic using the API's `unitCost` and the 35% estimation fallback has been **removed**.
    *   **Service Costs:** Currently using **estimated/mock costs** defined in the `MOCK_SERVICE_COSTS_BY_URN` dictionary within `app.py`. These are often inaccurate ($0 or placeholders).
    *   **Revenue Reallocation Heuristic:** Implemented to handle specific discounting patterns (typically a $0 product line offset by a single revenue-capturing line on the same order). Adjusted sales figures are flagged (`isAdjusted=true`). Gratuity lines are excluded as revenue sources for this heuristic.
    *   **Account Credit:** `OrderAccountCreditLine` items are aggregated into a single "Account Credit Used" summary line (with $0 cost) using a generic ID (`account_credit_summary`) and are excluded from the main item profitability table view.
    *   API Rate Limiting: Retry logic with backoff is implemented in `boulevard_client.make_boulevard_request` to handle 429 errors.

**Last Steps Taken:**

1.  Refactored backend to use `Inventory On-Hand.csv` for product costs instead of API/estimation.
2.  Discussed the components needed to calculate accurate **service costs** (Direct Materials/Consumables, Direct Labor, optional Machine Usage).
3.  Confirmed that `Service Sales.csv` provides sales data but not cost data.
4.  Confirmed that `Inventory On-Hand.csv` provides product cost data but not service cost data.

**Next Steps (Action Required by User):**

1.  **Determine Service Costs:** Gather the standard **direct cost** (Consumables + Direct Labor +/- Machine Usage) for each service offered.
2.  **Provide Service Costs:** Decide how to get these costs into the system:
    *   Manually update the `MOCK_SERVICE_COSTS_BY_URN` dictionary in `backend/app.py`.
    *   Provide a new file/data source containing Service Name/ID and its corresponding cost.
    *   Opt for an estimation formula (e.g., percentage of revenue) if precise costs aren't available.

**Future Considerations:**

*   Implement frontend date range filtering.
*   Build out the other Profit Analytics tabs (Services, Discounts, Trends).
*   Refine frontend table (sorting, filtering).
*   Investigate if service costs can be obtained from any other Boulevard API endpoint (less likely based on current findings). 