import { useState, useCallback, useEffect, useMemo } from 'react';
import { ArrowUpDown, MessageSquare, Pill, Clock, ClipboardList, FileText, FlaskConical, BookOpen, Shield, Paperclip, LayoutDashboard } from 'lucide-react';
import { Layout } from './components/Layout';
import { AppNav } from './components/AppNav';
import type { AppPage, UserRole } from './components/AppNav';
import { MemberSearch } from './components/MemberSearch';
import { MemberOverview } from './components/MemberOverview';
import { MemberDetailPanel } from './components/MemberDetailPanel';
import { ChatPanel } from './components/ChatPanel';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Avatar } from './components/Avatar';
import { AboutTab } from './components/AboutTab';
import { DocumentsPage } from './components/DocumentsPage';
import { JobsPage } from './components/JobsPage';
import { AuditPage } from './components/AuditPage';
import { MemberStudioPage } from './components/MemberStudioPage';
import { SettingsPage } from './components/SettingsPage';
import { useAgent } from './hooks/useAgent';
import { useMemberDetail } from './hooks/useMemberDetail';
import { getTopRiskMembers } from './api/client';
import type { MemberSummary, ChatMessage } from './types';
import './styles/globals.css';

type SortKey = 'risk' | 'name' | 'age';
type MemberTab = 'overview' | 'chat' | 'medications' | 'timeline' | 'encounters' | 'diagnoses' | 'labs' | 'sources' | 'insurance' | 'attachments';

const MEMBER_TABS: { key: MemberTab; label: string; Icon: typeof MessageSquare }[] = [
  { key: 'overview', label: 'Overview', Icon: LayoutDashboard },
  { key: 'chat', label: 'Chat', Icon: MessageSquare },
  { key: 'timeline', label: 'Timeline', Icon: Clock },
  { key: 'medications', label: 'Meds', Icon: Pill },
  { key: 'encounters', label: 'Visits', Icon: ClipboardList },
  { key: 'diagnoses', label: 'Dx', Icon: FileText },
  { key: 'labs', label: 'Labs', Icon: FlaskConical },
  { key: 'insurance', label: 'Claims', Icon: Shield },
  { key: 'sources', label: 'Documents', Icon: BookOpen },
  { key: 'attachments', label: 'Files', Icon: Paperclip },
];

