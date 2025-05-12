# Debug Session State — Rella Analytics

_Last updated: [fill in date/time on next session start]_

## Current Status
- **Boulevard API integration:**
  - Now uses the correct top-level `orders` query and variable names (`locationId`, `query`).
  - Backend is able to authenticate and fetch orders from Boulevard.
- **Pagination Issue:**
  - The backend is stuck in a loop, repeatedly fetching pages with `has_next_page: True`.
  - This suggests a possible bug in how the pagination cursor (`endCursor`) is handled, or the API is returning the same page/cursor repeatedly.

## Next Steps
1. **Investigate Pagination Logic:**
   - Review `get_boulevard_kpi_data` in `backend/boulevard_client.py`.
   - Add debug prints for the value of `after_cursor` on each loop.
   - Consider adding a safety limit (e.g., max 1000 orders or 50 pages) to prevent infinite loops.
2. **Test with a smaller date range** to see if the issue is data volume or logic.

## Other Context
- All API credentials are working.
- The dashboard and backend are otherwise up-to-date with the latest query structure.

---

**To resume:**
- Start by reviewing the pagination logic and recent logs.
- Reference this file for session continuity. 