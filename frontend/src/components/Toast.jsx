import useToastStore from '../store/toastStore';
import Icon from './Icon';

const typeStyle = {
  info: { color: 'var(--info)', bg: 'var(--info-soft)' },
  success: { color: 'var(--good)', bg: 'var(--good-soft)' },
  error: { color: 'var(--bad)', bg: 'var(--bad-soft)' },
  warn: { color: 'var(--warn)', bg: 'var(--warn-soft)' },
};

const Toast = () => {
  const { toasts, remove } = useToastStore();
  if (!toasts.length) return null;
  return (
    <div style={{ position: 'fixed', bottom: 24, right: 24, zIndex: 9999, display: 'flex', flexDirection: 'column', gap: 8 }}>
      {toasts.map(t => {
        const s = typeStyle[t.type] || typeStyle.info;
        return (
          <div key={t.id} style={{
            display: 'flex', alignItems: 'center', gap: 10,
            background: 'var(--bg-2)', border: '1px solid var(--line-1)',
            borderLeft: `3px solid ${s.color}`,
            borderRadius: 'var(--r-2)', padding: '10px 14px',
            minWidth: 260, maxWidth: 400, boxShadow: 'var(--shadow-2)',
            animation: 'fadeUp 0.24s cubic-bezier(0.2,0.8,0.2,1) both',
          }}>
            <span style={{ color: s.color, flexShrink: 0 }}>
              {t.type === 'success' && <Icon name="check-circle" size={15} />}
              {t.type === 'error' && <Icon name="x" size={15} />}
              {t.type === 'warn' && <Icon name="info" size={15} />}
              {t.type === 'info' && <Icon name="info" size={15} />}
            </span>
            <span style={{ flex: 1, fontSize: 13, color: 'var(--fg-0)' }}>{t.message}</span>
            <button onClick={() => remove(t.id)} style={{ color: 'var(--fg-3)', padding: 2 }}>
              <Icon name="x" size={13} />
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default Toast;
