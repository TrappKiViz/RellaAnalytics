// API service functions for authentication

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export async function login({ username, password }) {
  const response = await fetch(`${API_BASE_URL}/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // include cookies for session
    body: JSON.stringify({ username, password }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || 'Login failed');
  }
  return data;
}

export async function checkAuthStatus() {
  const response = await fetch(`${API_BASE_URL}/v1/auth/status`, {
    method: 'GET',
    credentials: 'include',
  });
  const contentType = response.headers.get('content-type');
  if (!response.ok) {
    return { isLoggedIn: false };
  }
  if (contentType && contentType.includes('application/json')) {
    return response.json();
  } else {
    return { isLoggedIn: false };
  }
}

export async function logout() {
  await fetch(`