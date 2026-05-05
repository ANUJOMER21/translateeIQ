import axios from 'axios';

const base = import.meta.env.VITE_API_URL || '/api';

export const getPublicMeeting = async (token) => {
  const res = await axios.get(`${base}/public/${token}/`);
  return res.data;
};
