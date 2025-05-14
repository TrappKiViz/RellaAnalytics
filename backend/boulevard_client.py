import os
import requests
import time
import hmac
import hashlib
import base64
import json
import re
from datetime import datetime, timezone, timedelta

# Import cache object from the new extensions module
from extensions import cache
from boulevard_queries import ORDER_DETAILS_QUERY, LOCATIONS_QUERY

BOULEVARD_API_URL = "https://dashboard.boulevard.io/api/2020-01/admin"

def _generate_http_basic_auth():
    # Fetch environment variables INSIDE the function
    print("Fetching Boulevard API credentials...")
    BOULEVARD_API_KEY = os.getenv('BOULEVARD_API_KEY')
    BOULEVARD_API_SECRET = os.getenv('BOULEVARD_SECRET')
    BOULEVARD_BUSINESS_ID = os.getenv('BOULEVARD_BUSINESS_ID')

    print(f"API Key exists: {bool(BOULEVARD_API_KEY)}")
    print(f"API Secret exists: {bool(BOULEVARD_API_SECRET)}")
    print(f"Business ID exists: {bool(BOULEVARD_BUSINESS_ID)}")

    if not all([BOULEVARD_API_KEY, BOULEVARD_API_SECRET, BOULEVARD_BUSINESS_ID]):
        raise ValueError("Missing Boulevard API Key, Secret, or Business ID in environment variables.")

    prefix = "blvd-admin-v1"
    timestamp = str(int(time.time()))
    token_payload = f"{prefix}{BOULEVARD_BUSINESS_ID}{timestamp}"
    print("Generated token payload")
    
    try:
        raw_key = base64.b64decode(BOULEVARD_API_SECRET)
        print("Successfully decoded API secret")
    except Exception as e:
        print(f"Failed to decode API secret: {e}")
        raise ValueError(f"Failed to Base64 decode BOULEVARD_SECRET: {e}")
    
    raw_mac = hmac.new(
        raw_key,
        token_payload.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(raw_mac).decode('utf-8')
    print("Generated signature")

    token = f"{signature}{token_payload}"
    print("Generated final token")
    
    http_basic_payload = f"{BOULEVARD_API_KEY}:{token}"
    http_basic_credentials_bytes = http_basic_payload.encode('utf-8')
    http_basic_credentials = base64.b64encode(http_basic_credentials_bytes).decode('utf-8')
    print("Generated HTTP basic auth credentials")
    
    return f"Basic {http_basic_credentials}"

def make_boulevard_request(query, variables=None, max_retries=4, initial_delay=1.5):
    """Makes a request to the Boulevard API with retry logic for rate limiting."""
    # Check is implicitly done by _generate_http_basic_auth now
    # if not BOULEVARD_API_KEY or not BOULEVARD_API_SECRET or not BOULEVARD_BUSINESS_ID:
    #     raise ValueError("API Key, Secret, or Business ID not configured in environment variables.")
        
    auth_header = _generate_http_basic_auth() # This will raise ValueError if keys are missing
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    request_body_dict = {'query': query}
    if variables:
        request_body_dict['variables'] = variables
    request_body_str = json.dumps(request_body_dict)

    retries = 0
    delay = initial_delay
    last_exception = None

    while retries < max_retries:
        try:
            response = requests.post(
                url=BOULEVARD_API_URL,
                headers=headers,
                data=request_body_str,
                timeout=30 # Add a timeout
            )
            response.raise_for_status() # Raises HTTPError for 4xx/5xx responses

            if response.status_code == 204:
                return None
            
            response_data = response.json()
            # Check for GraphQL errors within a successful HTTP response
            if 'errors' in response_data:
                print(f"GraphQL errors received: {response_data['errors']}")
                # Decide if GraphQL errors should also be retried? For now, return them.
                # Potentially check error content for rate limit messages here too?
                return response_data 
                
            return response_data # Success!

        except requests.exceptions.HTTPError as e:
            last_exception = e
            if e.response.status_code == 429:
                retries += 1
                wait_time = delay # Default wait time
                try:
                    # Attempt to parse suggested wait time from body
                    error_body = e.response.json()
                    message = error_body.get('errors', [{}])[0].get('message', '')
                    match = re.search(r'Please wait (\d+\.?\d*)ms', message)
                    if match:
                        wait_time_ms = float(match.group(1))
                        wait_time = max(wait_time_ms / 1000.0, 0.1) # Convert ms to s, ensure minimum wait
                        print(f"Rate limit hit (429). Retrying in {wait_time:.2f} seconds... (Attempt {retries}/{max_retries})")
                    else:
                        print(f"Rate limit hit (429), but couldn't parse wait time. Retrying in {wait_time:.2f} seconds... (Attempt {retries}/{max_retries})")
                except Exception as parse_error:
                    print(f"Rate limit hit (429), error parsing wait time ({parse_error}). Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})")
                
                time.sleep(wait_time)
                delay = min(delay * 2, 30) # Exponential backoff, cap at 30 seconds
            else:
                # For other HTTP errors (4xx, 5xx), don't retry, just raise
                print(f"HTTP error making Boulevard API request: {e}")
                raise e 
        except requests.exceptions.RequestException as e:
            # For connection errors, timeouts, etc.
            last_exception = e
            retries += 1
            print(f"Network error making Boulevard API request: {e}. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(delay)
            delay = min(delay * 2, 30) # Exponential backoff, cap at 30 seconds
        except Exception as e:
             # Catch any other unexpected errors during the request
             print(f"Unexpected error during Boulevard API request: {e}")
             last_exception = e
             raise e # Re-raise unexpected errors immediately

    # If loop finishes without success
    print(f"API request failed after {max_retries} retries.")
    if last_exception:
         raise last_exception # Re-raise the last encountered exception
    else:
         # Should not happen if logic is correct, but as a fallback
         raise Exception("API request failed after multiple retries for an unknown reason.") 

def get_boulevard_locations():
    """Fetches all locations from Boulevard API."""
    response = make_boulevard_request(LOCATIONS_QUERY)
    return response

def get_historical_orders(location_id, days_history=30):
    """Fetches historical orders for a location within the specified timeframe."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_history)
    
    # Format dates for Boulevard API
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    filter_str = f"closedAt >= '{start_str}' AND closedAt <= '{end_str}'"
    print(f"--- Attempting Paginated Order Details Query (with cost) for location {location_id} with QueryString: {filter_str} ---")
    
    variables = {
        "locationId": location_id,
        "filter": filter_str
    }
    
    response = make_boulevard_request(ORDER_DETAILS_QUERY, variables)
    
    if response and 'data' in response and 'location' in response['data']:
        location_data = response['data']['location']
        if 'orders' in location_data and 'edges' in location_data['orders']:
            return [edge['node'] for edge in location_data['orders']['edges']]
    
    return []

# --- Helper function for pagination (RESTORED) ---
def _fetch_all_pages(query, variables):
    all_nodes = []
    has_next_page = True
    after_cursor = None

    while has_next_page:
        variables['after'] = after_cursor
        try:
            response = make_boulevard_request(query=query, variables=variables)
            if response is None or 'errors' in response or 'data' not in response:
                error_detail = response.get('errors', 'Unknown API error') if response else 'No response'
                print(f"Error during pagination: {error_detail}")
                break

            connection_key = next((k for k in response['data'] if not k.startswith('__')), None)
            if not connection_key or not response['data'][connection_key]:
                 print("Error: Could not find connection key in response data during pagination.")
                 break
            
            connection = response['data'][connection_key]
            
            if 'edges' in connection and connection['edges']:
                all_nodes.extend([edge['node'] for edge in connection['edges'] if edge and 'node' in edge])

            if 'pageInfo' in connection:
                page_info = connection['pageInfo']
                has_next_page = page_info.get('hasNextPage', False)
                after_cursor = page_info.get('endCursor')
            else:
                has_next_page = False 

            if has_next_page and not after_cursor:
                print("Warning: hasNextPage is true but no endCursor found. Stopping pagination.")
                has_next_page = False
                
        except Exception as e:
            print(f"Exception during pagination: {e}")
            break 

    return all_nodes

# --- Updated Function for KPI Data (Fetches Order Details for Profitability) ---
@cache.cached(key_prefix='kpi_data') 
def get_boulevard_kpi_data(location_id, query_string=None): 
    """Fetches order details with cost information from Boulevard API using the top-level orders query."""
    if not query_string:
        query_string = "closedAt >= '2025-03-01T00:00:00Z' AND closedAt <= '2025-04-25T23:59:59Z'"

    # Use the updated top-level orders query
    query = ORDER_DETAILS_QUERY

    variables = {
        "locationId": location_id,
        "query": query_string
    }
    variables = {k: v for k, v in variables.items() if v is not None}

    print(f"--- Attempting Paginated Order Details Query (with cost) for location {location_id} with QueryString: {query_string} ---")
    try:
        all_orders = []
        has_next_page = True
        after_cursor = None
        page_count = 0
        max_pages = 50
        max_orders = 1000

        while has_next_page:
            current_vars = variables.copy()
            if after_cursor:
                current_vars['after'] = after_cursor
            print(f"[DEBUG] Pagination loop: page {page_count+1}, after_cursor={after_cursor}")
            response = make_boulevard_request(query=query, variables=current_vars)

            if response is None or 'errors' in response or 'data' not in response:
                error_detail = response.get('errors', 'Unknown API error') if response else 'No response'
                print(f"Error during pagination: {error_detail}")
                break

            # Parse the new top-level orders structure
            orders_data = response['data'].get('orders')
            if not orders_data:
                print("Error: Could not find orders data in response during pagination.")
                break

            edges = orders_data.get('edges', [])
            for edge in edges:
                if edge and 'node' in edge:
                    all_orders.append(edge['node'])

            page_info = orders_data.get('pageInfo', {})
            has_next_page = page_info.get('hasNextPage', False)
            after_cursor = page_info.get('endCursor') if has_next_page else None

            print(f"Fetched {len(edges)} orders on page {page_count+1}. Has next page: {has_next_page}. Total orders so far: {len(all_orders)}")
            page_count += 1

            # Safety limits
            if page_count >= max_pages:
                print(f"[SAFETY] Reached max page limit ({max_pages}). Stopping pagination.")
                break
            if len(all_orders) >= max_orders:
                print(f"[SAFETY] Reached max order limit ({max_orders}). Stopping pagination.")
                break

            # Extra: If has_next_page is True but after_cursor is None, stop to avoid infinite loop
            if has_next_page and not after_cursor:
                print("Warning: hasNextPage is true but no endCursor found. Stopping pagination.")
                has_next_page = False

        print(f"Total orders fetched: {len(all_orders)} (pages: {page_count})")
        return all_orders

    except Exception as e:
        print(f"Failed order details query (with cost) for location {location_id}: {e}")
        return None

@cache.cached(key_prefix='historical_orders')
def get_historical_orders(location_id, days_history=365):
    """Fetches all orders for a location going back a specified number of days."""
    
    # Calculate start date for history
    start_date = datetime.now(timezone.utc) - timedelta(days=days_history)
    start_date_str = start_date.strftime('%Y-%m-%d')
    
    # Construct QueryString for the historical date range
    # Uses closedAt field, adjust if needed (e.g., createdAt)
    start_iso = f"{start_date_str}T00:00:00Z"
    query_string = f"closedAt >= '{start_iso}'" # Only need lower bound

    # Re-use the same GraphQL query structure as get_boulevard_kpi_data
    query = """
    query GetOrders(
        $first: Int,
        $after: String,
        $locationId: ID!,
        $query: QueryString
    ) {
      orders(
          first: $first,
          after: $after,
          locationId: $locationId,
          query: $query
        ) {
        pageInfo { 
          hasNextPage
          endCursor
        }
        edges {
          node {
            id
            closedAt
            summary {
              currentSubtotal
            }
            lineGroups {
              lines { 
                __typename
                id
                quantity
                currentSubtotal 
                currentDiscountAmount
                
                ... on OrderProductLine {
                  productId
                  name
                }
                ... on OrderServiceLine {
                  serviceId
                  name
                }
              }
            }
          }
        }
      }
    }
    """

    # Prepare variables
    variables = {
        "first": 100, 
        "locationId": location_id,
        "query": query_string
    }
    variables = {k: v for k, v in variables.items() if v is not None} # Clean nulls

    print(f"--- Attempting HISTORICAL Orders Query for location {location_id} ({days_history} days) ---")
    try:
        # Use pagination helper 
        all_order_nodes = _fetch_all_pages(query, variables)
        print(f"--- Fetched {len(all_order_nodes)} historical orders for location {location_id} (FROM API) ---") # Indicate non-cached
        return all_order_nodes
    except Exception as e:
        print(f"Failed historical orders query for location {location_id}: {e}")
        return None

# --- NEW: Function to fetch costs for multiple products --- 
@cache.cached(key_prefix='product_costs', make_cache_key=lambda *args, **kwargs: tuple(sorted(args[0])) if args else ()) 
def get_boulevard_product_costs(product_ids):
    """Fetches unitCost for a list of product IDs using a single batch query."""
    if not product_ids:
        return {}

    # Build the query dynamically using aliases
    query_body = ""
    variables = {}
    for i, pid in enumerate(product_ids):
        alias = f"prod{i}"
        var_name = f"id{i}"
        query_body += f"  {alias}: product(id: ${var_name}) {{ id unitCost }}\n"
        variables[var_name] = pid
        
    query_params_def = ", ".join([f"${k}: ID!" for k in variables.keys()])
    full_query = f"query GetMultipleProductCosts({query_params_def}) {{\n{query_body}}}\n"

    print(f"--- Attempting Batch Product Cost Query for {len(product_ids)} products ---")
    try:
        response = make_boulevard_request(query=full_query, variables=variables)
        
        if response is None or 'errors' in response or 'data' not in response:
            error_detail = response.get('errors', 'API call failed') if response else 'No response'
            print(f"Error fetching batch product costs: {error_detail}")
            return None # Indicate failure

        # Process the response data into a product_id -> cost_cents dictionary
        costs = {}
        for i, pid in enumerate(product_ids):
            alias = f"prod{i}"
            product_data = response['data'].get(alias)
            if product_data and isinstance(product_data, dict):
                cost_cents = product_data.get('unitCost')
                if cost_cents is not None: # Assuming Money scalar returns the int directly
                    costs[pid] = cost_cents
                else:
                     print(f"Warning: unitCost not found for product {pid} in batch response.")
            else:
                 print(f"Warning: Product data not found for alias {alias} (ID: {pid}) in batch response.")
                 
        print(f"--- Successfully fetched costs for {len(costs)} out of {len(product_ids)} products (FROM API) ---") # Indicate non-cached
        return costs

    except Exception as e:
        print(f"Failed batch product cost query: {e}")
        return None # Indicate failure

# Add functions for other endpoints: get_transactions, get_services, etc.
