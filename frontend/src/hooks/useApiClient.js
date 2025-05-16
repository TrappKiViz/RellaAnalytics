import { useCallback } from 'react';

// Basic API client hook using fetch
const useApiClient = () => {
  // GET request
  const get = useCallback(async (url, params = {}) => {
    // Add query parameters to URL if provided
    const queryString = Object.keys(params).length 
      ? '?' + new URLSearchParams(params).toString() 
      : '';
    
    const fullUrl = `${url}${queryString}`;
    console.log(`[API Client] Making GET request to: ${fullUrl}`);
    
    try {
      const response = await fetch(fullUrl, {
        method: 'GET',
        credentials: 'include', // include cookies for auth if needed
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      console.log(`[API Client] Response status: ${response.status}`);
      
      if (!response.ok) {
        // Try to get error details from response
        let errorDetail = 'Unknown error';
        try {
          const errorData = await response.json();
          errorDetail = errorData.message || errorData.error || `HTTP error! status: ${response.status}`;
        } catch (e) {
          errorDetail = `HTTP error! status: ${response.status}`;
        }
        
        console.error(`[API Client] Request failed: ${errorDetail}`);
        throw new Error(errorDetail);
      }
      
      const data = await response.json();
      console.log(`[API Client] Request successful`);
      return data;
    } catch (error) {
      console.error(`[API Client] Request error: ${error.message}`);
      throw error;
    }
  }, []);

  // You can add more methods (post, put, delete) as needed

  return { get };
};

export default useApiClient; 