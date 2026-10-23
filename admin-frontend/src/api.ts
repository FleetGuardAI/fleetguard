import axios from 'axios';

function resolveAdminBaseUrl(): string {
  const envUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
  if (envUrl) {
    const cleaned = envUrl.replace(/\/+$/, '');
    if (cleaned.endsWith('/admin')) {
      return cleaned;
    }
    if (cleaned.endsWith('/api/v1')) {
      return `${cleaned}/admin`;
    }
    if (cleaned.endsWith('/api')) {
      return `${cleaned}/v1/admin`;
    }
    return `${cleaned}/api/v1/admin`;
  }
  return import.meta.env.PROD
    ? "https://fleetguard-hpip.onrender.com/api/v1/admin"
    : "http://localhost:8000/api/v1/admin";
}

const api = axios.create({
  baseURL: resolveAdminBaseUrl(),
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("[SUPER ADMIN API ERROR]", {
      status: error.response?.status,
      data: error.response?.data,
      url: error.config?.url,
      baseURL: error.config?.baseURL,
    });
    return Promise.reject(error);
  }
);

export function getApiErrorMessage(error: any): string {
  if (error?.response?.data) {
    const data = error.response.data;
    if (typeof data === "string") return data;
    if (data.detail) {
      if (typeof data.detail === "string") return data.detail;
      if (Array.isArray(data.detail)) {
        return data.detail.map((item: any) => {
          if (typeof item === "string") return item;
          if (item.loc) return `${item.loc.join('.')}: ${item.msg}`;
          return item.msg || item.message || JSON.stringify(item);
        }).join(", ");
      }
      return JSON.stringify(data.detail);
    }
    if (data.message) {
      return typeof data.message === "string" ? data.message : JSON.stringify(data.message);
    }
    return JSON.stringify(data);
  }
  if (error?.message) {
    return error.message;
  }
  return "An unexpected error occurred.";
}

export default api;
