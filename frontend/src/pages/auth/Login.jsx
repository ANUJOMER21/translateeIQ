import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../../services/authService';
import { me } from '../../services/authService';
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
          Transcribe, summarize, and ask questions across your entire meeting library —
          without ever scrubbing through audio again.
        </p>
        <div className="auth-hero__features">
          {[
            { icon: 'doc', title: 'Speaker-tagged transcripts', desc: 'Every word, every speaker, every timestamp — searchable in seconds.' },
            { icon: 'lightbulb', title: 'Decisions & action items, surfaced', desc: 'We pull out what matters so you don\'t have to re-read the transcript.' },
            { icon: 'sparkles', title: 'Chat with your meeting library', desc: '"What did we decide about pricing in Q1?" Just ask. Get answers with citations.' },
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

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setUser = useAuthStore(s => s.setUser);
  const toast = useToastStore(s => s.add);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      const user = await me();
      setUser(user);
      navigate('/');
    } catch (err) {
      toast(err.response?.data?.detail || 'Invalid credentials', 'error');
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
            <h2 className="auth-form__title">Welcome back</h2>
            <p className="auth-form__subtitle">Sign in to pick up where you left off.</p>
          </div>
          <div className="input-group">
            <label className="input-label">Email</label>
            <input className="input" type="email" placeholder="you@company.com" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div className="input-group">
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label className="input-label">Password</label>
            </div>
            <div className="input-wrap">
              <input className="input" type={showPw ? 'text' : 'password'} placeholder="••••••••" value={password} onChange={e => setPassword(e.target.value)} required />
              <button type="button" className="input-wrap__btn" onClick={() => setShowPw(!showPw)}>
                <Icon name={showPw ? 'eye-off' : 'eye'} size={16} />
              </button>
            </div>
          </div>
          <button type="submit" className="btn btn--primary btn--lg" disabled={loading} style={{ width: '100%' }}>
            {loading ? <><Icon name="loader" size={15} className="spin" /> Signing in…</> : <>Sign in <Icon name="arrow-right" size={15} /></>}
          </button>
          <div style={{ textAlign: 'center', fontSize: 13, color: 'var(--fg-2)' }}>
            New here? <Link to="/signup" style={{ color: 'var(--accent)', fontWeight: 600 }}>Create an account</Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;
