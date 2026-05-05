import axios from 'axios';
import { getAccess, getRefresh, setTokens, clearTokens } from '../utils/tokenStorage';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({ baseURL: BASE });

api.interceptors.request.use((cfg) => {
  const token = getAccess();
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

let refreshing = null;

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const orig = err.config;
    if (err.response?.status === 401 && !orig._retry) {
      orig._retry = true;
      if (!refreshing) {
        refreshing = axios
          .post(`${BASE}/auth/token/refresh/`, { refresh: getRefresh() })
          .then((r) => {
            setTokens(r.data.access, r.data.refresh);
            refreshing = null;
          })
          .catch(() => {
            clearTokens();
            refreshing = null;
            window.location.href = '/login';
          });
      }
      await refreshing;
      orig.headers.Authorization = `Bearer ${getAccess()}`;
      return api(orig);
    }
    return Promise.reject(err);
  }
);

export default api;
