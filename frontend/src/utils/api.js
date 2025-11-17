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
  try {
    const response = await fetch(API_URL + endpoint, options);

    if (!response.ok) {
      // Handle cases where backend returns HTML or text on error
      const contentType = response.headers.get("Content-Type") || "";

      if (!contentType.includes("application/json")) {
        console.warn(`Non-JSON response at ${endpoint}: returning null`);
        return null;
      }
    }

    return await response.json();

  } catch (error) {
    console.error("Fetch failed:", error);
    return null;
  }
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
    fetchWrapper('/conversions/formats'),

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
