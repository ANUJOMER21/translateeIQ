import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import useAuthStore from '../store/authStore';
import useToastStore from '../store/toastStore';
import { getDashboard, getTrendingTopics } from '../services/dashboardService';
import { getActionItems, toggleActionItem } from '../services/actionItemsService';
import { greeting, statusPill, statusLabel, thumbAlt, formatDate, waveformBars } from '../utils/meetingUtils';

const Waveform = ({ count = 24, height = 64 }) => {
  const bars = waveformBars(count);
  return (
    <div style={{ display: 'flex', alignItems: 'end', gap: 4, height, padding: '0 4px', flexShrink: 0 }}>
      {bars.map((h, i) => (
        <div key={i} className="viz-bar" style={{ height: `${h * 100}%`, opacity: 0.35 + (i / bars.length) * 0.65 }} />
      ))}
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuthStore();
  const toast = useToastStore(s => s.add);
  const navigate = useNavigate();

  const [dash, setDash] = useState(null);
  const [actions, setActions] = useState([]);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);

  const displayName = user?.username || user?.email?.split('@')[0] || 'there';

  useEffect(() => {
    Promise.all([getDashboard(), getActionItems(), getTrendingTopics()])
      .then(([d, a, t]) => { setDash(d); setActions(a); setTopics(t); })
      .catch(() => toast('Failed to load dashboard', 'error'))
      .finally(() => setLoading(false));
  }, []);

  const handleToggle = async (id) => {
    try {
      const updated = await toggleActionItem(id);
      setActions(prev => prev.map(a => a.id === id ? { ...a, is_done: updated.is_done } : a));
    } catch { toast('Failed to update action item', 'error'); }
  };

  const stats = dash?.stats;
  const recent = dash?.recent_meetings || [];

  return (
    <Layout crumbs={['Workspace', 'Dashboard']}>
      <div className="fade-up">
        {/* Hero banner */}
        <div className="hero-banner">
          <div className="hero-banner__row">
            <div>
              <div className="hero-banner__greeting">
                {stats?.active_uploads > 0 && <><span className="live-dot" /> Live · {stats.active_uploads} active upload{stats.active_uploads > 1 ? 's' : ''} processing</>}
                {(!stats || stats.active_uploads === 0) && <><span style={{ fontSize: 16 }}>☀️</span> {greeting()}</>}
              </div>
              <h1 className="hero-banner__title">{greeting()}, {displayName}</h1>
              <p className="hero-banner__sub">
                {stats && (
                  <>
                    You have <b style={{ color: 'var(--fg-0)' }}>{stats.new_transcripts} new transcript{stats.new_transcripts !== 1 ? 's' : ''}</b> ready to review
                    {stats.open_action_items > 0 && <> and <b style={{ color: 'var(--fg-0)' }}>{stats.open_action_items} action item{stats.open_action_items !== 1 ? 's' : ''}</b> assigned to you across this week's meetings.</>}
                  </>
                )}
                {!stats && 'Loading your workspace…'}
              </p>
              <div className="hero-banner__actions">
                <button className="btn btn--primary" onClick={() => navigate('/upload')}>
                  <Icon name="upload" size={15} /> Upload recording
                </button>
                <button className="btn btn--ghost" onClick={() => navigate('/assistant')}>
                  <Icon name="sparkles" size={15} /> Ask AI
                </button>
              </div>
            </div>
            <Waveform />
          </div>
        </div>

        {/* Stats */}
        <div className="stats-grid">
          {[
            { icon: 'video', color: 'accent', label: 'Total meetings', value: stats?.total ?? '—', unit: '' },
            { icon: 'check-circle', color: 'good', label: 'Completed', value: stats?.completed ?? '—', unit: '' },
            { icon: 'loader', color: 'warn', label: 'Processing', value: stats?.processing ?? '—', unit: '', spin: true },
            { icon: 'trend-up', color: 'info', label: 'Hours saved', value: stats?.hours_saved ?? '—', unit: 'h' },
          ].map(s => (
            <div key={s.label} className="card stat-card">
              <div className="stat-card__icon" style={{ background: `var(--${s.color}-soft)`, color: `var(--${s.color})` }}>
                <Icon name={s.icon} size={18} className={s.spin && stats?.processing > 0 ? 'spin' : ''} />
              </div>
              <div className="stat-card__value">{s.value}{s.unit && <span className="stat-card__unit">{s.unit}</span>}</div>
              <div className="stat-card__label"><span>{s.label}</span></div>
            </div>
          ))}
        </div>

        {/* Two-col grid */}
        <div className="dash-grid">
          {/* Recent meetings */}
          <div>
            <div className="section-head">
              <h2 className="section-title">Recent meetings</h2>
              <button className="link-btn" onClick={() => navigate('/meetings')}>
                View all <Icon name="arrow-right" size={13} />
              </button>
            </div>
            <div className="card" style={{ padding: 8 }}>
              {loading && (
                <div style={{ padding: 24, textAlign: 'center', color: 'var(--fg-3)' }}>
                  <Icon name="loader" size={18} className="spin" />
                </div>
              )}
              {!loading && recent.length === 0 && (
                <div className="empty-card">No meetings yet. <button className="link-btn" style={{ display: 'inline' }} onClick={() => navigate('/upload')}>Upload one</button></div>
              )}
              {recent.map((m, i) => {
                const pill = statusPill(m.status);
                return (
                  <div className="meeting-row" key={m.id} onClick={() => navigate(`/meetings/${m.id}`)}>
                    <div className={`meeting-row__thumb meeting-row__thumb--${thumbAlt(i)}`}>
                      <Icon name={m.file_type === 'audio' ? 'audio' : 'video'} size={16} />
                    </div>
                    <div style={{ minWidth: 0 }}>
                      <div className="meeting-row__title">{m.title}</div>
                      <div className="meeting-row__meta">
                        <Icon name="calendar" size={11} /> {formatDate(m.created_at)}
                      </div>
                    </div>
                    <div />
                    {pill && <span className={`pill pill--${pill}`}><span className="pill__dot" />{statusLabel(m.status)}</span>}
                    <Icon name="arrow-right" size={14} style={{ color: 'var(--fg-3)' }} />
                  </div>
                );
              })}
            </div>
          </div>

          {/* Insights sidebar */}
          <div className="insights">
            {/* Action items */}
            <div className="card insight-card">
              <div className="insight-card__head">
                <div style={{ width: 28, height: 28, borderRadius: 7, background: 'var(--accent-soft)', color: 'var(--accent)', display: 'grid', placeItems: 'center' }}>
                  <Icon name="check" size={14} />
                </div>
                <h3 className="insight-card__title">Your action items</h3>
                <span className="pill pill--accent" style={{ marginLeft: 'auto' }}>
                  {actions.filter(a => !a.is_done).length} open
                </span>
              </div>
              {loading && <div style={{ color: 'var(--fg-3)', fontSize: 13, padding: '8px 0' }}>Loading…</div>}
              {!loading && actions.length === 0 && (
                <div style={{ color: 'var(--fg-3)', fontSize: 13, padding: '8px 0' }}>No action items yet.</div>
              )}
              {actions.slice(0, 5).map(a => (
                <div key={a.id} className={`action-item${a.is_done ? ' action-item--done' : ''}`}>
                  <div className="action-item__check" onClick={() => handleToggle(a.id)}>
                    {a.is_done && <Icon name="check" size={11} />}
                  </div>
                  <div className="action-item__text">
                    {a.task}
                    <div className="action-item__meta">
                      {a.owner && <><Icon name="user" size={10} /> {a.owner}</>}
                      {a.due_date && <><span style={{ width: 2, height: 2, borderRadius: 1, background: 'var(--fg-3)', display: 'inline-block' }} /><Icon name="clock" size={10} /> {a.due_date}</>}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Trending topics */}
            <div className="card insight-card">
              <div className="insight-card__head">
                <div style={{ width: 28, height: 28, borderRadius: 7, background: 'var(--info-soft)', color: 'var(--info)', display: 'grid', placeItems: 'center' }}>
                  <Icon name="lightbulb" size={14} />
                </div>
                <h3 className="insight-card__title">Trending topics this week</h3>
              </div>
              {!loading && topics.length === 0 && (
                <div style={{ color: 'var(--fg-3)', fontSize: 13 }}>No topics yet — process more meetings.</div>
              )}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {topics.map(t => (
                  <span key={t.topic} className="pill" style={{ background: 'var(--bg-2)' }}>
                    {t.topic}
                    <span style={{ color: 'var(--fg-3)', fontFamily: 'var(--font-mono)', fontSize: 10 }}>×{t.count}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
