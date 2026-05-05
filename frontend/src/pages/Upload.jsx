import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import useToastStore from '../store/toastStore';
import useUpload from '../hooks/useUpload';

const ACCEPTED = '.mp4,.mov,.avi,.mkv,.webm,.m4v,.mp3,.wav,.m4a,.flac,.aac,.ogg';
const FORMATS = ['MP4', 'MOV', 'AVI', 'MKV', 'MP3', 'WAV', 'M4A', 'FLAC'];

const Upload = () => {
  const navigate = useNavigate();
  const toast = useToastStore(s => s.add);
  const fileRef = useRef(null);
  const [hover, setHover] = useState(false);
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const { phase, pct, meetingId, error, upload, reset } = useUpload();

  const handleFile = (f) => {
    if (!f) return;
    setFile(f);
    if (!title) setTitle(f.name.replace(/\.[^.]+$/, ''));
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setHover(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleStart = async () => {
    if (!file) return;
    try {
      const { meetingId: mid } = await upload(file, title || file.name.replace(/\.[^.]+$/, ''));
      toast('Upload complete! Processing in background.', 'success');
      setTimeout(() => navigate(`/meetings/${mid}`), 1200);
    } catch {
      toast(error || 'Upload failed', 'error');
    }
  };

  const isIdle = phase === 'idle';
  const isUploading = phase === 'uploading';
  const isProcessing = phase === 'processing';
  const isDone = phase === 'done';
  const isError = phase === 'error';
  const inProgress = isUploading || isProcessing;

  return (
    <Layout crumbs={['Workspace', 'Upload']}>
      <div className="upload-page fade-up">
        <div className="page-header" style={{ display: 'block' }}>
          <h1 className="page-title">Upload meeting</h1>
          <p className="page-subtitle">Drop a recording — we'll transcribe, identify speakers, and surface the highlights.</p>
        </div>

        {(isIdle || isError) && !file && (
          <>
            <div
              className={`dropzone${hover ? ' dropzone--hover' : ''}`}
              onDragEnter={() => setHover(true)}
              onDragLeave={() => setHover(false)}
              onDragOver={e => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileRef.current?.click()}
            >
              <div className="dropzone__icons">
                <div className="dropzone__icon"><Icon name="film" size={22} /></div>
                <div className="dropzone__icon"><Icon name="upload" size={22} /></div>
                <div className="dropzone__icon"><Icon name="audio" size={22} /></div>
              </div>
              <h3 className="dropzone__title">Drag &amp; drop your meeting file</h3>
              <p className="dropzone__sub">or click to browse — up to 4 GB per file</p>
              <button className="btn btn--primary" type="button"><Icon name="upload" size={14} /> Choose file</button>
              <div style={{ marginTop: 24 }}>
                <div style={{ fontSize: 11, color: 'var(--fg-3)', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 8 }}>Supported formats</div>
                <div className="format-row">
                  {FORMATS.map(f => <span key={f} className="format-tag">{f}</span>)}
                </div>
              </div>
            </div>
            <input ref={fileRef} type="file" accept={ACCEPTED} style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
          </>
        )}

        {(isIdle || isError) && file && (
          <div className="card" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 18 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--accent-soft)', color: 'var(--accent)', display: 'grid', placeItems: 'center' }}>
                <Icon name="film" size={22} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, color: 'var(--fg-0)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.name}</div>
                <div style={{ fontSize: 12, color: 'var(--fg-3)', marginTop: 2 }}>{(file.size / 1e6).toFixed(1)} MB</div>
              </div>
              <button className="btn btn--ghost btn--sm" onClick={() => { setFile(null); reset(); }}>
                <Icon name="x" size={13} /> Remove
              </button>
            </div>
            <div className="input-group">
              <label className="input-label">Meeting title</label>
              <input className="input" value={title} onChange={e => setTitle(e.target.value)} placeholder="e.g. Q2 Planning Sync" />
            </div>
            {isError && <div style={{ padding: '10px 14px', background: 'var(--bad-soft)', borderRadius: 'var(--r-2)', color: 'var(--bad)', fontSize: 13 }}>{error}</div>}
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn--primary" onClick={handleStart}>
                <Icon name="upload" size={14} /> Start upload
              </button>
              <button className="btn btn--ghost" onClick={() => { setFile(null); reset(); }}>Cancel</button>
            </div>
          </div>
        )}

        {inProgress && (
          <div className="card" style={{ padding: 28, display: 'flex', flexDirection: 'column', gap: 20, alignItems: 'center', textAlign: 'center' }}>
            <div style={{ width: 56, height: 56, borderRadius: 14, background: 'var(--accent-soft)', color: 'var(--accent)', display: 'grid', placeItems: 'center' }}>
              <Icon name="loader" size={26} className="spin" />
            </div>
            <div>
              <div style={{ fontWeight: 600, color: 'var(--fg-0)', fontSize: 16, marginBottom: 4 }}>
                {isUploading ? 'Uploading…' : 'Processing…'}
              </div>
              <div style={{ color: 'var(--fg-2)', fontSize: 13 }}>
                {isUploading ? 'Sending chunks to server' : 'Transcribing and analyzing'}
              </div>
            </div>
            <div style={{ width: '100%', maxWidth: 360 }}>
              <div style={{ height: 6, borderRadius: 3, background: 'var(--bg-3)', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${pct}%`, background: 'var(--accent)', borderRadius: 3, transition: 'width 0.5s ease' }} />
              </div>
              <div style={{ marginTop: 6, fontSize: 12, color: 'var(--fg-3)', textAlign: 'right' }}>{pct.toFixed(0)}%</div>
            </div>
          </div>
        )}

        {isDone && (
          <div className="card" style={{ padding: 28, textAlign: 'center' }}>
            <div style={{ color: 'var(--good)', marginBottom: 12 }}><Icon name="check-circle" size={40} /></div>
            <div style={{ fontWeight: 600, color: 'var(--fg-0)', fontSize: 16, marginBottom: 4 }}>Processing complete!</div>
            <div style={{ color: 'var(--fg-2)', fontSize: 13, marginBottom: 20 }}>Your meeting is ready to view.</div>
            <button className="btn btn--primary" onClick={() => navigate(`/meetings/${meetingId}`)}>
              Open meeting <Icon name="arrow-right" size={14} />
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Upload;
