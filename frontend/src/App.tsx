import { useState, useCallback, useEffect, useMemo } from 'react';
import { Info, ArrowUpDown, MessageSquare, Pill, Clock, ClipboardList, FileText, FlaskConical, BookOpen, Shield, Paperclip } from 'lucide-react';
import { Layout } from './components/Layout';
import { MemberSearch } from './components/MemberSearch';
import { MemberProfile } from './components/MemberProfile';
import { MemberDetailPanel } from './components/MemberDetailPanel';
import { ChatPanel } from './components/ChatPanel';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Avatar } from './components/Avatar';
import { AboutTab } from './components/AboutTab';
import { useAgent } from './hooks/useAgent';
import { useMemberDetail } from './hooks/useMemberDetail';
import { getTopRiskMembers } from './api/client';
import type { MemberSummary, ChatMessage } from './types';
import './styles/globals.css';

type SortKey = 'risk' | 'name' | 'age';
type AppView = 'main' | 'about';
type MemberTab = 'chat' | 'medications' | 'timeline' | 'encounters' | 'diagnoses' | 'labs' | 'sources' | 'insurance' | 'attachments';

const MEMBER_TABS: { key: MemberTab; label: string; Icon: typeof MessageSquare }[] = [
  { key: 'chat', label: 'Chat', Icon: MessageSquare },
  { key: 'medications', label: 'Meds', Icon: Pill },
  { key: 'timeline', label: 'Timeline', Icon: Clock },
  { key: 'encounters', label: 'Visits', Icon: ClipboardList },
  { key: 'diagnoses', label: 'Dx', Icon: FileText },
  { key: 'labs', label: 'Labs', Icon: FlaskConical },
  { key: 'sources', label: 'Sources', Icon: BookOpen },
  { key: 'insurance', label: 'Claims', Icon: Shield },
  { key: 'attachments', label: 'Files', Icon: Paperclip },
];

