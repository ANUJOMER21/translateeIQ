import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import MediaPlayer from '../components/MediaPlayer';
import useToastStore from '../store/toastStore';
import { getMeeting, getTranscript, getSummary, getMOM, deleteMeeting } from '../services/meetingService';
import { statusLabel, formatDate } from '../utils/meetingUtils';
import api from '../services/api';

/* ── Pipeline steps ─────────────────────────────────────────── */
const STEPS = [
  { key: 'uploading',    icon: 'upload',    label: 'Upload',     eta: '1–3 min'  },
  { key: 'assembling',   icon: 'doc',       label: 'Assemble',   eta: '~30 sec'  },
  { key: 'transcribing', icon: 'audio',     label: 'Transcribe', eta: '2–8 min'  },
  { key: 'analyzing',    icon: 'sparkles',  label: 'Analyze',    eta: '1–2 min'  },
  { key: 'indexing',     icon: 'search',    label: 'Index',      eta: '~30 sec'  },
  { key: 'completed',    icon: 'check',     label: 'Done',       eta: null       },
];

const STEP_ORDER = STEPS.map(s => s.key);

const stepIndex = (status) => {
  const i = STEP_ORDER.indexOf(status);
  return i === -1 ? 0 : i;
};

const PROCESSING = ['uploading', 'assembling', 'transcribing', 'analyzing', 'indexing'];

/* ── Helpers ─────────────────────────────────────────────────── */
const fmtDur = (raw) => {
  if (!raw) return null;
  const n = parseFloat(raw);
  if (!isFinite(n)) return raw;
  const h = Math.floor(n / 3600), m = Math.floor((n % 3600) / 60), s = Math.floor(n % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
};

/* ── Stepper component ───────────────────────────────────────── */
const Stepper = ({ status, processingStep }) => {
  const current = stepIndex(status);
  const isError = status === 'error';

  return (
    <div className="stepper">
      {STEPS.map((step, i) => {
        const done    = !isError && i < current;
        const active  = !isError && i === current;
        const error   = isError && i === current - 1;

        return (
          <div key={step.key} className="stepper__item">
            {i > 0 && (
              <div className={`stepper__line${done || (active && i <= current) ? ' stepper__line--done' : ''}`} />
            )}
            <div className={`stepper__dot${done ? ' stepper__dot--done' : active ? ' stepper__dot--active' : error ? ' stepper__dot--error' : ''}`}>
              {done
                ? <Icon name="check" size={11} />
                : active
                  ? <span className="stepper__spinner" />
                  : error
                    ? <Icon name="info" size={11} />
                    : <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--fg-3)' }}>{i + 1}</span>
              }
            </div>
            <div className="stepper__label">
              <span className={`stepper__label-text${done ? ' stepper__label-text--done' : active ? ' stepper__label-text--active' : ''}`}>
                {step.label}
              </span>
              {active && processingStep
                ? <span className="stepper__sub">{processingStep.replace(/_/g, ' ')}</span>
                : !done && step.eta && (
                  <span className="stepper__eta">{active ? `est. ${step.eta}` : step.eta}</span>
                )
              }
            </div>
          </div>
        );
      })}
    </div>
  );
};

