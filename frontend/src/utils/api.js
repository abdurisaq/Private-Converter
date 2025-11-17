import { useAuthStore } from '../utils/authStore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function getAuthHeaders() {
  const { access } = useAuthStore.getState();
  return access ? { Authorization: `Bearer ${access}` } : {};
}

async function handleResponse(response) {
  if (response.status === 401) {
    useAuthStore.getState().logout();
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || errorData.message || 'Request failed';
    return Promise.reject(new Error(message));
  }

  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/octet-stream')) {
    return response.blob();
  }

  return response.json();
}

async function fetchWrapper(endpoint, options = {}) {
  const headers = {
    ...getAuthHeaders(),
    ...options.headers,
  };

  const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
  return handleResponse(response);
}

export const authApi = {
  login: (email, password) =>
    fetchWrapper('/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }),

  register: (email, password) =>
    fetchWrapper('/auth/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, password2: password }),
    }),

  me: () => fetchWrapper('/auth/me/'),
};

export default fetchWrapper;
