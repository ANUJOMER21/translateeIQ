import api from './api';

export const getDashboard = () => api.get('/dashboard/').then(r => r.data);
export const getTrendingTopics = () => api.get('/trending-topics/').then(r => r.data);
