import { useState, useRef, useEffect } from 'react';
import { ChatMessageBubble } from './ChatMessage';
import { QuickActions } from './QuickActions';
import { ExportButton } from './ExportButton';
import { ErrorBanner } from './ErrorBanner';
import type { ChatMessage, MemberSummary } from '../types';

interface ChatPanelProps {
  messages: ChatMessage[];
  onSend: (question: string) => void;
  loading: boolean;
  disabled: boolean;
  member: MemberSummary | null;
  error: string | null;
  onClearError?: () => void;
  onRetry?: () => void;
}

const LOADING_MESSAGES = [
  'Retrieving clinical data...',
  'Analyzing medications...',
  'Checking interactions...',
  'Reviewing policy guidelines...',
  'Composing answer...',
];

export function ChatPanel({ messages, onSend, loading, disabled, member, error, onClearError, onRetry }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [loadingIdx, setLoadingIdx] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (!loading) {
      setLoadingIdx(0);
      return;
    }
    const interval = setInterval(() => {
      setLoadingIdx((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 2500);
    return () => clearInterval(interval);
  }, [loading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading || disabled) return;
    onSend(input.trim());
    setInput('');
  };

  const showQuickActions = member && messages.length === 0 && !loading;

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span className="chat-header-title">
          {member ? `Chat — ${member.first_name} ${member.last_name}` : 'Clinical Copilot'}
        </span>
        {member && <ExportButton messages={messages} member={member} />}
      </div>
      <div className="chat-messages">
        {!member && (
          <div className="chat-empty">
            Select a member from the sidebar to get started.
          </div>
        )}
        {showQuickActions && (
          <div className="chat-welcome">
            <div className="chat-welcome-text">
              What would you like to know about {member.first_name}?
            </div>
            <QuickActions member={member} onAsk={onSend} />
          </div>
        )}
        {messages.map((msg) => (
          <ChatMessageBubble key={msg.id} message={msg} onFollowUp={!loading ? onSend : undefined} />
        ))}
        {loading && (
          <div className="chat-loading">
            <div className="loading-indicator">
              <div className="loading-dots">
                <span></span><span></span><span></span>
              </div>
              <span className="loading-status">{LOADING_MESSAGES[loadingIdx]}</span>
            </div>
          </div>
        )}
        {error && (
          <ErrorBanner message={error} onRetry={onRetry} onDismiss={onClearError} />
        )}
        <div ref={messagesEndRef} />
      </div>
      <form className="chat-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="chat-input"
          placeholder={disabled ? 'Select a member first...' : 'Ask about this member...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={disabled || loading}
        />
        <button
          type="submit"
          className="chat-send-btn"
          disabled={!input.trim() || loading || disabled}
        >
          Send
        </button>
      </form>
    </div>
  );
}
