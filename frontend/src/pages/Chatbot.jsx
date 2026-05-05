import { useState, useRef, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import Layout from '../components/Layout';
import Icon from '../components/Icon';
import { sendMessage } from '../services/chatService';

const SUGGESTIONS = [
  'What were the main decisions this week?',
  'Summarize action items with owners',
  'What risks or blockers came up?',
  'List topics discussed in the last few meetings',
];

const renderText = (text) =>
  text.split('**').map((part, idx) =>
    idx % 2 === 1 ? <strong key={idx}>{part}</strong> : <span key={idx}>{part}</span>
  );

const Chatbot = () => {
  const [searchParams] = useSearchParams();
  const meetingId = searchParams.get('meeting');
  const [scope, setScope] = useState(meetingId ? 'this' : 'all');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'ai', text: "Hi! I'm your meeting assistant. Ask me anything about your meetings — summaries, decisions, action items, or search across all transcripts." },
  ]);
  const [thinking, setThinking] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, thinking]);

  const send = async (text) => {
    if (!text.trim() || thinking) return;
    setMessages(prev => [...prev, { role: 'user', text }]);
    setInput('');
    setThinking(true);
    try {
      const data = await sendMessage(text, scope, scope === 'this' ? meetingId : null);
      setMessages(prev => [...prev, { role: 'ai', text: data.response }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'ai', text: `Error: ${err.response?.data?.response || err.message}` }]);
    } finally {
      setThinking(false);
    }
  };

  return (
    <Layout crumbs={['Workspace', 'AI Assistant']}>
      <div className="chat fade-up">
        <div className="chat__scope">
          <button className={`chat__scope-btn${scope === 'all' ? ' chat__scope-btn--active' : ''}`} onClick={() => setScope('all')}>
            <Icon name="doc" size={12} style={{ verticalAlign: -1, marginRight: 4 }} /> All meetings
          </button>
          {meetingId && (
            <button className={`chat__scope-btn${scope === 'this' ? ' chat__scope-btn--active' : ''}`} onClick={() => setScope('this')}>
              This meeting
            </button>
          )}
        </div>

        <div className="chat__messages" ref={scrollRef}>
          {messages.map((m, i) => (
            <div key={i} className={`chat-msg${m.role === 'user' ? ' chat-msg--user' : ''}`}>
              <div className={`chat-msg__avatar chat-msg__avatar--${m.role === 'user' ? 'user' : 'ai'}`}>
                {m.role === 'user' ? 'U' : <Icon name="sparkles" size={16} />}
              </div>
              <div className="chat-msg__body">
                <div className="chat-msg__name">
                  {m.role === 'user' ? 'You' : 'TranslateeIQ'}
                </div>
                <div className="chat-msg__bubble">{renderText(m.text)}</div>
              </div>
            </div>
          ))}
          {thinking && (
            <div className="chat-msg">
              <div className="chat-msg__avatar chat-msg__avatar--ai"><Icon name="sparkles" size={16} /></div>
              <div className="chat-msg__body">
                <div className="chat-msg__name">TranslateeIQ</div>
                <div className="chat-msg__bubble" style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <Icon name="loader" size={14} className="spin" /> Thinking…
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="chat__suggestions">
          {SUGGESTIONS.map((s, i) => (
            <button key={i} className="chat-suggest" onClick={() => send(s)}>{s}</button>
          ))}
        </div>

        <div className="chat__composer">
          <input
            className="chat__input"
            placeholder="Ask anything about your meetings…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send(input)}
          />
          <button className="chat__send" disabled={!input.trim() || thinking} onClick={() => send(input)}>
            <Icon name="send" size={15} />
          </button>
        </div>
      </div>
    </Layout>
  );
};

export default Chatbot;
