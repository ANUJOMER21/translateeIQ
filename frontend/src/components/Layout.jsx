import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import Icon from './Icon';

const navItems = [
  { to: '/', icon: 'home', label: 'Dashboard' },
  { to: '/meetings', icon: 'video', label: 'Meetings' },
  { to: '/assistant', icon: 'sparkles', label: 'AI Assistant', badge: 'AI' },
  { to: '/profile', icon: 'user', label: 'Profile' },
];

const Layout = ({ children, crumbs = [] }) => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const initial = (user?.username || user?.email || 'U')[0].toUpperCase();
  const displayName = user?.username || user?.email?.split('@')[0] || 'User';
  const email = user?.email || '';

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <div className="brand-mark"><Icon name="zap" size={16} /></div>
          <div className="brand-name">translatee<b>IQ</b></div>
        </div>

        <NavLink to="/upload" className="new-meeting-btn" style={{ textDecoration: 'none' }}>
          <Icon name="plus" size={16} /> New meeting
        </NavLink>

        <nav className="nav">
          <div className="nav__label">Workspace</div>
          {navItems.map(({ to, icon, label, badge }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `nav__item${isActive ? ' nav__item--active' : ''}`}
            >
              <Icon name={icon} size={17} className="nav__icon" />
              <span>{label}</span>
              {badge && <span className="nav__badge">{badge}</span>}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar__spacer" />

        <button className="user-card" onClick={() => navigate('/profile')}>
          <div className="avatar">{initial}</div>
          <div className="user-card__info">
            <div className="user-card__name">{displayName}</div>
            <div className="user-card__email">{email}</div>
          </div>
          <span
            role="button"
            title="Sign out"
            onClick={(e) => { e.stopPropagation(); handleLogout(); }}
            style={{ display: 'grid', placeItems: 'center', width: 26, height: 26, borderRadius: 7, color: 'var(--fg-3)' }}
          >
            <Icon name="logout" size={14} />
          </span>
        </button>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="crumb">
            {crumbs.map((c, i) => (
              <span key={i}>
                {i > 0 && <span style={{ margin: '0 8px', color: 'var(--fg-3)' }}>/</span>}
                {i === crumbs.length - 1 ? <b>{c}</b> : c}
              </span>
            ))}
          </div>
          <div className="topbar__search">
            <Icon name="search" size={14} />
            <span>Search meetings, transcripts…</span>
            <kbd>⌘K</kbd>
          </div>
          <button className="icon-btn" title="Notifications">
            <Icon name="bell" size={16} />
            <span className="icon-btn__dot" />
          </button>
        </header>

        <div className="content">{children}</div>

        <nav className="mobile-nav" aria-label="Mobile navigation">
          {[
            ...navItems,
            { to: '/upload', icon: 'plus', label: 'Upload' },
          ].map(({ to, icon, label }) => {
            const active = to === '/'
              ? location.pathname === '/'
              : location.pathname === to || location.pathname.startsWith(`${to}/`);
            return (
              <button
                key={to}
                className={`mobile-nav__item${active ? ' mobile-nav__item--active' : ''}`}
                onClick={() => navigate(to)}
                aria-label={label}
              >
                <Icon name={icon} size={16} />
                <span>{label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};

export default Layout;