/* ── Main page ───────────────────────────────────────────────── */
const MeetingDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToastStore(s => s.add);

  const [meeting, setMeeting] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [summary, setSummary] = useState(null);
  const [mom, setMom] = useState(null);
  const [tab, setTab] = useState('transcript');
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);

  const isProcessing = meeting && PROCESSING.includes(meeting.status);

  // Initial fetch
  useEffect(() => {
    getMeeting(id)
      .then(m => {
        setMeeting(m);
        setLoading(false);
        if (m.status === 'completed') loadContent(m.id);
      })
      .catch(() => { toast('Meeting not found', 'error'); navigate('/meetings'); });
  }, [id]);

  const loadContent = (mid) => {
    getTranscript(mid).then(setTranscript).catch(() => {});
    getSummary(mid).then(setSummary).catch(() => {});
    getMOM(mid).then(setMom).catch(() => {});
  };

  // Poll while processing
  useEffect(() => {
    if (!isProcessing) return;
    const t = setInterval(() => {
      getMeeting(id)
        .then(m => {
          setMeeting(m);
          if (m.status === 'completed') {
            loadContent(m.id);
            setTab('transcript');
          }
        })
        .catch(() => {});
    }, 4000);
    return () => clearInterval(t);
  }, [isProcessing, id]);

  const handleDelete = async () => {
    if (!confirm(`Delete "${meeting?.title}"? This cannot be undone.`)) return;
    setDeleting(true);
    try {
      await deleteMeeting(id);
      toast('Meeting deleted', 'success');
      navigate('/meetings');
    } catch { toast('Failed to delete', 'error'); setDeleting(false); }
  };

  const handlePdf = async () => {
    setPdfLoading(true);
    try {
      const res = await api.get(`/meetings/${id}/pdf/`, { responseType: 'blob' });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement('a');
      a.href = url; a.download = `meeting-${id}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch { toast('PDF download failed', 'error'); }
    finally { setPdfLoading(false); }
  };

  if (loading) return (
    <Layout crumbs={['Meetings', '…']}>
      <div style={{ padding: 64, textAlign: 'center' }}>
        <Icon name="loader" size={24} className="spin" style={{ color: 'var(--accent)' }} />
      </div>
    </Layout>
  );

  const completed = meeting.status === 'completed';
  const isError   = meeting.status === 'error';

  return (
    <Layout crumbs={['Meetings', meeting.title]}>
      <div className="fade-up meeting-detail-page">

        {/* ── Top bar ── */}
        <div className="detail-head">
          <button className="back-link" onClick={() => navigate('/meetings')}>
            <Icon name="back" size={14} /> Meetings
          </button>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button className="btn btn--ghost btn--sm" onClick={() => navigate(`/assistant?meeting=${id}`)}>
              <Icon name="sparkles" size={13} /> Chat with AI
            </button>
            <button className="btn btn--ghost btn--sm" onClick={handleDelete} disabled={deleting}>
              <Icon name="trash" size={13} /> {deleting ? 'Deleting…' : 'Delete'}
            </button>
          </div>
        </div>

        {/* ── Hero card ── */}
        <div className="meeting-hero card">
          <div className="meeting-hero__left">
            <div className="meeting-hero__type-badge">
              <Icon name={meeting.file_type === 'audio' ? 'audio' : 'film'} size={13} />
              {meeting.file_type === 'audio' ? 'Audio' : 'Video'}
            </div>
            <h1 className="meeting-hero__title">{meeting.title}</h1>
            <div className="meeting-hero__meta">
              <span><Icon name="calendar" size={12} /> {formatDate(meeting.created_at)}</span>
              {fmtDur(meeting.duration) && <span><Icon name="loader" size={12} /> {fmtDur(meeting.duration)}</span>}
              <span><Icon name="doc" size={12} /> {meeting.original_filename}</span>
              {meeting.file_size > 0 && (
                <span style={{ color: 'var(--fg-3)' }}>
                  {meeting.file_size > 1e9
                    ? `${(meeting.file_size / 1e9).toFixed(1)} GB`
                    : `${(meeting.file_size / 1e6).toFixed(1)} MB`}
                </span>
              )}
            </div>

            {/* Status badge */}
            <div style={{ marginTop: 12 }}>
              {completed && (
                <span className="status-badge status-badge--done">
                  <span className="status-badge__dot" /> Completed
                </span>
              )}
              {isProcessing && (
                <span className="status-badge status-badge--processing">
                  <Icon name="loader" size={11} className="spin" /> {statusLabel(meeting.status)}
                  {meeting.processing_step && (
                    <span style={{ color: 'var(--fg-2)', marginLeft: 6, fontWeight: 400 }}>
                      · {meeting.processing_step.replace(/_/g, ' ')}
                    </span>
                  )}
                </span>
              )}
              {isError && (
                <span className="status-badge status-badge--error">
                  <Icon name="info" size={11} /> Failed
                </span>
              )}
            </div>
          </div>

          {/* Participants */}
          {meeting.participants?.length > 0 && (
            <div className="meeting-hero__participants">
              <div style={{ fontSize: 11, color: 'var(--fg-3)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
                Speakers
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {meeting.participants.map((p, i) => (
                  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'var(--bg-2)', borderRadius: 'var(--r-pill)', padding: '4px 10px', fontSize: 12 }}>
                    <div style={{
                      width: 20, height: 20, borderRadius: '50%', fontSize: 10, fontWeight: 700,
                      display: 'grid', placeItems: 'center',
                      background: `var(--sp-${(i % 5) + 1})`, color: 'var(--accent-fg)',
                    }}>{p[0]}</div>
                    {p}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── Stepper (processing or error) ── */}
        {(isProcessing || isError) && (
          <div className="card" style={{ padding: '24px 28px' }}>
            <Stepper status={meeting.status} processingStep={meeting.processing_step} />
            {isError && (
              <div style={{
                marginTop: 20, padding: '12px 16px', background: 'var(--bad-soft)',
                borderRadius: 'var(--r-2)', color: 'var(--bad)', fontSize: 13,
                display: 'flex', alignItems: 'flex-start', gap: 8,
              }}>
                <Icon name="info" size={14} style={{ flexShrink: 0, marginTop: 1 }} />
                <span>{meeting.error_message || 'Processing failed. Please re-upload the file.'}</span>
              </div>
            )}
          </div>
        )}

        {/* ── Completed stepper (collapsed done state) ── */}
        {completed && (
          <div className="card" style={{ padding: '20px 28px' }}>
            <Stepper status="completed" processingStep="" />
          </div>
        )}

        {/* ── Media player ── */}
        {completed && meeting.playback_url && (
          <div className="card" style={{ padding: 20 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--fg-3)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 14 }}>
              <Icon name={meeting.file_type === 'audio' ? 'audio' : 'film'} size={12} style={{ marginRight: 6 }} />
              {meeting.file_type === 'audio' ? 'Audio Playback' : 'Video Playback'}
            </div>
            <MediaPlayer url={meeting.playback_url} fileType={meeting.file_type} />
          </div>
        )}

        {/* ── Tabs + content ── */}
        {completed && (
          <>
            <div className="detail-tabs">
              {[['transcript', 'Transcript'], ['summary', 'Summary'], ['mom', 'Minutes']].map(([tid, label]) => (
                <button
                  key={tid}
                  className={`detail-tab${tab === tid ? ' detail-tab--active' : ''}`}
                  onClick={() => setTab(tid)}
                >
                  {label}
                </button>
              ))}
              <div style={{ marginLeft: 'auto', paddingBottom: 6 }}>
                <button className="btn btn--ghost btn--sm" onClick={handlePdf} disabled={pdfLoading}>
                  <Icon name="doc" size={12} /> {pdfLoading ? 'Exporting…' : 'Export PDF'}
                </button>
              </div>
            </div>

            {/* Transcript */}
            {tab === 'transcript' && (
              <div className="transcript">
                {!transcript && (
                  <div style={{ padding: 24, textAlign: 'center', color: 'var(--fg-3)' }}>
                    <Icon name="loader" size={18} className="spin" style={{ marginBottom: 8, display: 'block', margin: '0 auto 8px' }} />
                    Loading transcript…
                  </div>
                )}
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
                  <div style={{ padding: 16, color: 'var(--fg-2)' }}>
                    <pre style={{ fontFamily: 'var(--font-sans)', whiteSpace: 'pre-wrap', lineHeight: 1.6, margin: 0 }}>
                      {transcript.raw_text || 'No transcript available.'}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Summary */}
            {tab === 'summary' && (
              <div className="summary">
                {!summary && <div className="card summary-card summary-card--full" style={{ color: 'var(--fg-3)' }}>Loading summary…</div>}
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
                        <h3 className="summary-card__title">Topics discussed</h3>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
                        {summary.topics.map((t, i) => <span key={i} className="pill">{t}</span>)}
                      </div>
                    </div>
                  )}
                </>}
              </div>
            )}

            {/* MOM */}
            {tab === 'mom' && (
              <div className="mom-doc">
                {!mom && <p style={{ color: 'var(--fg-3)' }}>Loading minutes…</p>}
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
                    : <pre style={{ fontFamily: 'var(--font-sans)', whiteSpace: 'pre-wrap', lineHeight: 1.65, margin: 0, color: 'var(--fg-1)' }}>
                        {mom.raw_text || mom.content || JSON.stringify(mom, null, 2)}
                      </pre>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
};

export default MeetingDetail;