export default function App() {
  const [selectedMember, setSelectedMember] = useState<MemberSummary | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const [topRisk, setTopRisk] = useState<MemberSummary[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>('risk');
  const [filterTag, setFilterTag] = useState<string>('all');
  const [appView, setAppView] = useState<AppView>('main');
  const [activeTab, setActiveTab] = useState<MemberTab>('chat');
  const { ask, loading, error, clearError } = useAgent();
  const { detail, loading: detailLoading } = useMemberDetail(selectedMember?.member_id ?? null);

  useEffect(() => { getTopRiskMembers().then(setTopRisk).catch(() => {}); }, []);

  const handleSelectMember = useCallback((member: MemberSummary) => {
    setSelectedMember(member);
    setMessages([]);
    setLastQuestion(null);
    setAppView('main');
    setActiveTab('chat');
  }, []);

  const buildHistory = useCallback((msgs: ChatMessage[]) => {
    return msgs.map((m) => ({ role: m.role, content: m.role === 'assistant' ? (m.response?.answer || m.content) : m.content }));
  }, []);

  const handleSend = useCallback(async (question: string) => {
    if (!selectedMember) return;
    setLastQuestion(question);
    clearError();
    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: question, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    const history = buildHistory(messages);
    const resp = await ask(selectedMember.member_id, question, history);
    if (resp) {
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'assistant', content: resp.answer, response: resp, timestamp: new Date() }]);
    }
  }, [selectedMember, ask, messages, buildHistory, clearError]);

  const handleRetry = useCallback(() => {
    if (lastQuestion) {
      clearError();
      setMessages((prev) => { const c = [...prev]; for (let i = c.length - 1; i >= 0; i--) { if (c[i].role === 'user' && c[i].content === lastQuestion) { c.splice(i, 1); break; } } return c; });
      handleSend(lastQuestion);
    }
  }, [lastQuestion, clearError, handleSend]);

  const conditionTags = useMemo(() => {
    const tags = new Set<string>();
    topRisk.forEach((m) => m.risk_flags.forEach((f) => tags.add(f)));
    return Array.from(tags).sort();
  }, [topRisk]);

  const sortedFiltered = useMemo(() => {
    let list = filterTag === 'all' ? topRisk : topRisk.filter((m) => m.risk_flags.includes(filterTag));
    if (sortKey === 'name') list = [...list].sort((a, b) => a.last_name.localeCompare(b.last_name));
    else if (sortKey === 'age') list = [...list].sort((a, b) => (b.age || 0) - (a.age || 0));
    return list;
  }, [topRisk, sortKey, filterTag]);

  // Sidebar: compact — logo, search, member card only
  const sidebar = (
    <>
      <div className="sidebar-header">
        <h2 onClick={() => { setSelectedMember(null); setAppView('main'); }} style={{ cursor: 'pointer' }}>Sentinel360</h2>
        <button className="about-nav-btn" onClick={() => setAppView('about')} title="About"><Info size={16} /></button>
      </div>
      <MemberSearch onSelect={handleSelectMember} />
      {selectedMember && <MemberProfile member={selectedMember} />}
      {detailLoading && <div className="detail-loading">Loading clinical data...</div>}
    </>
  );

  // Main panel content
  let main;
  if (appView === 'about') {
    main = <AboutTab />;
  } else if (!selectedMember) {
    // Landing worklist
    main = (
      <div className="landing-panel">
        <div className="landing-header">
          <h2>Needs Attention Today</h2>
          <p className="landing-subtitle">Members ranked by risk — select one to start</p>
        </div>
        <div className="worklist-controls">
          <div className="sort-control">
            <ArrowUpDown size={14} />
            {(['risk', 'name', 'age'] as SortKey[]).map((k) => (
              <button key={k} className={`filter-chip ${sortKey === k ? 'filter-chip-active' : ''}`} onClick={() => setSortKey(k)}>
                {k === 'risk' ? 'Risk' : k === 'name' ? 'Name' : 'Age'}
              </button>
            ))}
          </div>
          <div className="filter-control">
            <button className={`filter-chip ${filterTag === 'all' ? 'filter-chip-active' : ''}`} onClick={() => setFilterTag('all')}>All</button>
            {conditionTags.slice(0, 6).map((tag) => (
              <button key={tag} className={`filter-chip ${filterTag === tag ? 'filter-chip-active' : ''}`} onClick={() => setFilterTag(tag)}>{tag}</button>
            ))}
          </div>
        </div>
        <div className="risk-worklist">
          {sortedFiltered.map((m) => (
            <button key={m.member_id} className="risk-worklist-item" onClick={() => handleSelectMember(m)}>
              <Avatar firstName={m.first_name} lastName={m.last_name} memberId={m.member_id} size={40} />
              <div className="worklist-member-info">
                <span className="worklist-name">{m.first_name} {m.last_name}</span>
                <span className="worklist-meta">{m.age}y · {m.gender} · {m.plan_type}</span>
              </div>
              <div className="worklist-flags">
                {m.risk_flags.slice(0, 3).map((flag) => (<span key={flag} className="condition-tag">{flag}</span>))}
                {m.risk_flags.length > 3 && <span className="worklist-more">+{m.risk_flags.length - 3}</span>}
              </div>
            </button>
          ))}
          {sortedFiltered.length === 0 && <div className="detail-empty">No members match this filter</div>}
        </div>
      </div>
    );
  } else {
    // Member selected — tab bar + content in main panel
    main = (
      <div className="main-tabbed">
        <div className="main-tab-bar">
          {MEMBER_TABS.map(({ key, label, Icon }) => (
            <button key={key} className={`main-tab ${activeTab === key ? 'main-tab-active' : ''}`} onClick={() => setActiveTab(key)}>
              <Icon size={14} />
              <span>{label}</span>
            </button>
          ))}
        </div>
        <div className="main-tab-content">
          <ErrorBoundary>
            {activeTab === 'chat' && (
              <ChatPanel messages={messages} onSend={handleSend} loading={loading} disabled={false} member={selectedMember} error={error} onClearError={clearError} onRetry={handleRetry} />
            )}
            {activeTab !== 'chat' && detail && (
              <MemberDetailPanel detail={detail} activeTab={activeTab} />
            )}
            {activeTab !== 'chat' && !detail && detailLoading && (
              <div className="detail-loading" style={{ padding: 32 }}>Loading clinical data...</div>
            )}
          </ErrorBoundary>
        </div>
      </div>
    );
  }

  return <Layout sidebar={sidebar} main={main} />;
}
