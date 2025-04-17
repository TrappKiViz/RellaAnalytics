import os
import requests
import time
import hmac
import hashlib
import base64
import json
from datetime import datetime, timezone

# Load credentials from environment variables
BOULEVARD_API_KEY = os.getenv('BOULEVARD_API_KEY')
BOULEVARD_SECRET = os.getenv('BOULEVARD_SECRET')
BOULEVARD_BUSINESS_ID = os.getenv('BOULEVARD_BUSINESS_ID')
# BOULEVARD_APP_ID = os.getenv('BOULEVARD_APP_ID') # App ID not used in this auth scheme

# Use the Sandbox GraphQL Endpoint URL
BOULEVARD_API_URL = "https://sandbox.joinblvd.com/api/2020-01/admin"

def _generate_http_basic_auth():
    """Generates the HTTP Basic Auth header with HMAC signature.
    Based on Boulevard Admin API Authentication documentation.
    """
    if not all([BOULEVARD_API_KEY, BOULEVARD_SECRET, BOULEVARD_BUSINESS_ID]):
        raise ValueError("Missing Boulevard API Key, Secret, or Business ID in environment variables.")

    # 1. Generate token payload
    prefix = "blvd-admin-v1"
    # Strip the URN prefix from the Business ID if present
    # business_id_short = BOULEVARD_BUSINESS_ID.split(':')[-1] 
    # Use the full Business ID directly as suggested by support feedback
    timestamp = str(int(time.time()))
    token_payload = f"{prefix}{BOULEVARD_BUSINESS_ID}{timestamp}"
    
    # 2. Sign the payload
    try:
        # Decode the Base64 secret key provided by Boulevard
        raw_key = base64.b64decode(BOULEVARD_SECRET)
    except Exception as e:
        raise ValueError(f"Failed to Base64 decode BOULEVARD_SECRET: {e}")
    
    raw_mac = hmac.new(
        raw_key,
        token_payload.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(raw_mac).decode('utf-8')

    # Concatenate signature and payload for the token
    token = f"{signature}{token_payload}"
    
    # 3. Create HTTP Basic Credentials
    http_basic_payload = f"{BOULEVARD_API_KEY}:{token}"
    http_basic_credentials_bytes = http_basic_payload.encode('utf-8')
    http_basic_credentials = base64.b64encode(http_basic_credentials_bytes).decode('utf-8')
    
    # --- DEBUG PRINTS --- 
    print(f"\n--- Auth Header Generation ---")
    print(f"Using Business ID: {BOULEVARD_BUSINESS_ID}")
    print(f"Timestamp: {timestamp}")
    print(f"Token Payload (Signed): {token_payload}")
    print(f"Signature (Base64): {signature}")
    print(f"Token (Sig+Payload): {token[:10]}...{token[-10:]}")
    print(f"HTTP Basic Payload (API_KEY:Token): {BOULEVARD_API_KEY[:5]}...:{token[:10]}...{token[-10:]}")
    print(f"Final Basic Creds (Base64): {http_basic_credentials[:10]}...{http_basic_credentials[-10:]}\n")
    # --- END DEBUG PRINTS ---

    return f"Basic {http_basic_credentials}"

def make_boulevard_request(query, variables=None):
    """Makes an authenticated GraphQL request to the Boulevard API using custom Basic Auth."""
    
    auth_header = _generate_http_basic_auth()
    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    request_body_dict = {'query': query}
    if variables:
        request_body_dict['variables'] = variables
    request_body_str = json.dumps(request_body_dict)

    # print(f"Making GraphQL request to: {BOULEVARD_API_URL}") # DEBUG
    # print(f"Using Auth Header: {auth_header[:10]}...{auth_header[-10:]}") # DEBUG
    try:
        response = requests.post(
            url=BOULEVARD_API_URL,
            headers=headers,
            data=request_body_str
        )
        response.raise_for_status()

        if response.status_code == 204:
            return None
        
        response_data = response.json()
        if 'errors' in response_data:
            print(f"GraphQL errors received: {response_data['errors']}")
            return response_data 
            
        return response_data

    except requests.exceptions.RequestException as e:
        print(f"Error making Boulevard API request to {BOULEVARD_API_URL}: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            try:
                print(f"Response body: {e.response.text}")
            except Exception: pass
        raise

# --- Example Functions (Using GraphQL) --- 

def get_boulevard_locations():
    """Fetches locations (businesses) from Boulevard using GraphQL."""
    query = """
    query GetBusinesses {
      businesses(first: 10) {
        edges {
          node {
            id
            name
            locations(first: 5) {
              edges {
                node {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    print(f"Attempting to fetch locations from Boulevard via GraphQL...") # DEBUG
    try:
        return make_boulevard_request(query=query, variables=None)
    except Exception as e:
        print(f"Failed to get locations from Boulevard: {e}")
        return None

# Add functions for other endpoints: get_transactions, get_services, etc.