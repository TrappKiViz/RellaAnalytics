// Central place for API calls

const API_BASE_URL = 'http://localhost:5001/api/v1'; // Ensure this matches backend

/**
 * Helper function to handle fetch responses
 * @param {Response} response - The fetch response object
 * @returns {Promise<any>} - Parsed JSON data
 * @throws {Error} - If response is not ok
 */
const handleResponse = async (response) => {
  if (!response.ok) {
    let errorData = {};
    try {
      errorData = await response.json(); // Try to parse error details
    } catch (e) {
      // If response is not JSON (e.g., HTML error page), use status text
      errorData.message = response.statusText || `HTTP error! status: ${response.status}`;
    }
    throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
  }
  // For 204 No Content or other non-JSON success responses
  if (response.status === 204) {
    return null; 
  }
  return response.json();
};

// Helper for making authenticated requests
const fetchAuthenticated = async (url, options = {}) => {
    // Ensure credentials are included for session cookies
    const defaultOptions = {
        credentials: 'include', 
        headers: {
            'Content-Type': 'application/json',
            ...options.headers, 
        },
        ...options, // Merge other options like method, body
    };
    const response = await fetch(url, defaultOptions);
    return handleResponse(response);
};

/**
 * Fetches the sales summary data.
 */
export const getSalesSummary = async () => {
  const response = await fetch(`${API_BASE_URL}/sales/summary`);
  return handleResponse(response);
};

/**
 * Fetches the list of locations.
 */
export const getLocations = async () => {
  return fetchAuthenticated(`${API_BASE_URL}/locations`);
};

/**
 * Fetches the list of products.
 */
export const getProducts = async () => {
  const response = await fetch(`${API_BASE_URL}/products`);
  return handleResponse(response);
};

/**
 * Fetches the list of services.
 */
export const getServices = async () => {
  const response = await fetch(`${API_BASE_URL}/services`);
  return handleResponse(response);
};

/**
 * Fetches KPI data.
 * @param {object} filters - Optional filters (e.g., { location_id: 1 })
 */
export const getKPIs = async (filters = {}) => {
  const query = new URLSearchParams(filters).toString();
  return fetchAuthenticated(`${API_BASE_URL}/kpis?${query}`);
};

/**
 * Fetches sales aggregated by category.
 * @param {object} filters - Optional filters (e.g., { location_id: 1 })
 */
export const getSalesByCategory = async (filters = {}) => {
  const query = new URLSearchParams(filters).toString();
  return fetchAuthenticated(`${API_BASE_URL}/sales/by_category?${query}`);
};

/**
 * Fetches sales aggregated over time.
 * @param {object} filters - Optional filters (e.g., { location_id: 1 })
 */
export const getSalesOverTime = async (filters = {}) => {
  // TODO: Add params for date range, interval etc.
  const query = new URLSearchParams(filters).toString();
  const response = await fetch(`${API_BASE_URL}/sales/over_time?${query}`);
  return handleResponse(response);
};

/**
 * Fetches sales forecast data.
 * @param {object} filters - Optional filters (e.g., { location_id: 1, start_date: '...', end_date: '...', days: 30 })
 */
export const getSalesForecast = async (filters = {}) => {
  const query = new URLSearchParams(filters).toString();
  return fetchAuthenticated(`${API_BASE_URL}/sales/forecast?${query}`);
};

// Add more functions here as new endpoints are implemented
// Example:
// export const getSalesOverTime = async (params) => {
//   const query = new URLSearchParams(params).toString();
//   const response = await fetch(`${API_BASE_URL}/sales/over_time?${query}`);
//   return handleResponse(response);
// }; 

// --- Authentication --- 
export const login = async (credentials) => {
  // Login doesn't need fetchAuthenticated initially, but subsequent calls will
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
      credentials: 'include'
  });
  return handleResponse(response);
};

export const logout = async () => {
  return fetchAuthenticated(`${API_BASE_URL}/auth/logout`, { method: 'POST' });
};

export const checkAuthStatus = async () => {
  return fetchAuthenticated(`${API_BASE_URL}/auth/status`);
};

// --- Customer Data ---
export const getCustomerLocations = async () => {
    // Fetches customer coordinates for the density map
    return fetchAuthenticated(`${API_BASE_URL}/customers/locations`);
};

// --- NEW: Get Profit by Category ---
export const getProfitByCategory = async (filters = {}) => {
  const queryParams = new URLSearchParams();
  if (filters.location_id && filters.location_id !== 'all') {
    queryParams.append('location_id', filters.location_id);
  }
  if (filters.start_date) {
    queryParams.append('start_date', filters.start_date);
  }
  if (filters.end_date) {
    queryParams.append('end_date', filters.end_date);
  }
  
  // --- Use API_BASE_URL and fetchAuthenticated ---
  const fullUrl = `${API_BASE_URL}/profit/by_category?${queryParams.toString()}`;
  return fetchAuthenticated(fullUrl, { method: 'GET' });

  /* OLD CODE:
  const url = `/api/v1/profit/by_category?${queryParams.toString()}`;
  
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return handleResponse(response);
  */
};

// --- Data Upload Functions ---
export const validateTransactionFile = async (formData) => {
// ... existing code ...

  return handleResponse(response);
}; 