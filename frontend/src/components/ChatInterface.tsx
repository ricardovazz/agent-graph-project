import React from 'react';
import { useAppStore } from '../store/appStore';
import ReactMarkdown from 'react-markdown';

export const ChatInterface: React.FC = () => {
  const { messages, sendMessage, status, statusMessage } = useAppStore();
  const [input, setInput] = React.useState('');
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  const getMessageStyle = (type: string) => {
    switch (type) {
      case 'human':
        return 'bg-primary text-white ms-auto';
      case 'ai':
        return 'bg-light text-dark me-auto border';
      case 'system':
        return 'bg-info text-white text-center w-100';
      case 'tool_result':
        return 'bg-secondary text-light me-auto border border-secondary';
      default:
        return 'bg-light text-dark me-auto';
    }
  };

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'human':
        return '👤';
      case 'ai':
        return '🤖';
      case 'system':
        return 'ℹ️';
      case 'tool_call':
        return '🔧';
      case 'tool_result':
        return '📦';
      case 'job_status':
        return '⚙️';
      default:
        return '💬';
    }
  };

  return (
    <div className="card h-100 shadow-sm">
      <div className="card-header bg-dark text-white d-flex justify-content-between align-items-center">
        <h5 className="mb-0">💬 Agent Chat</h5>
        <span className={`badge ${status === 'thinking' ? 'bg-warning' : 'bg-success'}`}>
          {status === 'thinking' ? '⏳ ' : '✓ '}{statusMessage}
        </span>
      </div>
      
      <div className="card-body d-flex flex-column" style={{ height: 'calc(100% - 120px)', overflow: 'hidden' }}>
        <div className="flex-grow-1 overflow-auto mb-3" style={{ maxHeight: '100%' }}>
          {messages.length === 0 ? (
            <div className="text-center text-muted mt-5">
              <p className="lead">No messages yet</p>
              <p>Start a conversation with the supervisor agent!</p>
            </div>
          ) : (
            <div className="d-flex flex-column gap-2">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`rounded-3 p-3 ${getMessageStyle(msg.type)}`}
                  style={{ maxWidth: '75%', alignSelf: msg.type === 'human' ? 'flex-end' : 'flex-start' }}
                >
                  <div className="d-flex align-items-center gap-2 mb-1">
                    <span>{getMessageIcon(msg.type)}</span>
                    <small className="text-uppercase fw-bold" style={{ fontSize: '0.7rem' }}>
                      {msg.type.replace('_', ' ')}
                    </small>
                    <small className="text-muted" style={{ fontSize: '0.65rem' }}>
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </small>
                  </div>
                  <div className="message-content" style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="d-flex gap-2">
          <input
            type="text"
            className="form-control flex-grow-1"
            placeholder="Type your message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={status === 'thinking'}
          />
          <button 
            type="submit" 
            className="btn btn-primary"
            disabled={!input.trim() || status === 'thinking'}
          >
            📤 Send
          </button>
        </form>
      </div>
    </div>
  );
};
