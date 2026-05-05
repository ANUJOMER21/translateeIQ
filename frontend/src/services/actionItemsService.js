import api from './api';

export const getActionItems = () => api.get('/action-items/').then(r => r.data);
export const toggleActionItem = (id) => api.patch(`/action-items/${id}/`).then(r => r.data);
