import { useState } from 'react';
import { Shield } from 'lucide-react';
import type { Claim } from '../types';

interface InsuranceTabProps {
  claims: Claim[];
}

export function InsuranceTab({ claims }: InsuranceTabProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  if (!claims || claims.length === 0) return <div className="detail-empty">No claims data available</div>;

  const filtered = statusFilter === 'all' ? claims : claims.filter((c) => c.status === statusFilter);
  const totalBilled = claims.reduce((s, c) => s + (c.amount_billed || 0), 0);
  const totalPaid = claims.reduce((s, c) => s + (c.amount_paid || 0), 0);
  const denied = claims.filter((c) => c.status === 'denied').length;
  const denialRate = claims.length > 0 ? ((denied / claims.length) * 100).toFixed(0) : '0';

  return (
    <div className="insurance-tab">
      <div className="insurance-summary">
        <div className="summary-card">
          <span className="summary-value">{claims.length}</span>
          <span className="summary-label">Total Claims</span>
        </div>
        <div className="summary-card">
          <span className="summary-value">${totalBilled.toLocaleString()}</span>
          <span className="summary-label">Billed</span>
        </div>
        <div className="summary-card">
          <span className="summary-value">${totalPaid.toLocaleString()}</span>
          <span className="summary-label">Paid</span>
        </div>
        <div className="summary-card summary-card-alert">
          <span className="summary-value">{denialRate}%</span>
          <span className="summary-label">Denial Rate</span>
        </div>
      </div>
      <div className="insurance-filter">
        {['all', 'approved', 'denied', 'pending'].map((s) => (
          <button key={s} className={`filter-chip ${statusFilter === s ? 'filter-chip-active' : ''}`} onClick={() => setStatusFilter(s)}>
            {s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>
      <div className="claims-list">
        {filtered.map((c) => (
          <div key={c.claim_id} className={`claim-row claim-${c.status}`}>
            <div className="claim-header" onClick={() => c.status === 'denied' ? setExpandedId(expandedId === c.claim_id ? null : c.claim_id) : null}>
              <Shield size={14} className={`claim-icon claim-icon-${c.status}`} />
              <span className="claim-date">{c.date_of_service}</span>
              <span className="claim-proc">{c.procedure_code}</span>
              <span className="claim-provider">{c.provider}</span>
              <span className="claim-amount">${c.amount_billed.toLocaleString()}</span>
              <span className={`claim-status-badge claim-status-${c.status}`}>{c.status}</span>
              {c.status === 'denied' && <span className="evidence-chevron">{expandedId === c.claim_id ? '\u25BC' : '\u25B6'}</span>}
            </div>
            {expandedId === c.claim_id && c.denial_reason && (
              <div className="claim-denial">
                <strong>Denial Reason:</strong> {c.denial_reason}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
