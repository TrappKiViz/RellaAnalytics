import { useCallback } from 'react';

// Basic API client hook using fetch
const useApiClient = () => {
  // GET request
  const get = useCallback(async (url, options = {}) => {
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include', // include cookies for auth if needed
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
    }
    return response.json();
  }, []);

  // You can add more methods (post, put, delete) as needed

  return { get };
};

export default useApiClient; 