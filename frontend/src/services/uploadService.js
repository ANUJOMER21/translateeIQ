import api from './api';

const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB

export const initUpload = (filename, fileSize, totalChunks, meetingTitle) =>
  api.post('/upload/init/', { filename, file_size: fileSize, total_chunks: totalChunks, meeting_title: meetingTitle }).then(r => r.data);

export const uploadChunk = (sessionId, chunkIndex, chunk) => {
  const form = new FormData();
  form.append('session_id', sessionId);
  form.append('chunk_index', chunkIndex);
  form.append('chunk', chunk);
  return api.post('/upload/chunk/', form).then(r => r.data);
};

export const completeUpload = (sessionId) =>
  api.post('/upload/complete/', { session_id: sessionId }).then(r => r.data);

export const getProgress = (sessionId) =>
  api.get(`/upload/${sessionId}/progress/`).then(r => r.data);

export { CHUNK_SIZE };
