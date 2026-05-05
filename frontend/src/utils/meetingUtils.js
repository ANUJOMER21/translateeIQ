export const greeting = () => {
  const h = new Date().getHours();
  if (h >= 5 && h < 12) return 'Good morning';
  if (h >= 12 && h < 17) return 'Good afternoon';
  if (h >= 17 && h < 22) return 'Good evening';
  return 'Good night';
};

export const statusPill = (status) => {
  if (status === 'completed') return 'good';
  if (status === 'error') return 'bad';
  if (['uploading', 'assembling', 'transcribing', 'analyzing', 'indexing'].includes(status)) return 'warn';
  return null;
};

export const statusLabel = (status) => {
  const map = {
    completed: 'Done',
    error: 'Failed',
    uploading: 'Uploading',
    assembling: 'Assembling',
    transcribing: 'Transcribing',
    analyzing: 'Analyzing',
    indexing: 'Indexing',
  };
  return map[status] || status;
};

export const thumbAlt = (idx) => `alt-${(idx % 5) + 1}`;

export const formatDate = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

export const formatFileSize = (bytes) => {
  if (!bytes) return '—';
  const gb = bytes / 1e9;
  if (gb >= 1) return `${gb.toFixed(1)} GB`;
  const mb = bytes / 1e6;
  if (mb >= 1) return `${mb.toFixed(0)} MB`;
  return `${(bytes / 1e3).toFixed(0)} KB`;
};

export const waveformBars = (count, seed = 0) =>
  Array.from({ length: count }, (_, i) =>
    Math.max(0.1, Math.min(1, 0.3 + Math.abs(Math.sin((i + seed) * 0.7) * 0.4 + Math.cos((i + seed) * 1.3) * 0.3)))
  );