export default function App() {
  const [currentPage, setCurrentPage] = useState<AppPage>('worklist');
  const [currentRole, setCurrentRole] = useState<UserRole>('admin');
  const [userName] = useState('System Admin');
  const [selectedMember, setSelectedMember] = useState<MemberSummary | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lastQuestion, setLastQuestion] = useState<string | null>(null);
  const [topRisk, setTopRisk] = useState<MemberSummary[]>([]);
  const [sortKey, setSortKey] = useState<SortKey>('risk');
  const [filterTag, setFilterTag] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<MemberTab>('overview');
  const { ask, loading, error, clearError } = useAgent();
  const { detail, loading: detailLoading } = useMemberDetail(selectedMember?.member_id ?? null);

  useEffect(() => { getTopRiskMembers().then(setTopRisk).catch(() => {}); }, []);

  const handleSelectMember = useCallback((member: MemberSummary) => {
    setSelectedMember(member);
    setMessages([]);
    setLastQuestion(null);
    setCurrentPage('member-detail');
    setActiveTab('overview');
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

  const handleNavigate = useCallback((page: AppPage) => {
    setCurrentPage(page);
    if (page !== 'member-detail') {
      // Keep selectedMember but navigate away from detail
    }
  }, []);

  // Member context bar (shown when a member is selected)
  const memberContext = selectedMember ? (
    <div className="member-context-card" onClick={() => { setCurrentPage('member-detail'); setActiveTab('overview'); }}>
      <Avatar firstName={selectedMember.first_name} lastName={selectedMember.last_name} memberId={selectedMember.member_id} size={32} />
      <div className="context-info">
        <span className="context-name">{selectedMember.first_name} {selectedMember.last_name}</span>
        <span className="context-meta">{selectedMember.member_id} · {selectedMember.age}y · {selectedMember.gender}</span>
      </div>
      <div className="context-flags">
        {selectedMember.risk_flags.slice(0, 2).map((f) => <span key={f} className="condition-tag condition-tag-sm">{f}</span>)}
      </div>
    </div>
  ) : null;

  // Nav
  const nav = (
    <AppNav
      currentPage={currentPage}
      onNavigate={handleNavigate}
      currentRole={currentRole}
      onRoleChange={setCurrentRole}
      userName={userName}
    />
  );

  // Main content based on current page
  let main;
  switch (currentPage) {
    case 'documents':
      main = <DocumentsPage />;
      break;
    case 'jobs':
      main = <JobsPage />;
      break;
    case 'audit':
      main = <AuditPage />;
      break;
    case 'member-studio':
      main = <MemberStudioPage />;
      break;
    case 'settings':
      main = <SettingsPage />;
      break;
    case 'about':
      main = <AboutTab />;
      break;
    case 'members':
      main = (
        <div className="page-container">
          <div className="page-header">
            <h2>Members</h2>
            <p className="page-subtitle">Search and browse synthetic members</p>
          </div>
          <MemberSearch onSelect={handleSelectMember} />
          {topRisk.length > 0 && (
            <>
              <h3 style={{ margin: '24px 0 12px', fontSize: '1rem' }}>All Members</h3>
              <div className="risk-worklist">
                {topRisk.map((m) => (
                  <button key={m.member_id} className="risk-worklist-item" onClick={() => handleSelectMember(m)}>
                    <Avatar firstName={m.first_name} lastName={m.last_name} memberId={m.member_id} size={36} />
                    <div className="worklist-member-info">
                      <span className="worklist-name">{m.first_name} {m.last_name}</span>
                      <span className="worklist-meta">{m.age}y · {m.gender} · {m.plan_type}</span>
                    </div>
                    <div className="worklist-flags">
                      {m.risk_flags.slice(0, 3).map((flag) => <span key={flag} className="condition-tag">{flag}</span>)}
                    </div>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      );
      break;
    case 'member-detail':
      if (!selectedMember) {
        main = <div className="page-empty"><p>Select a member to view their profile.</p></div>;
      } else {
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
                {activeTab === 'overview' && detail && <MemberOverview detail={detail} />}
                {activeTab === 'overview' && !detail && detailLoading && <div className="page-loading">Loading clinical data...</div>}
                {activeTab === 'chat' && (
                  <ChatPanel messages={messages} onSend={handleSend} loading={loading} disabled={false} member={selectedMember} error={error} onClearError={clearError} onRetry={handleRetry} />
                )}
                {activeTab !== 'chat' && activeTab !== 'overview' && detail && (
                  <MemberDetailPanel detail={detail} activeTab={activeTab} />
                )}
                {activeTab !== 'chat' && activeTab !== 'overview' && !detail && detailLoading && (
                  <div className="page-loading">Loading clinical data...</div>
                )}
              </ErrorBoundary>
            </div>
          </div>
        );
      }
      break;
    default: // worklist
      main = (
        <div className="page-container">
          <div className="page-header">
            <h2>Care Intelligence</h2>
            <p className="page-subtitle">Synthetic Data Environment</p>
          </div>

          <div className="worklist-summary-cards">
            <div className="summary-stat-card summary-red">
              <div className="stat-value">{topRisk.filter((m) => m.risk_flags.length >= 3).length}</div>
              <div className="stat-label">High Risk Members</div>
            </div>
            <div className="summary-stat-card summary-amber">
              <div className="stat-value">—</div>
              <div className="stat-label">Risk Increased Today</div>
            </div>
            <div className="summary-stat-card summary-blue">
              <div className="stat-value">—</div>
              <div className="stat-label">Policy Gaps</div>
            </div>
            <div className="summary-stat-card summary-green">
              <div className="stat-value">{topRisk.length}</div>
              <div className="stat-label">Total Members</div>
            </div>
          </div>

          <div className="worklist-section-header">
            <h3>Needs Attention Today</h3>
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
                  {m.risk_flags.slice(0, 3).map((flag) => <span key={flag} className="condition-tag">{flag}</span>)}
                  {m.risk_flags.length > 3 && <span className="worklist-more">+{m.risk_flags.length - 3}</span>}
                </div>
              </button>
            ))}
            {sortedFiltered.length === 0 && <div className="page-empty"><p>No members match this filter</p></div>}
          </div>
        </div>
      );
  }

  return <Layout nav={nav} main={main} memberContext={currentPage === 'member-detail' ? null : memberContext} />;
}
