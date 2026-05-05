import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import useToastStore from '../store/toastStore';
import { listMeetings } from '../services/meetingService';
import { statusPill, statusLabel, thumbAlt, formatDate, waveformBars } from '../utils/meetingUtils';

const MeetingCard = ({ m, idx, onOpen }) => {
  const bars = waveformBars(40, idx);
  const coverNum = (idx % 5) + 1;
  const pill = statusPill(m.status);
  return (
    <div className="card meeting-card" onClick={() => onOpen(m.id)}>
      <div className={`meeting-card__cover meeting-card__cover--g${coverNum}`}>
        <div className="meeting-card__cover-status">
          {pill && <span className={`pill pill--${pill}`}><span className="pill__dot" />{statusLabel(m.status)}</span>}
        </div>
        <div className="meeting-card__waveform">
          {bars.map((h, i) => <div key={i} className="bar" style={{ height: `${h * 100}%` }} />)}
        </div>
      </div>
      <div className="meeting-card__body">
        <h3 className="meeting-card__title">{m.title}</h3>
        <div className="meeting-card__meta">
          <span><Icon name="calendar" size={11} style={{ marginRight: 4, verticalAlign: -1 }} />{formatDate(m.created_at)}</span>
          <span style={{ width: 3, height: 3, borderRadius: 1.5, background: 'var(--fg-3)', display: 'inline-block' }} />
          <span style={{ textTransform: 'capitalize' }}>{m.file_type || 'video'}</span>
        </div>
        <div className="meeting-card__foot">
          <div />
          <button className="btn btn--sm btn--ghost" style={{ padding: '5px 10px' }}>Open</button>
        </div>
      </div>
    </div>
  );
};

const Meetings = () => {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [view, setView] = useState('grid');
  const navigate = useNavigate();
  const toast = useToastStore(s => s.add);

  useEffect(() => {
    listMeetings()
      .then(d => setMeetings(d.results || []))
      .catch(() => toast('Failed to load meetings', 'error'))
      .finally(() => setLoading(false));
  }, []);

  const filtered = meetings.filter(m => {
    if (filter === 'all') return true;
    if (filter === 'done') return m.status === 'completed';
    if (filter === 'processing') return ['uploading', 'assembling', 'transcribing', 'analyzing', 'indexing'].includes(m.status);
    if (filter === 'failed') return m.status === 'error';
    return true;
  });

  const counts = {
    all: meetings.length,
    done: meetings.filter(m => m.status === 'completed').length,
    processing: meetings.filter(m => ['uploading', 'assembling', 'transcribing', 'analyzing', 'indexing'].includes(m.status)).length,
    failed: meetings.filter(m => m.status === 'error').length,
  };

  return (
    <Layout crumbs={['Workspace', 'Meetings']}>
      <div className="fade-up">
        <div className="page-header">
          <div>
            <h1 className="page-title">Meetings</h1>
            <p className="page-subtitle">{meetings.length} meetings · sorted by most recent</p>
          </div>
          <button className="btn btn--primary" onClick={() => navigate('/upload')}>
            <Icon name="plus" size={14} /> New meeting
          </button>
        </div>

        <div className="list-toolbar">
          <div className="tabs">
            {[['all', 'All'], ['done', 'Done'], ['processing', 'Processing'], ['failed', 'Failed']].map(([id, label]) => (
              <button key={id} className={`tab${filter === id ? ' tab--active' : ''}`} onClick={() => setFilter(id)}>
                {label} <span className="tab__count">{counts[id]}</span>
              </button>
            ))}
          </div>
          <div className="view-toggle" style={{ marginLeft: 'auto' }}>
            <button className={`view-toggle__btn${view === 'grid' ? ' view-toggle__btn--active' : ''}`} onClick={() => setView('grid')}>
              <Icon name="grid" size={14} />
            </button>
            <button className={`view-toggle__btn${view === 'list' ? ' view-toggle__btn--active' : ''}`} onClick={() => setView('list')}>
              <Icon name="list" size={14} />
            </button>
          </div>
        </div>

        {loading && (
          <div style={{ padding: 48, textAlign: 'center', color: 'var(--fg-3)' }}>
            <Icon name="loader" size={24} className="spin" />
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <div className="empty-card" style={{ marginTop: 24 }}>
            No meetings found.{' '}
            <button className="link-btn" style={{ display: 'inline' }} onClick={() => navigate('/upload')}>Upload one</button>
          </div>
        )}

        {!loading && view === 'grid' && (
          <div className="meetings-grid">
            {filtered.map((m, i) => <MeetingCard key={m.id} m={m} idx={i} onOpen={(id) => navigate(`/meetings/${id}`)} />)}
          </div>
        )}

        {!loading && view === 'list' && (
          <div className="meetings-list">
            <div className="list-row list-row--head">
              <div></div><div>Meeting</div><div>Date</div><div>Type</div><div>Status</div><div></div>
            </div>
            {filtered.map((m, i) => {
              const pill = statusPill(m.status);
              return (
                <div key={m.id} className="list-row" onClick={() => navigate(`/meetings/${m.id}`)}>
                  <div className={`meeting-row__thumb meeting-row__thumb--${thumbAlt(i)}`}>
                    <Icon name={m.file_type === 'audio' ? 'audio' : 'video'} size={16} />
                  </div>
                  <div>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--fg-0)' }}>{m.title}</div>
                    <div style={{ fontSize: 11.5, color: 'var(--fg-3)', marginTop: 2 }}>{m.original_filename}</div>
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--fg-2)' }}>{formatDate(m.created_at)}</div>
                  <div style={{ fontSize: 12, color: 'var(--fg-2)', textTransform: 'capitalize' }}>{m.file_type}</div>
                  <div>{pill && <span className={`pill pill--${pill}`}><span className="pill__dot" />{statusLabel(m.status)}</span>}</div>
                  <Icon name="arrow-right" size={14} style={{ color: 'var(--fg-3)' }} />
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Meetings;
