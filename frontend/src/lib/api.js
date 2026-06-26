import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API_BASE = `${BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_BASE,
});

// Attach token from localStorage as Bearer (in addition to cookie)
api.interceptors.request.use((config) => {
  const t = localStorage.getItem("af_token");
  if (t) config.headers.Authorization = `Bearer ${t}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && window.location.pathname !== "/login") {
      localStorage.removeItem("af_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  },
);

export default api;
