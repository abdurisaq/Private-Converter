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

export async function fetchWrapper(endpoint, options = {}) {
  const authHeaders = getAuthHeaders();

  // Merge headers
  options.headers = {
    ...authHeaders,
    ...options.headers,
  };

  console.log('Request URL:', API_URL + endpoint);
  console.log('Request options:', options);

  const response = await fetch(API_URL + endpoint, options);

  console.log('Response status:', response.status);
  console.log('Response headers:', Array.from(response.headers.entries()));

  // Clone response so we can read it for logging without consuming the body
  const clone = response.clone();
  let responseText;
  try {
    responseText = await clone.text();
    console.log('Raw response body:', responseText);
  } catch (err) {
    console.warn('Failed to read response body:', err);
  }

  const contentType = response.headers.get('content-type');

  if (!response.ok) {
    let errorMessage = 'Request failed';
    if (contentType && contentType.includes('application/json')) {
      try {
        const errorData = JSON.parse(responseText);
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        errorMessage = `Request failed (invalid JSON): ${responseText}`;
      }
    }
    throw new Error(errorMessage);
  }

  if (contentType && contentType.includes('application/octet-stream')) {
    return response.blob();
  }

  if (contentType && contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
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

export const conversionApi = {
  getFormats: () =>
    fetchWrapper('/conversions/formats/'),

  upload: (file, inputFormat, outputFormat) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('inputFormat', inputFormat);
    formData.append('outputFormat', outputFormat);

    return fetchWrapper('/conversions/upload/', {
      method: 'POST',
      body: formData,
    });
  },

  getStatus: (jobId) =>
    fetchWrapper(`/jobs/${jobId}/`),

  listJobs: (params) =>
    fetchWrapper('/jobs/', { params }),

  downloadResult: (jobId) =>
    fetchWrapper(`/jobs/${jobId}/download/`, {
      responseType: 'blob',
    }),

  cancelJob: (jobId) =>
    fetchWrapper(`/jobs/${jobId}/cancel/`, {
      method: 'POST',
    }),
};

export default fetchWrapper;
