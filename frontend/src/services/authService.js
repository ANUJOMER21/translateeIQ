import api from './api';
import { setTokens, clearTokens } from '../utils/tokenStorage';

export const login = async (email, password) => {
  const res = await api.post('/auth/token/', { email, password });
  setTokens(res.data.access, res.data.refresh);
  return res.data;
};

export const register = async (email, password, username) => {
  const res = await api.post('/auth/register/', { email, password, username });
  return res.data;
};

export const me = async () => {
  const res = await api.get('/auth/me/');
  return res.data;
};

export const updateMe = async (data) => {
  const res = await api.patch('/auth/me/', data);
  return res.data;
};

export const logout = () => {
  clearTokens();
};
