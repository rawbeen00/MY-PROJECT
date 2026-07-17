import axios from "axios";

export const BACKEND_URL =
 "https://ansary-invoice-api.onrender.com";

export const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
});

// Attach token from localStorage
api.interceptors.request.use((config) => {
  const t = localStorage.getItem("af_token");
  if (t) {
    config.headers.Authorization = `Bearer ${t}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (err) => {
    if (
      err.response?.status === 401 &&
      window.location.pathname !== "/login"
    ) {
      localStorage.removeItem("af_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;