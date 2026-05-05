import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import useAuthStore from '../store/authStore';
import useToastStore from '../store/toastStore';
import { updateMe } from '../services/authService';

const fmtBytes = (b) => {
  if (!b) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  let i = 0; let v = b;
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(i > 1 ? 2 : 0)} ${units[i]}`;
};

const Profile = () => {
  const { user, setUser, logout } = useAuthStore();
  const navigate = useNavigate();
  const toast = useToastStore(s => s.add);

  const initial = (user?.display_name || user?.username || user?.email || 'U')[0].toUpperCase();
  const displayName = user?.display_name || user?.username || user?.email?.split('@')[0] || 'User';
  const email = user?.email || '';
  const emailNotifs = user?.email_notifications ?? true;

  const [editingName, setEditingName] = useState(false);
  const [nameVal, setNameVal] = useState(displayName);
  const [saving, setSaving] = useState(false);

  const handleLogout = () => { logout(); navigate('/login'); };

  const saveName = async () => {
    if (!nameVal.trim() || nameVal === displayName) { setEditingName(false); return; }
    setSaving(true);
    try {
      const updated = await updateMe({ display_name: nameVal.trim() });
      setUser({ ...user, ...updated });
      toast('Name updated', 'success');
      setEditingName(false);
    } catch { toast('Failed to update name', 'error'); }
    finally { setSaving(false); }
  };

  const toggleNotifs = async () => {
    try {
      const updated = await updateMe({ email_notifications: !emailNotifs });
      setUser({ ...user, ...updated });
    } catch { toast('Failed to update setting', 'error'); }
  };

  return (
    <Layout crumbs={['Workspace', 'Profile']}>
      <div className="profile-page fade-up">
        <div className="profile-hero">
          <div className="avatar avatar--lg">{initial}</div>
          <div className="profile-hero__info">
            <h1 className="profile-hero__name">{displayName}</h1>
            <p className="profile-hero__email">{email}</p>
            <div className="profile-hero__pills">
              <span className="pill pill--accent">Active</span>
              <span className="pill"><Icon name="calendar" size={11} /> Member</span>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {[
            { label: 'Total meetings', value: user?.total_meetings ?? '—', icon: 'video' },
            { label: 'Completed', value: user?.completed_meetings ?? '—', icon: 'check' },
            { label: 'Storage used', value: fmtBytes(user?.total_storage_bytes), icon: 'doc' },
          ].map(({ label, value, icon }) => (
            <div key={label} className="card" style={{ padding: '16px 20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                <Icon name={icon} size={14} style={{ color: 'var(--accent)' }} />
                <span style={{ fontSize: 12, color: 'var(--fg-2)' }}>{label}</span>
              </div>
              <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--fg-0)' }}>{value}</div>
            </div>
          ))}
        </div>

        {/* Account */}
        <div className="card">
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--line-0)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name="user" size={15} style={{ color: 'var(--accent)' }} />
            <h3 style={{ margin: 0, fontSize: 13.5, color: 'var(--fg-0)', fontWeight: 600 }}>Account</h3>
          </div>
          <div className="field-list">
            <div className="field">
              <div>
                <div className="field__label">Display name</div>
                <div className="field__sub">Shown across the app</div>
              </div>
              {editingName
                ? <input
                    className="field__input"
                    value={nameVal}
                    onChange={e => setNameVal(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') saveName(); if (e.key === 'Escape') setEditingName(false); }}
                    autoFocus
                    style={{ flex: 1, background: 'var(--bg-2)', border: '1px solid var(--accent)', borderRadius: 'var(--r-1)', padding: '4px 8px', fontSize: 13, color: 'var(--fg-0)' }}
                  />
                : <div className="field__value">{displayName}</div>
              }
              {editingName
                ? <div style={{ display: 'flex', gap: 6 }}>
                    <button className="btn btn--accent btn--sm" onClick={saveName} disabled={saving}>{saving ? '…' : 'Save'}</button>
                    <button className="btn btn--ghost btn--sm" onClick={() => { setEditingName(false); setNameVal(displayName); }}>Cancel</button>
                  </div>
                : <button className="link-btn" onClick={() => setEditingName(true)}>Edit</button>
              }
            </div>
            <div className="field">
              <div>
                <div className="field__label">Email</div>
                <div className="field__sub">Used for sign in &amp; notifications</div>
              </div>
              <div className="field__value">{email}</div>
              <div />
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card">
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--line-0)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Icon name="bell" size={15} style={{ color: 'var(--accent)' }} />
            <h3 style={{ margin: 0, fontSize: 13.5, color: 'var(--fg-0)', fontWeight: 600 }}>Notifications</h3>
          </div>
          <div className="field-list">
            <div className="field">
              <div>
                <div className="field__label">Email notifications</div>
                <div className="field__sub">Get a digest when transcripts are ready</div>
              </div>
              <button
                className={`toggle${emailNotifs ? ' toggle--on' : ''}`}
                onClick={toggleNotifs}
                aria-label="Toggle email notifications"
              />
            </div>
          </div>
        </div>

        {/* Sign out */}
        <div className="card" style={{ display: 'flex', alignItems: 'center', padding: '16px 20px', gap: 16 }}>
          <Icon name="logout" size={16} style={{ color: 'var(--fg-2)' }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--fg-0)' }}>Sign out</div>
            <div style={{ fontSize: 12, color: 'var(--fg-2)' }}>End this session on this device</div>
          </div>
          <button className="btn btn--ghost btn--sm" onClick={handleLogout}>Sign out</button>
        </div>
      </div>
    </Layout>
  );
};

export default Profile;
