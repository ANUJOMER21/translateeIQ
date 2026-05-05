import api from './api';

export const listMeetings = (page = 1) => api.get('/meetings/', { params: { page } }).then(r => r.data);
export const getMeeting = (id) => api.get(`/meetings/${id}/`).then(r => r.data);
export const updateMeeting = (id, data) => api.patch(`/meetings/${id}/`, data).then(r => r.data);
export const deleteMeeting = (id) => api.delete(`/meetings/${id}/`);
export const getTranscript = (id) => api.get(`/meetings/${id}/transcript/`).then(r => r.data);
export const getSummary = (id) => api.get(`/meetings/${id}/summary/`).then(r => r.data);
export const getMOM = (id) => api.get(`/meetings/${id}/mom/`).then(r => r.data);
