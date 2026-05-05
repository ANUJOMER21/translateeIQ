import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './store/authStore';
import Toast from './components/Toast';
import Login from './pages/auth/Login';
import Signup from './pages/auth/Signup';
import Dashboard from './pages/Dashboard';
import Meetings from './pages/Meetings';
import MeetingDetail from './pages/MeetingDetail';
import Upload from './pages/Upload';
import Chatbot from './pages/Chatbot';
import Profile from './pages/Profile';
import PublicMeetingDetail from './pages/PublicMeetingDetail';
import Icon from './components/Icon';

const RequireAuth = ({ children }) => {
  const { user, loading } = useAuthStore();
  if (loading) return (
    <div style={{ height: '100vh', display: 'grid', placeItems: 'center', background: 'var(--bg-0)' }}>
      <Icon name="loader" size={28} className="spin" style={{ color: 'var(--accent)' }} />
    </div>
  );
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

const App = () => {
  const init = useAuthStore(s => s.init);
  useEffect(() => { init(); }, []);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/share/:token" element={<PublicMeetingDetail />} />
        <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
        <Route path="/meetings" element={<RequireAuth><Meetings /></RequireAuth>} />
        <Route path="/meetings/:id" element={<RequireAuth><MeetingDetail /></RequireAuth>} />
        <Route path="/upload" element={<RequireAuth><Upload /></RequireAuth>} />
        <Route path="/assistant" element={<RequireAuth><Chatbot /></RequireAuth>} />
        <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toast />
    </BrowserRouter>
  );
};

export default App;
