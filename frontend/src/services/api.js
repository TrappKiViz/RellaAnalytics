// API service functions for authentication

export async function login({ username, password }) {
  const response = await fetch('/api/v1/auth/login', {
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
  const response = await fetch('/api/v1/auth/status', {
    method: 'GET',
    credentials: 'include',
  });
  if (!response.ok) {
    return { isLoggedIn: false };
  }
  return response.json();
}

export async function logout() {
  await fetch('/api/v1/auth/logout', {
    method: 'POST',
    credentials: 'include',
  });
} 