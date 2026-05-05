import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import Icon from '../components/Icon';
import MediaPlayer from '../components/MediaPlayer';
import { getPublicMeeting } from '../services/publicMeetingService';

const formatDate = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
};

const fmtDur = (raw) => {
  if (!raw) return null;
  const n = parseFloat(raw);
  if (!isFinite(n)) return raw;
  const h = Math.floor(n / 3600), m = Math.floor((n % 3600) / 60), s = Math.floor(n % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
};

const SectionTitle = ({ icon, label, color }) => (
  <div style={{
    display: 'flex', alignItems: 'center', gap: 6,
    marginBottom: 12, fontSize: 11, fontWeight: 700,
    textTransform: 'uppercase', letterSpacing: '0.07em',
    color: color || 'var(--fg-3)',
  }}>
    <Icon name={icon} size={12} />
    {label}
  </div>
);

const PublicMeetingDetail = () => {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('transcript');

  useEffect(() => {
    getPublicMeeting(token)
      .then(setData)
      .catch(() => setError('This link is invalid or the meeting is not yet available.'));
  }, [token]);

  if (error) return (
    <div className="pub-shell pub-shell--center">
      <div style={{ textAlign: 'center', maxWidth: 380, padding: 24 }}>
        <div style={{
          width: 52, height: 52, borderRadius: '50%',
          background: 'var(--bad-soft)', display: 'grid', placeItems: 'center',
          margin: '0 auto 16px',
        }}>
          <Icon name="info" size={22} style={{ color: 'var(--bad)' }} />
        </div>
        <h2 style={{ margin: '0 0 8px', color: 'var(--fg-0)', fontSize: 18 }}>Link not found</h2>
        <p style={{ margin: 0, color: 'var(--fg-2)', fontSize: 13.5, lineHeight: 1.6 }}>{error}</p>
      </div>
    </div>
  );

  if (!data) return (
    <div className="pub-shell pub-shell--center">
      <div style={{ textAlign: 'center' }}>
        <Icon name="loader" size={28} className="spin" style={{ color: 'var(--accent)', marginBottom: 12 }} />
        <p style={{ color: 'var(--fg-2)', margin: 0, fontSize: 13 }}>Loading meeting…</p>
      </div>
    </div>
  );

  const { title, file_type, duration, created_at, original_filename, playback_url, transcript, summary, mom } = data;

  return (
    <div className="pub-shell">
      {/* ── Nav ── */}
      <header className="pub-nav">
        <a className="pub-nav__brand" href="/login" title="Open TranslateeIQ app">
          <div className="pub-nav__mark">
            <Icon name="zap" size={13} style={{ color: 'var(--accent-fg)' }} />
          </div>
          <span className="pub-nav__name">translatee<b style={{ color: 'var(--accent)' }}>IQ</b></span>
        </a>
        <span className="pub-nav__badge">
          <Icon name="doc" size={11} /> Shared · read only
        </span>
      </header>

      {/* ── Content ── */}
      <main className="pub-content">

        {/* Hero */}
        <div className="pub-hero">
          <div className="pub-hero__type">
            <Icon name={file_type === 'audio' ? 'audio' : 'film'} size={12} />
            {file_type === 'audio' ? 'Audio recording' : 'Video recording'}
          </div>
          <h1 className="pub-hero__title">{title}</h1>
          <div className="pub-hero__meta">
            <span><Icon name="calendar" size={12} />{formatDate(created_at)}</span>
            {fmtDur(duration) && <span><Icon name="loader" size={12} />{fmtDur(duration)}</span>}
            <span><Icon name="doc" size={12} />{original_filename}</span>
          </div>
        </div>

        {/* Media player */}
        {playback_url && (
          <div className="card" style={{ padding: 20, marginBottom: 0 }}>
            <SectionTitle icon={file_type === 'audio' ? 'audio' : 'film'} label={file_type === 'audio' ? 'Audio Playback' : 'Video Playback'} />
            <MediaPlayer url={playback_url} fileType={file_type} />
          </div>
        )}

        {/* Tabs */}
        <div className="pub-tabs">
          {[['transcript', 'Transcript'], ['summary', 'Summary'], ['mom', 'Minutes']].map(([tid, label]) => (
            <button
              key={tid}
              className={`pub-tab${tab === tid ? ' pub-tab--active' : ''}`}
              onClick={() => setTab(tid)}
            >
              {label}
            </button>
          ))}
        </div>

        {/* ── Transcript ── */}
        {tab === 'transcript' && (
          <div>
            {!transcript && <p style={{ color: 'var(--fg-3)', fontSize: 13 }}>No transcript available.</p>}
            {transcript?.segments?.map((seg, i) => (
              <div key={i} className="transcript-line">
                <div className="transcript-line__time">{seg.start_time || ''}</div>
                <div className="transcript-line__body">
                  <div className="transcript-line__head">
                    <div className={`avatar avatar--sm bg-speaker-${(i % 5) + 1}`} style={{ color: 'oklch(0.18 0.020 60)' }}>
                      {(seg.speaker || 'S')[0]}
                    </div>
                    <div className={`transcript-line__speaker speaker-${(i % 5) + 1}`}>{seg.speaker || `Speaker ${i + 1}`}</div>
                  </div>
                  <div className="transcript-line__text">{seg.text}</div>
                </div>
              </div>
            ))}
            {transcript && !transcript.segments?.length && (
              <pre style={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', lineHeight: 1.6, margin: 0, color: 'var(--fg-1)', fontSize: 13.5 }}>
                {transcript.raw_text || 'No transcript available.'}
              </pre>
            )}
          </div>
        )}

        {/* ── Summary ── */}
        {tab === 'summary' && (
          <div className="summary">
            {!summary && <div className="card summary-card summary-card--full" style={{ color: 'var(--fg-3)' }}>No summary available.</div>}
            {summary && <>
              {(summary.tldr || summary.raw_text) && (
                <div className="card summary-card summary-card--full">
                  <div className="summary-card__head">
                    <div className="summary-card__icon"><Icon name="doc" size={14} /></div>
                    <h3 className="summary-card__title">TL;DR</h3>
                  </div>
                  <p style={{ margin: 0, fontSize: 14, color: 'var(--fg-1)', lineHeight: 1.65 }}>{summary.tldr || summary.raw_text}</p>
                </div>
              )}
              {summary.bullet_points?.length > 0 && (
                <div className="card summary-card summary-card--full">
                  <div className="summary-card__head">
                    <div className="summary-card__icon" style={{ background: 'var(--accent-soft)', color: 'var(--accent)' }}><Icon name="lightbulb" size={14} /></div>
                    <h3 className="summary-card__title">Key points</h3>
                  </div>
                  <ul className="summary-card__list">{summary.bullet_points.map((k, i) => <li key={i}>{k}</li>)}</ul>
                </div>
              )}
              {summary.decisions?.length > 0 && (
                <div className="card summary-card">
                  <div className="summary-card__head">
                    <div className="summary-card__icon" style={{ background: 'var(--good-soft)', color: 'var(--good)' }}><Icon name="check" size={14} /></div>
                    <h3 className="summary-card__title">Decisions</h3>
                  </div>
                  <ul className="summary-card__list">{summary.decisions.map((d, i) => <li key={i}>{d}</li>)}</ul>
                </div>
              )}
              {summary.action_items?.length > 0 && (
                <div className="card summary-card">
                  <div className="summary-card__head">
                    <div className="summary-card__icon" style={{ background: 'var(--info-soft)', color: 'var(--info)' }}><Icon name="flag" size={14} /></div>
                    <h3 className="summary-card__title">Action items</h3>
                  </div>
                  <ul className="summary-card__list">
                    {summary.action_items.map((a, i) => (
                      <li key={i}>{typeof a === 'string' ? a : `${a.task}${a.owner ? ` · ${a.owner}` : ''}${a.due_date ? ` · due ${a.due_date}` : ''}`}</li>
                    ))}
                  </ul>
                </div>
              )}
              {summary.topics?.length > 0 && (
                <div className="card summary-card summary-card--full">
                  <div className="summary-card__head">
                    <div className="summary-card__icon" style={{ background: 'var(--warn-soft)', color: 'var(--warn)' }}><Icon name="sparkles" size={14} /></div>
                    <h3 className="summary-card__title">Topics</h3>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
                    {summary.topics.map((t, i) => <span key={i} className="pill">{t}</span>)}
                  </div>
                </div>
              )}
            </>}
          </div>
        )}

        {/* ── MOM ── */}
        {tab === 'mom' && (
          <div className="mom-doc">
            {!mom && <p style={{ color: 'var(--fg-3)', fontSize: 13 }}>No minutes available.</p>}
            {mom && (
              (mom.attendees?.length || mom.agenda?.length || mom.discussion || mom.decisions?.length || mom.action_items?.length || mom.notes?.length)
                ? <>
                    {mom.attendees?.length > 0 && (
                      <div className="mom-section">
                        <div className="mom-section__title"><Icon name="user" size={13} /> Attendees</div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {mom.attendees.map((a, i) => <span key={i} className="pill">{a}</span>)}
                        </div>
                      </div>
                    )}
                    {mom.agenda?.length > 0 && (
                      <div className="mom-section">
                        <div className="mom-section__title"><Icon name="doc" size={13} /> Agenda</div>
                        <ol className="mom-list">{mom.agenda.map((a, i) => <li key={i}>{a}</li>)}</ol>
                      </div>
                    )}
                    {mom.discussion && (
                      <div className="mom-section">
                        <div className="mom-section__title"><Icon name="sparkles" size={13} /> Discussion</div>
                        <p style={{ margin: 0, fontSize: 13.5, color: 'var(--fg-1)', lineHeight: 1.7, whiteSpace: 'pre-wrap' }}>{mom.discussion}</p>
                      </div>
                    )}
                    {mom.decisions?.length > 0 && (
                      <div className="mom-section">
                        <div className="mom-section__title"><Icon name="check" size={13} /> Decisions</div>
                        <ul className="mom-list">{mom.decisions.map((d, i) => <li key={i}>{d}</li>)}</ul>
                      </div>
                    )}
                    {mom.action_items?.length > 0 && (
                      <div className="mom-section">
                        <div className="mom-section__title"><Icon name="flag" size={13} /> Action Items</div>
                        <ul className="mom-list">
                          {mom.action_items.map((a, i) => (
                            <li key={i}>{typeof a === 'string' ? a : `${a.task}${a.owner ? ` · ${a.owner}` : ''}${a.due_date ? ` · due ${a.due_date}` : ''}`}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {mom.notes?.length > 0 && (
                      <div className="mom-section">
                        <div className="mom-section__title"><Icon name="info" size={13} /> Notes</div>
                        <ul className="mom-list">{mom.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
                      </div>
                    )}
                  </>
                : <pre style={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', lineHeight: 1.65, margin: 0, color: 'var(--fg-1)', fontSize: 13.5 }}>
                    {mom.raw_text || mom.content || JSON.stringify(mom, null, 2)}
                  </pre>
            )}
          </div>
        )}

        <div className="pub-footer">
          Powered by <span style={{ color: 'var(--accent)', fontWeight: 700 }}>TranslateeIQ</span>
        </div>
      </main>
    </div>
  );
};

export default PublicMeetingDetail;
