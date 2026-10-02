import axios from 'axios';

const API_ROOT =
  import.meta.env.PROD
    ? "https://fleetguard-hpip.onrender.com/api/v1"
    : (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1");

const api = axios.create({
  baseURL: `${API_ROOT}/admin`,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  console.log("[SUPER ADMIN API]", {
    method: config.method,
    baseURL: config.baseURL,
    url: config.url,
    fullURL: `${config.baseURL}${config.url || ""}`,
  });

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
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('admin_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
