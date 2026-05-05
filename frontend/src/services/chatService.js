import api from './api';

export const sendMessage = (message, scope, meetingId = null) =>
  api.post('/chat/', { message, scope, meeting_id: meetingId }).then(r => r.data);
