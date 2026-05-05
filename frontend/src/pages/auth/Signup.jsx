import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { register, login, me } from '../../services/authService';
import useAuthStore from '../../store/authStore';
import useToastStore from '../../store/toastStore';
import Icon from '../../components/Icon';

const AuthHero = () => (
  <div className="auth-hero">
    <div className="auth-hero__bg" />
    <div className="auth-hero__content">
      <div className="auth-hero__brand">
        <div className="brand-mark"><Icon name="zap" size={16} /></div>
        <div className="brand-name">translatee<b>IQ</b></div>
      </div>
      <div style={{ marginTop: 'auto' }}>
        <h1 className="auth-hero__title">Meetings, distilled into clarity.</h1>
        <p className="auth-hero__subtitle">
          Upload a recording and get a transcript, summary, action items, and MOM in minutes.
        </p>
        <div className="auth-hero__features">
          {[
            { icon: 'video', title: 'Video & audio support', desc: 'MP4, MOV, AVI, MKV, MP3, WAV, M4A, FLAC — all supported.' },
            { icon: 'check-circle', title: 'Action items extracted', desc: 'Owners, due dates, and tasks pulled automatically from every meeting.' },
            { icon: 'sparkles', title: 'AI-powered insights', desc: 'Ask natural language questions. Get cited answers instantly.' },
          ].map(f => (
            <div key={f.title} className="auth-feature">
              <div className="auth-feature__icon"><Icon name={f.icon} size={18} /></div>
              <div>
                <p className="auth-feature__title">{f.title}</p>
                <p className="auth-feature__desc">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="auth-hero__footer">
        <span>Privacy</span><span>Terms</span>
        <span style={{ marginLeft: 'auto' }}>© 2026 TranslateeIQ</span>
      </div>
    </div>
  </div>
);

const Signup = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setUser = useAuthStore(s => s.setUser);
  const toast = useToastStore(s => s.add);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(email, password, username);
      await login(email, password);
      const user = await me();
      setUser(user);
      navigate('/');
    } catch (err) {
      const msg = err.response?.data ? JSON.stringify(err.response.data) : 'Registration failed';
      toast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <AuthHero />
      <div className="auth-form-wrap">
        <form className="auth-form fade-up" onSubmit={handleSubmit}>
          <div>
            <h2 className="auth-form__title">Create your account</h2>
            <p className="auth-form__subtitle">Start transcribing meetings — free to get started.</p>
          </div>
          <div className="input-group">
            <label className="input-label">Username</label>
            <input className="input" placeholder="yourname" value={username} onChange={e => setUsername(e.target.value)} required />
          </div>
          <div className="input-group">
            <label className="input-label">Work email</label>
            <input className="input" type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div className="input-group">
            <label className="input-label">Password</label>
            <input className="input" type="password" placeholder="At least 8 characters" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} />
          </div>
          <button type="submit" className="btn btn--primary btn--lg" disabled={loading} style={{ width: '100%' }}>
            {loading ? <><Icon name="loader" size={15} className="spin" /> Creating…</> : <>Create account <Icon name="arrow-right" size={15} /></>}
          </button>
          <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--fg-2)' }}>
            Already have an account? <Link to="/login" style={{ color: 'var(--accent)', fontWeight: 600 }}>Sign in</Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Signup;
