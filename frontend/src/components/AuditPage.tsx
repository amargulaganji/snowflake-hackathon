import { useState, useEffect } from 'react';
import { ClipboardCheck, Search } from 'lucide-react';
import axios from 'axios';

interface AuditEntry {
  audit_id: string;
  timestamp: string;
  user_id: string | null;
  user_role: string | null;
  member_id: string | null;
  action: string;
  question: string | null;
  tools_invoked: string[] | null;
  risk_level: string | null;
  contradiction_detected: boolean;
  insufficient_evidence: boolean;
  response_preview: string | null;
  latency_ms: number | null;
}

export function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    axios.get('/admin/audit', { params: { limit: 100 } })
      .then(({ data }) => setEntries(data))
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = entries.filter((e) =>
    !search || e.question?.toLowerCase().includes(search.toLowerCase()) || e.member_id?.includes(search)
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <h2><ClipboardCheck size={20} /> Audit Trail</h2>
        <p className="page-subtitle">Review AI questions, evidence sources, tools used, guardrail outcomes, and response provenance</p>
      </div>

      <div className="page-toolbar">
        <div className="search-box">
          <Search size={14} />
          <input type="text" placeholder="Search by question or member ID..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
      </div>

      {loading ? (
        <div className="page-loading">Loading audit trail...</div>
      ) : filtered.length === 0 ? (
        <div className="page-empty"><p>No audit entries found.</p></div>
      ) : (
        <div className="table-wrap">
          <table className="detail-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>User</th>
                <th>Role</th>
                <th>Member</th>
                <th>Question</th>
                <th>Tools</th>
                <th>Risk</th>
                <th>Flags</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => (
                <tr key={e.audit_id}>
                  <td style={{ whiteSpace: 'nowrap', fontSize: '0.8rem' }}>{e.timestamp?.replace('T', ' ').slice(0, 19)}</td>
                  <td>{e.user_id || '—'}</td>
                  <td><span className="doc-type-badge">{e.user_role || '—'}</span></td>
                  <td>{e.member_id || '—'}</td>
                  <td className="td-primary" style={{ maxWidth: 240, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {e.question || '—'}
                  </td>
                  <td style={{ fontSize: '0.8rem' }}>{e.tools_invoked?.join(', ') || '—'}</td>
                  <td>{e.risk_level ? <span className={`risk-level-badge risk-${e.risk_level.toLowerCase()}`}>{e.risk_level}</span> : '—'}</td>
                  <td>
                    {e.contradiction_detected && <span className="flag-abnormal" style={{ fontSize: '0.7rem' }}>CONTRADICTION</span>}
                    {e.insufficient_evidence && <span className="flag-abnormal" style={{ fontSize: '0.7rem', background: '#1565C0' }}>INSUFFICIENT</span>}
                    {!e.contradiction_detected && !e.insufficient_evidence && '—'}
                  </td>
                  <td>{e.latency_ms ? `${(e.latency_ms / 1000).toFixed(1)}s` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
