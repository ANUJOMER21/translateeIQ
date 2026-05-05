import { useState, useRef, useCallback } from 'react';
import { initUpload, uploadChunk, completeUpload, getProgress, CHUNK_SIZE } from '../services/uploadService';

const useUpload = () => {
  const [state, setState] = useState({ phase: 'idle', pct: 0, meetingId: null, sessionId: null, error: null });
  const pollRef = useRef(null);

  const stopPoll = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };

  const startPoll = (sessionId) => {
    pollRef.current = setInterval(async () => {
      try {
        const data = await getProgress(sessionId);
        setState(s => ({ ...s, pct: data.overall_progress, phase: data.stage === 'completed' ? 'done' : data.stage === 'error' ? 'error' : 'processing', error: data.error || null }));
        if (data.stage === 'completed' || data.stage === 'error') stopPoll();
      } catch { /* ignore transient errors */ }
    }, 3000);
  };

  const upload = useCallback(async (file, meetingTitle) => {
    setState({ phase: 'uploading', pct: 0, meetingId: null, sessionId: null, error: null });
    try {
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
      const { session_id, meeting_id } = await initUpload(file.name, file.size, totalChunks, meetingTitle);
      setState(s => ({ ...s, sessionId: session_id, meetingId: meeting_id }));

      for (let i = 0; i < totalChunks; i++) {
        const chunk = file.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE);
        await uploadChunk(session_id, i, chunk);
        setState(s => ({ ...s, pct: Math.round(((i + 1) / totalChunks) * 40) }));
      }

      await completeUpload(session_id);
      setState(s => ({ ...s, phase: 'processing', pct: 40 }));
      startPoll(session_id);
      return { sessionId: session_id, meetingId: meeting_id };
    } catch (err) {
      stopPoll();
      setState(s => ({ ...s, phase: 'error', error: err.response?.data?.error || err.message }));
      throw err;
    }
  }, []);

  const reset = useCallback(() => { stopPoll(); setState({ phase: 'idle', pct: 0, meetingId: null, sessionId: null, error: null }); }, []);

  return { ...state, upload, reset };
};

export default useUpload;
